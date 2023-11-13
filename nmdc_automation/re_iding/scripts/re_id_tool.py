#!/usr/bin/env python3
# nmdc_automation/nmdc_automation/re_iding/scripts/re_id_tool.py
"""
re_id_tool.py: Provides command-line tools to extract and re-ID NMDC metagenome
workflow records.
"""
import logging
import time
from pathlib import Path
import json
import click

from nmdc_automation.api import NmdcRuntimeApi, NmdcRuntimeUserApi
from nmdc_automation.config import Config
import nmdc_schema.nmdc as nmdc
from nmdc_automation.re_iding.base import ReIdTool
from nmdc_automation.re_iding.db_utils import get_omics_processing_id

# Defaults
GOLD_STUDY_ID = "gold:Gs0114663"
STUDY_ID = "nmdc:sty-11-aygzgv51"
NAPA_CONFIG = Path("../../../configs/napa_config.toml")


BASE_DATAFILE_DIR = "/global/cfs/cdirs/m3408/results"
DRYRUN_DATAFILE_DIR = "./data/dryrun_data/results"

DATA_DIR = Path(__file__).parent.absolute().joinpath("data")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)



@click.group()
@click.option("--site-config", type=click.Path(exists=True),
              default=NAPA_CONFIG,)
@click.pass_context
def cli(ctx, site_config):
    """
    NMDC re-ID tool
    """
    ctx.ensure_object(dict)
    ctx.obj['site_config'] = site_config


@cli.command()
@click.option('--study_id', default=STUDY_ID,
              help=f'Optional updated study ID. Default: {STUDY_ID}')
@click.pass_context
def extract_records(ctx, study_id):
    """
    Extract metagenome workflow activities and their data object records
    that are informed_by the legacy ID (GOLD Study ID) for a re-ID-ed Study/
    Biosample/OmicsProcessing.

    Write the results, as a list of nmdc-schema Database instances to a JSON file.
    """
    start_time = time.time()
    logging.info(f"Extracting workflow records for study_id: {study_id}")
    logging.info(f"study_id: {study_id}")

    config = Config(ctx.obj['site_config'])
    api_client = NmdcRuntimeUserApi(username=config.napa_username, password=config.napa_password,
        base_url=config.napa_base_url)

    # 1. Retrieve all OmicsProcessing records for the updated NMDC study ID
    omics_processing_records = api_client.get_omics_processing_records_for_nmdc_study(
        study_id
    )
    logging.info(
        f"Retrieved {len(omics_processing_records)} OmicsProcessing records for study {study_id}"
    )

    retrieved_databases = []
    # 2. For each OmicsProcessing record, find the legacy identifier:
    for omics_processing_record in omics_processing_records:
        db = nmdc.Database()
        logging.info(
            f"omics_processing_record: "
            f"{omics_processing_record['id']}"
            )
        legacy_id = _get_legacy_id(omics_processing_record)
        logging.info(f"legacy_id: {legacy_id}")

        if (omics_processing_record["omics_type"]["has_raw_value"] !=
                "Metagenome"):
            logging.info(
                f"omics_processing_record {omics_processing_record['id']} "
                f"is not a Metagenome"
                )
            continue
        db.omics_processing_set.append(omics_processing_record)
        for data_object_id in omics_processing_record["has_output"]:
            data_object_record = api_client.get_data_object_by_id(
                data_object_id
            )
            db.data_object_set.append(data_object_record)

        # downstream workflow activity sets
        (read_qc_records, readbased_records, metagenome_assembly_records,
         metagenome_annotation_records, mags_records) = [], [], [], [], []

        downstream_workflow_activity_sets = {
            "read_qc_analysis_activity_set": read_qc_records,
            "read_based_taxonomy_analysis_activity_set": readbased_records,
            "metagenome_assembly_set": metagenome_assembly_records,
            "metagenome_annotation_activity_set": metagenome_annotation_records,
            "mags_activity_set": mags_records,
        }
        for set_name, records in downstream_workflow_activity_sets.items():
            records = api_client.get_workflow_activity_informed_by(
                set_name, legacy_id
            )
            db.__setattr__(set_name, records)
            # Add the data objects referenced by the `has_output` property
            for record in records:
                logging.info(f"record: {record['id']}, {record['name']}")
                for data_object_id in record["has_output"]:
                    data_object_record = api_client.get_data_object_by_id(
                        data_object_id
                    )
                    logging.info(
                        f"data_object_record: "
                        f"{data_object_record['id']}, {data_object_record['description']}"
                        )
                    db.data_object_set.append(data_object_record)

        # Search for orphaned data objects with the legacy ID in the description
        orphaned_data_objects = api_client.get_data_objects_by_description(
            legacy_id
        )
        # check that we don't already have the data object in the set
        for data_object in orphaned_data_objects:
            if data_object["id"] not in [d["id"] for d in db.data_object_set]:
                db.data_object_set.append(data_object)
                logging.info(
                    f"Added orphaned data object: "
                    f"{data_object['id']}, {data_object['description']}"
                    )

        retrieved_databases.append(db)

    with open(f"{study_id}_assocated_record_dump.json", 'w') as json_file:
        json.dump(
            [o.__dict__ for o in retrieved_databases], json_file, indent=4
            )


@cli.command()
@click.option('--dryrun / --no-dryrun', is_flag=True, default=True,
              help='Dryrun mode: use local data dir and do not save results')
@click.option('--study_id', default=STUDY_ID,
              help=f'Optional updated study ID. Default: {STUDY_ID}')
@click.option('--data_dir', default=BASE_DATAFILE_DIR,
              help=f'Optional base datafile directory. Default: {BASE_DATAFILE_DIR}')
@click.pass_context
def process_records(ctx, dryrun, study_id, data_dir):
    """
    Read the JSON file of extracted workflow records and their data objects and
    re-ID the records with newly-minted NMDC IDs, update data file headers.

    Write the results to a new JSON file of nmdc Database instances.
    """
    start_time = time.time()
    logging.info(f"Processing workflow records for study_id: {study_id}")

    # Get API client
    config = ctx.obj['site_config']
    api_client = NmdcRuntimeApi(config)


    # Get Database dump file paths and the data directory
    db_infile, db_outfile = _get_database_paths(study_id, dryrun)
    data_dir = _get_data_dir(data_dir, dryrun)

    # Initialize re-ID tool
    reid_tool = ReIdTool(api_client, data_dir)


    # Read extracted DB records
    logging.info(f"Using db_infile: {db_infile}")
    with open(db_infile, "r") as f:
        db_records = json.load(f)
    logging.info(f"Read {len(db_records)} records from db_infile")

    re_ided_db_records = []
    for db_record in db_records:
        omics_processing_id = get_omics_processing_id(db_record)
        logging.info(f"omics_processing_id: {omics_processing_id}")

        new_db = nmdc.Database()
        # update OmicsProcessing has_output and related DataObject records
        new_db = reid_tool.update_omics_processing_has_output(db_record, new_db)
        # update ReadsQC
        new_db = reid_tool.update_reads_qc_analysis_activity_set(db_record, new_db)
        # update Metagenome Assembly
        new_db = reid_tool.update_metagenome_assembly_set(db_record, new_db)
        # update Read Based Taxonomy Analysis
        new_db = reid_tool.update_read_based_taxonomy_analysis_activity_set(db_record, new_db)

        re_ided_db_records.append(new_db)


    json_data = json.dumps(re_ided_db_records, default=lambda o: o.__dict__, indent=4)
    logging.info(f"Writing re_ided_db_records to {db_outfile}")
    with open(db_outfile, "w") as f:
        f.write(json_data)


def _get_data_dir(data_dir, dryrun):
    """
    Return the path to the data object files
    """
    if dryrun:
        logging.info("Running in dryrun mode")
        return DRYRUN_DATAFILE_DIR
    elif not data_dir:
        data_dir = BASE_DATAFILE_DIR
    logging.info(f"Using datafile_dir: {data_dir}")
    return data_dir

def _get_database_paths(study_id, dryrun):
    """
    Return the paths to the input and output data files
    """
    db_infile_suffix = "_associated_record_dump.json"
    db_outfile_suffix = "_re_ided_record_dump.json"
    if dryrun:
        db_infile = DATA_DIR.joinpath(f"dryrun{db_infile_suffix}")
        db_outfile = DATA_DIR.joinpath(f"dryrun{db_outfile_suffix}")
    else:
        db_infile = DATA_DIR.joinpath(f"{study_id}{db_infile_suffix}")
        db_outfile = DATA_DIR.joinpath(f"{study_id}{db_outfile_suffix}")
    return db_infile, db_outfile

def _get_legacy_id(omics_processing_record: dict) -> str:
    """
    Get the legacy ID for the given OmicsProcessing record.
    """
    legacy_id = None
    legacy_ids = []
    gold_ids = omics_processing_record.get("gold_sequencing_project_identifiers", [])
    legacy_ids.extend(gold_ids)
    alternative_ids = omics_processing_record.get("alternative_identifiers", [])
    legacy_ids.extend(alternative_ids)
    if len(legacy_ids) == 0:
        logging.warning(
            f"No legacy IDs found for omics_processing_record: {omics_processing_record['id']}"
        )
        return None
    elif len(legacy_ids) > 1:
        logging.warning(
            f"Multiple legacy IDs found for omics_processing_record: {omics_processing_record['id']}"
        )
        return None
    else:
        legacy_id = legacy_ids[0]
    return legacy_id

if __name__ == '__main__':
    cli(obj={})
