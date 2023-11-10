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

from nmdc_automation.api import NmdcRuntimeApi
from nmdc_automation.config import Config
import nmdc_schema.nmdc as nmdc
from nmdc_automation.re_iding.base import update_omics_processing_has_output
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
        new_db = update_omics_processing_has_output(db_record, new_db, api_client)



        # Re-ID db_record
        # Update data file headers
        # Write re-IDed db_record to db_outfile
        # Write updated data file to datafile_dir
        # Log results


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


if __name__ == '__main__':
    cli(obj={})
