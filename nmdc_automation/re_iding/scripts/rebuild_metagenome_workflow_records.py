#!/usr/bin/env python3
# coding: utf-8
# nmdc_schema/napa_compliance/scripts/rebuild_metagenome_workflow_records.py
"""
rebuild_metagenome_workflow_records.py: Rebuild metagenome workflow records
after re-ID-ing of OmicsProcessing records.
"""
import logging
import os
from pathlib import Path
# import requests
import time

import click

from nmdc_automation.config import Config
from nmdc_automation.api import NmdcRuntimeApi

GOLD_STUDY_ID = "gold:Gs0114663"
STUDY_ID = "nmdc:sty-11-aygzgv51"
NAPA_CONFIG = Path("../../../configs/napa_config.toml")

@click.command()
@click.option("--study_id", default=STUDY_ID, help="Updated study ID")
@click.option("--site_config", type=click.Path(exists=True),
              default=NAPA_CONFIG, help="Site configuration file")
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

    runtime_api_client = NmdcRuntimeApi(site_config)



    # 1. Retrieve all OmicsProcessing records for the given GOLD study ID
    # https://api-napa.microbiomedata.org/omics_processing_sets?find=omics_processing_set&filter=part_of%3Agold:Gs0114663&per_page=99&page=1

    params = {
        "find": "omics_processing_set",
        "filter": {
            "part_of": {
                "$elemMatch": {"$eq": study_id}
            }
        }
    }
    response = runtime_api_client.run_query(params)
    print(response)

    # 2. For each OmicsProcessing record, retrieve the corresponding


if __name__ == "__main__":
    rebuild_workflow_records()