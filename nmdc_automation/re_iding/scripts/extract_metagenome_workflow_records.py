#!/usr/bin/env python3
# coding: utf-8
# nmdc_schema/napa_compliance/scripts/extract_metagenome_workflow_records.py
"""
extract_metagenome_workflow_records.py: Extract metagenome workflow records
for re-ID-ing of OmicsProcessing records.
"""
import logging
import time
from pathlib import Path
import json
import click

from nmdc_automation.api import NmdcRuntimeUserApi
from nmdc_automation.config import Config
import nmdc_schema.nmdc as nmdc

GOLD_STUDY_ID = "gold:Gs0114663"
STUDY_ID = "nmdc:sty-11-aygzgv51"
NAPA_CONFIG = Path("../../../configs/napa_config.toml")


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

@click.command()
@click.option("--study_id", default=STUDY_ID, help="Updated study ID")
@click.option(
    "--site_config", type=click.Path(exists=True), default=NAPA_CONFIG,
    help="Site configuration file"
)
def extract_workflow_records(study_id: str, site_config: bool):
    """
    Extract metagenome workflow records for re-ID-ing of Study, Biosample, and
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
       a. Retrieve the corresponding DataObject records
    4. Create a database object for each OmicsProcessing record and its
    associated WorkflowExecutionActivity and DataObject records
    5. Write the database object to a JSON file
    """
    start_time = time.time()
    logging.info("starting missing_neon_soils_ecosystem_data.py...")
    logging.info(f"study_id: {study_id}")

    config = Config(site_config)
    query_api_client = NmdcRuntimeUserApi(
        username=config.napa_username, password=config.napa_password,
        base_url=config.napa_base_url, )
    
    # 1. Retrieve all OmicsProcessing records for the updated NMDC study ID
    omics_processing_records = query_api_client.get_omics_processing_records_for_nmdc_study(
        study_id
        )
    logging.info(
        f"Retrieved {len(omics_processing_records)} OmicsProcessing records for study {study_id}"
    )
    
    retrieved_databases = []
    # 2. For each OmicsProcessing record, find the legacy identifier:
    for omics_processing_record in omics_processing_records:
        db = nmdc.Database()
        logging.info(f"omics_processing_record: "
                     f"{omics_processing_record['id']}")
        legacy_id = _get_legacy_id(omics_processing_record)
        logging.info(f"legacy_id: {legacy_id}")

        if (omics_processing_record["omics_type"]["has_raw_value"] !=
                "Metagenome"):
            logging.info(f"omics_processing_record {omics_processing_record['id']} "
                         f"is not a Metagenome")
            continue
        db.omics_processing_set.append(omics_processing_record)
        for data_object_id in omics_processing_record["has_output"]:
            data_object_record = query_api_client.get_data_object_by_id(
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
            records = query_api_client.get_workflow_activity_informed_by(
                set_name, legacy_id
            )
            db.__setattr__(set_name, records)
            # Add the data objects referenced by the `has_output` property
            for record in records:
                logging.info(f"record: {record['id']}, {record['name']}")
                for data_object_id in record["has_output"]:
                    data_object_record = query_api_client.get_data_object_by_id(
                        data_object_id
                    )
                    logging.info(f"data_object_record: "
                                 f"{data_object_record['id']}, {data_object_record['description']}")
                    db.data_object_set.append(data_object_record)

        # Search for orphaned data objects with the legacy ID in the description
        orphaned_data_objects = query_api_client.get_data_objects_by_description(
                legacy_id
        )
        # check that we don't already have the data object in the set
        for data_object in orphaned_data_objects:
            if data_object["id"] not in [d["id"] for d in db.data_object_set]:
                db.data_object_set.append(data_object)
                logging.info(f"Added orphaned data object: "
                             f"{data_object['id']}, {data_object['description']}")

        retrieved_databases.append(db)
        
    with open(f"{study_id}_assocated_record_dump.json", 'w') as json_file:
        json.dump([o.__dict__ for o in retrieved_databases], json_file, indent=4)


if __name__ == "__main__":
    extract_workflow_records()
