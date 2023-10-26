#!/usr/bin/env python3
# coding: utf-8
# nmdc_schema/napa_compliance/scripts/rebuild_metagenome_workflow_records.py
"""
rebuild_metagenome_workflow_records.py: Rebuild metagenome workflow records
after re-ID-ing of OmicsProcessing records.
"""
import logging
import time
from pathlib import Path

import click

from nmdc_automation.api import NmdcRuntimeUserApi
from nmdc_automation.config import Config

GOLD_STUDY_ID = "gold:Gs0114663"
STUDY_ID = "nmdc:sty-11-aygzgv51"
NAPA_CONFIG = Path("../../../configs/napa_config.toml")


@click.command()
@click.option("--study_id", default=STUDY_ID, help="Updated study ID")
@click.option(
    "--site_config", type=click.Path(exists=True), default=NAPA_CONFIG,
    help="Site configuration file"
)
def rebuild_workflow_records(study_id: str, site_config: bool):
    """
    Rebuild metagenome workflow records after re-ID-ing of Study, Biosample, and
    OmicsProcessing records by:
    1. Retrieving all OmicsProcessing records for updated study ID
    2. For each OmicsProcessing record, retrieve the corresponding
    WorkflowExecutionActivity records:
        a. ReadQcAnalysisActivity
        b. ReadBasedTaxonomyAnalysisActivity
        c. MetagenomeAssembly
        d. MetagenomeAnnotationActivity
        e. MagsAnalysisActivity
    3. For each WorkflowExecutionActivity record:
    TODO - summarize Michal's flowchart here

    """
    start_time = time.time()
    logging.info("starting missing_neon_soils_ecosystem_data.py...")
    logging.info(f"study_id: {study_id}")

    config = Config(site_config)
    query_api_client = NmdcRuntimeUserApi(
        username=config.napa_username, password=config.napa_password,
        base_url=config.napa_base_url, )

    # 1. Retrieve all OmicsProcessing records for the given GOLD study ID
    url = "queries:run"
    params = {"find": "omics_processing_set",
              "filter": {"part_of": {"$elemMatch": {"$eq": study_id}}}}
    response = query_api_client.request("POST", url, params_or_json_data=params)
    if response.status_code != 200:
        raise Exception(
            f"Error retrieving OmicsProcessing records for study {study_id}"
            )
    omics_processing_records = response.json()["cursor"]["firstBatch"]
    logging.info(
        f"Retrieved {len(omics_processing_records)} OmicsProcessing records for study {study_id}"
        )

    # 2. For each OmicsProcessing record, retrieve the corresponding


if __name__ == "__main__":
    rebuild_workflow_records()
