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
import requests
from linkml_runtime.dumpers import json_dumper

from nmdc_automation.api import NmdcRuntimeApi, NmdcRuntimeUserApi
from nmdc_automation.nmdc_common.client import NmdcApi
import nmdc_schema.nmdc as nmdc
from nmdc_automation.re_iding.base import ReIdTool
from nmdc_automation.re_iding.changesheets import Changesheet, ChangesheetLineItem
from nmdc_automation.re_iding.db_utils import get_omics_processing_id

# Defaults
GOLD_STUDY_ID = "gold:Gs0114663"
STUDY_ID = "nmdc:sty-11-aygzgv51"
NAPA_CONFIG = Path("../../../configs/napa_config.toml")
NAPA_BASE_URL = "https://api-napa.microbiomedata.org/"


BASE_DATAFILE_DIR = "/global/cfs/cdirs/m3408/results"
DRYRUN_DATAFILE_DIR = "/global/cfs/cdirs/m3408/results"

DATA_DIR = Path(__file__).parent.absolute().joinpath("data")
LOG_PATH = DATA_DIR.joinpath("re_id_tool.log")

logging.basicConfig(
    filename="re_id.log",
    filemode="w",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())


@click.group()
@click.option(
    "--site-config",
    type=click.Path(exists=True),
    default=NAPA_CONFIG,
)
@click.pass_context
def cli(ctx, site_config):
    """
    NMDC re-ID tool
    """
    ctx.ensure_object(dict)
    ctx.obj["site_config"] = site_config


@cli.command()
@click.option(
    "--study-id",
    default=STUDY_ID,
    help=f"Optional updated study ID. Default: {STUDY_ID}",
)
@click.option("--api-base-url", default=NAPA_BASE_URL,
              help=f"Optional base URL for the NMDC API. Default: {NAPA_BASE_URL}")
@click.pass_context
def extract_records(ctx, study_id, api_base_url):
    """
    Extract metagenome workflow activities and their data object records
    that are informed_by the legacy ID (GOLD Study ID) for a re-ID-ed Study/
    Biosample/OmicsProcessing.

    Write the results, as a list of nmdc-schema Database instances to a JSON file.
    """
    start_time = time.time()
    logger.info(f"Extracting workflow records for study_id: {study_id}")
    logger.info(f"study_id: {study_id}")

    config = ctx.obj["site_config"]
    # api_client = NmdcRuntimeUserApi(config)
    api_client = NmdcApi(api_base_url)

    # 1. Retrieve all OmicsProcessing records for the updated NMDC study ID
    omics_processing_records = (
        api_client.get_omics_processing_records_part_of_study(
        study_id
    ))
    logger.info(
        f"Retrieved {len(omics_processing_records)} OmicsProcessing records for study {study_id}"
    )

    retrieved_databases = []
    # 2. For each OmicsProcessing record, find the legacy identifier:
    for omics_processing_record in omics_processing_records:
        db = nmdc.Database()
        logger.info(f"omics_processing_record: " f"{omics_processing_record['id']}")
        legacy_id = _get_legacy_id(omics_processing_record)
        logger.info(f"legacy_id: {legacy_id}")

        # if omics_processing_record["omics_type"]["has_raw_value"] != "Metagenome":
        #     logger.info(
        #         f"omics_processing_record {omics_processing_record['id']} "
        #         f"is not a Metagenome"
        #     )
        #     continue
        db.omics_processing_set.append(omics_processing_record)
        for data_object_id in omics_processing_record["has_output"]:
            data_object_record = api_client.get_data_object(data_object_id)
            db.data_object_set.append(data_object_record)

        # downstream workflow activity sets
        (
            read_qc_records,
            readbased_records,
            metagenome_assembly_records,
            metagenome_annotation_records,
            mags_records,
            metatranscriptome_activity_records,
        ) = ([], [], [], [], [], [])

        downstream_workflow_activity_sets = {
            "read_qc_analysis_activity_set": read_qc_records,
            "read_based_taxonomy_analysis_activity_set": readbased_records,
            "metagenome_assembly_set": metagenome_assembly_records,
            "metagenome_annotation_activity_set": metagenome_annotation_records,
            "mags_activity_set": mags_records,
            "metatranscriptome_activity_set": metatranscriptome_activity_records,
        }
        for set_name, records in downstream_workflow_activity_sets.items():
            logger.info(f"set_name: {set_name} for {legacy_id}")
            records = api_client.get_workflow_activities_informed_by(set_name,
                                                                   legacy_id)
            logger.info(f"found {len(records)} records")
            db.__setattr__(set_name, records)
            # Add the data objects referenced by the `has_output` property
            for record in records:
                logger.info(f"record: {record['id']}, {record['name']}")
                for data_object_id in record["has_output"]:
                    data_object_record = api_client.get_data_object(
                        data_object_id
                    )
                    if not data_object_record:
                        logger.warning(f"no data object found for {data_object_id}")
                        continue
                    logger.info(
                        f"has_output: "
                        f"{data_object_record['id']}, {data_object_record['description']}"
                    )
                    db.data_object_set.append(data_object_record)

        # Search for orphaned data objects with the legacy ID in the description
        orphaned_data_objects = api_client.get_data_objects_by_description(legacy_id)
        # check that we don't already have the data object in the set
        for data_object in orphaned_data_objects:
            if data_object["id"] not in [d["id"] for d in db.data_object_set]:
                db.data_object_set.append(data_object)
                logger.info(
                    f"Added orphaned data object: "
                    f"{data_object['id']}, {data_object['description']}"
                )

        retrieved_databases.append(db)

    json_data = json.loads(json_dumper.dumps(retrieved_databases, inject_type=False))
    db_outfile = DATA_DIR.joinpath(f"{study_id}_associated_record_dump.json")
    with open(db_outfile, "w") as f:
        f.write(json.dumps(json_data, indent=4))


@cli.command()
@click.option(
    "--dryrun / --no-dryrun",
    is_flag=True,
    default=True,
    help="Dryrun mode: use local data dir and do not save results",
)
@click.option(
    "--study_id",
    default=STUDY_ID,
    help=f"Optional updated study ID. Default: {STUDY_ID}",
)
@click.option(
    "--data_dir",
    default=BASE_DATAFILE_DIR,
    help=f"Optional base datafile directory. Default: {BASE_DATAFILE_DIR}",
)
@click.pass_context
def process_records(ctx, dryrun, study_id, data_dir):
    """
    Read the JSON file of extracted workflow records and their data objects and
    re-ID the records with newly-minted NMDC IDs, update data file headers.

    Write the results to a new JSON file of nmdc Database instances.
    """
    start_time = time.time()
    logging.info(f"Processing workflow records for study_id: {study_id}")
    if dryrun:
        logging.info("Running in dryrun mode")

    # Get API client
    config = ctx.obj["site_config"]
    api_client = NmdcRuntimeApi(config)

    # Get Database dump file paths and the data directory
    db_infile, db_outfile = _get_database_paths(study_id, dryrun)
    data_dir = _get_data_dir(data_dir, dryrun)
    logging.info(f"Using data_dir: {data_dir}")

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
        # update ReadsQC:
        # db records
        new_db = reid_tool.update_reads_qc_analysis_activity_set(db_record, new_db)
        # files
        # TODO - update reads qc files
        # update Metagenome Assembly
        new_db = reid_tool.update_metagenome_assembly_set(db_record, new_db)
        # update Read Based Taxonomy Analysis
        new_db = reid_tool.update_read_based_taxonomy_analysis_activity_set(
            db_record, new_db
        )

        re_ided_db_records.append(new_db)

    json_data = json.loads(json_dumper.dumps(re_ided_db_records, inject_type=False))
    with open(db_outfile, "w") as f:
        f.write(json.dumps(json_data, indent=4))


@cli.command()
@click.argument("reid_records_file", type=click.Path(exists=True))
@click.option(
    "--changesheet_only",
    is_flag=True,
    default=False,
)
@click.pass_context
def ingest_records(ctx, reid_records_file, changesheet_only):
    """
    Read in json dump of re_id'd records and:
    submit them to the
    /v1/workflows/activities endpoint
    """
    start_time = time.time()
    logging.info(f"Submitting re id'd records from : {reid_records_file}")
    reid_records_filename = Path(reid_records_file).name
    reid_base_name = reid_records_filename.split("_")[0]

    # Get API client(s)
    config = ctx.obj["site_config"]
    api_client = NmdcRuntimeApi(config)
    api_user_client = NmdcRuntimeUserApi(config)

    with open(reid_records_file, "r") as f:
        db_records = json.load(f)

    changesheet = Changesheet(name=f"{reid_base_name}_changesheet")
    for record in db_records:
        time.sleep(3)
        # remove the omics_processing_set and use it to generate
        # changes to omics_processing has_output
        omics_processing_set = record.pop("omics_processing_set")
        for omics_processing_record in omics_processing_set:
            omics_processing_id = omics_processing_record["id"]
            logging.info(f"omics_processing_id: {omics_processing_id}")
            # find legacy has_output and create change to remove it
            # need to strip the nmdc: prefix for the objects endpoint
            trimmed_omics_processing_id = omics_processing_id.split(":")[1]
            resp = api_user_client.request(
                "GET", f"objects/{trimmed_omics_processing_id}"
            )
            legacy_omics_processing_record = resp.json()
            # delete legacy has_output
            change = ChangesheetLineItem(
                id=omics_processing_id,
                action="remove item",
                attribute="has_output",
                value="|".join(legacy_omics_processing_record["has_output"]) + "|",
            )
            changesheet.line_items.append(change)
            logging.info(f"changes: {change}")

            # insert new has_output
            change = ChangesheetLineItem(
                id=omics_processing_id,
                action="insert",
                attribute="has_output",
                value="|".join(omics_processing_record["has_output"]) + "|",
            )
            changesheet.line_items.append(change)
            logging.info(f"changes: {change}")

        # submit the record to the workflows endpoint
        if not changesheet_only:
            resp = api_client.post_objects(record)
            logger.info(f"{record} posted, got response: {resp}")
        else:
            logger.info(f"changesheet_only is True, skipping ingest")

    changesheet.write_changesheet()
    logging.info(f"changesheet written to {changesheet.output_filepath}")
    if changesheet.validate_changesheet(api_client.config.napa_base_url):
        logging.info(f"changesheet validated")
    else:
        logging.info(f"changesheet validation failed")


@cli.command()
@click.argument("old_records_file", type=click.Path(exists=True))
@click.pass_context
def delete_old_records(ctx, old_records_file):
    """
    Read in json dump of old records and:
    delete them using
    /queries/run endpoint
    """

    logging.info(f"Deleting old objects found in : {old_records_file}")
    old_records_filename = Path(old_records_file).name
    old_base_name = old_records_filename.split("_")[0]

    # Get API client(s)
    config = ctx.obj["site_config"]
    api_user_client = NmdcRuntimeUserApi(config)

    # get old db records
    with open(old_records_file, "r") as f:
        old_db_records = json.load(f)

    # set list to capture annotation genes for agg set
    gene_id_list = []
    for record in old_db_records:
        for set_name, object_record in record.items():
            if set_name == "omics_processing_set":
                continue
            if isinstance(object_record, list):
                for item in object_record:
                    if "id" in item:
                        if set_name == "metagenome_annotation_activity_set":
                            gene_id_list.append(item["id"])
                        delete_query = {
                            "delete": set_name,
                            "deletes": [{"q": {"id": item["id"]}, "limit": 1}],
                        }
                        try:
                            logging.info(
                                f"Running query: {delete_query}, deleting {set_name} with id: {item['id']}"
                            )

                            run_query_response = api_user_client.run_query(
                                delete_query
                            )

                            logging.info(
                                f"Deleting query posted with response: {run_query_response}"
                            )
                        except requests.exceptions.RequestException as e:
                            logging.info(
                                f"An error occured while running: {delete_query}, response retutrned: {e}"
                            )

    for annotation_id in gene_id_list:
        try:
            logging.info(
                f"Deleting functional aggregate record with id: {annotation_id}"
            )
            delete_query_agg = {
                "delete": "functional_annotation_agg",
                "deletes": [{"q": {"metagenome_annotation_id": annotation_id}, "limit": 1}],
            }

            run_query_agg_response = api_user_client.run_query(delete_query_agg)

            logging.info(
                f"Response for deleting functional annotation agg record returned: {run_query_agg_response}"
            )
        except requests.exceptions.RequestException as e:
            logging.error(
                f"An error occurred while deleting annotation id {annotation_id}: {e}"
            )


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
            f"No legacy IDs found for: {omics_processing_record['id']} using ID instead"
        )
        return omics_processing_record["id"]
    elif len(legacy_ids) > 1:
        logging.warning(
            f"Multiple legacy IDs found for omics_processing_record: {omics_processing_record['id']}"
        )
        return None
    else:
        legacy_id = legacy_ids[0]
    return legacy_id


if __name__ == "__main__":
    cli(obj={})
