#!/usr/bin/env python3
# nmdc_automation/nmdc_automation/re_iding/scripts/re_id_tool.py
"""
re_id_tool.py: Provides command-line tools to extract and re-ID NMDC metagenome
workflow records.
"""
from copy import deepcopy
import csv
import logging
import sys
import time
from pathlib import Path
import json
import re

import click
from linkml_runtime.dumpers import json_dumper
import pymongo

from nmdc_automation.api import NmdcRuntimeApi, NmdcRuntimeUserApi
from nmdc_automation.nmdc_common.client import NmdcApi
import nmdc_schema.nmdc as nmdc
from nmdc_automation.config import UserConfig
from nmdc_automation.re_iding.base import (
    ReIdTool,
    _get_biosample_legacy_id,
    write_updated_record_identifiers, compare_models,
    get_updates_for_metabolomics_or_nom, update_biosample,
    update_omics_processing
)
from nmdc_automation.re_iding.db_utils import (
    get_omics_processing_id, ANALYSIS_ACTIVITIES, get_collection_name_from_workflow_id, fix_malformed_workflow_id_version
)

# Defaults
NAPA_CONFIG = Path("../../../configs/.local_napa_user_config.toml")
PROD_CONFIG = Path("../../../configs/.local_prod_user_config.toml")
NAPA_BASE_URL = "https://api-napa.microbiomedata.org/"
RE_ID = {
    "Stegen": ("nmdc:sty-11-aygzgv51", "gold:Gs0114663"),
    "SPRUCE": ("nmdc:sty-11-33fbta56", "gold:Gs0110138"),
    "EMP": ("nmdc:sty-11-547rwq94", "gold:Gs0154244"),
    "Luquillo": ("nmdc:sty-11-076c9980", "gold:Gs0128850"),
    "CrestedButte": ("nmdc:sty-11-dcqce727", "gold:Gs0135149"),
    "Populus": ("nmdc:sty-11-1t150432", "gold:Gs0103573"),
    "Angelo": ("nmdc:sty-11-zs2syx06", "gold:Gs0110119"),
    "Shale": ("nmdc:sty-11-8fb6t785", "gold:Gs0114675"),
}
CONSORTIA = (
    "nmdc:sty-11-33fbta56",
    "nmdc:sty-11-547rwq94"
)
STUDIES = (
    "nmdc:sty-11-aygzgv51",
    "nmdc:sty-11-076c9980",
    "nmdc:sty-11-dcqce727",
    "nmdc:sty-11-1t150432",
    "nmdc:sty-11-zs2syx06",
    "nmdc:sty-11-8fb6t785",
)
DATA_DIR = Path(__file__).parent.absolute().joinpath("data")
PROD_DATAFILE_DIR = "/global/cfs/cdirs/m3408/results"
# assuming Mac: /Users/username/Documents/data/results
LOCAL_DATAFILE_DIR = Path.home().joinpath("Documents/data/results")
DRYRUN_DATAFILE_DIR = DATA_DIR.joinpath("dryrun_data/results")
LOG_PATH = DATA_DIR.joinpath("re_id_tool.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


@click.group()
@click.pass_context
def cli(ctx):
    """
    NMDC re-ID tool
    """
    ctx.ensure_object(dict)
    site_config = NAPA_CONFIG
    ctx.obj["site_config"] = site_config
    ctx.obj["database_name"] = "nmdc"
    ctx.obj["is_direct_connection"] = True


@cli.command()
@click.argument("legacy_study_id", type=str, required=True)
@click.argument("nmdc_study_id", type=str, required=True)
@click.option("--mongo-uri",required=False, default="mongodb://localhost:27017",)
@click.option("--identifiers-file", type=click.Path(exists=True), required=False)
@click.option("--no-update", is_flag=True, default=False, help="Do not update the database")
@click.pass_context
def update_study(ctx, legacy_study_id, nmdc_study_id,  mongo_uri, identifiers_file=None, no_update=False):
    """
    Update the NMDC study with the given legacy ID by re-IDing the study, biosample, and omics processing records
    and updating the MongoDB database with the new records.

    If an identifiers file is provided, the script will use the identifiers in the file rather than minting new IDs.

    If the --no-update flag is set, the script will not update the database, but will log the records that would be updated.
    """
    start_time = time.time()
    logging.info(f"Updating NMDC study with legacy ID: {legacy_study_id}")
    logging.info(f"Updating NMDC study with ID: {nmdc_study_id}")
    # Make sure we are using a valid nmdc_study_id
    valid_study_ids = CONSORTIA + STUDIES
    assert nmdc_study_id in valid_study_ids, f"Invalid nmdc_study_id: {nmdc_study_id}"

    # Read the identifiers file if provided as a .tsv file with columns: collection_name, legacy_id, new_id
    if identifiers_file:
        with open(identifiers_file, "r") as f:
            reader = csv.DictReader(f, delimiter="\t")
            identifiers = list(reader)
            logging.info(f"Using {len(identifiers)} identifiers from {identifiers_file}")
        # convert the identifiers to a mapping of (collection_name, legacy_id) -> new_id
        identifiers_map = {(record["collection_name"], record["legacy_id"]): record["new_id"] for record in identifiers}
    else:
        identifiers_map = None

    # Connect to the MongoDB server and check the database name
    is_direct_connection = ctx.obj["is_direct_connection"]
    database_name = ctx.obj["database_name"]
    client = pymongo.MongoClient(mongo_uri, directConnection=is_direct_connection)
    with pymongo.timeout(5):
        assert (database_name in client.list_database_names()), f"Database {database_name} not found"
    db_client = client[database_name]
    # start a session
    session = client.start_session()

    # API client for minting new IDs
    config = ctx.obj["site_config"]
    api_client = NmdcRuntimeApi(config)

    # Keep track of the updated record identifiers as (collection_name, legacy_id, new_id)
    updated_record_identifiers = set()

    #====== Study Update ======
    # Look up the study record, first by legacy ID then by NMDC ID
    study_record = db_client["study_set"].find_one({"id": legacy_study_id})
    if not study_record:
        study_record = db_client["study_set"].find_one({"id": nmdc_study_id})
    assert study_record, f"Study record not found for legacy ID: {legacy_study_id} or NMDC ID: {nmdc_study_id}"
    updated_record_identifiers.add(("study_set", legacy_study_id, nmdc_study_id))

    # Keep track of what updates we are going to make as a dict of {collection_name: {_id: update}}
    updates = {
        "study_set": {},
        "biosample_set": {},
        "omics_processing_set": {},
        "data_object_set": {},
        "metabolomics_analysis_activity_set": {},
        "nom_analysis_activity_set": {}
    }
    # Keep track of records that we will be deleting as a dict of {collection_name: [record]}
    deletions = {
        "omics_processing_set": [],
        "data_object_set": [],
    }

    study__id = study_record.pop("_id")
    # TODO work out why we have to strip off part_of, study_category, and associated_dois
    study_record.pop("part_of", None)
    study_record.pop("study_category", None)
    study_record.pop("associated_dois", None)
    study_record.pop("homepage_website", None)
    study = nmdc.Study(**study_record)
    updated_study = _update_study(study, legacy_study_id, nmdc_study_id)
    study_update = compare_models(study, updated_study)
    if study_update:
        updates["study_set"][study__id] = (study, study_update)

    #====== Biosample Update ======
    # Find all biosample records associated with the study by either study ID
    biosample_query = {
        "$or": [
            {"part_of": legacy_study_id},
            {"part_of": nmdc_study_id}
        ]
    }
    biosample_records = db_client["biosample_set"].find(biosample_query)
    # Iterate over the biosample records and update them and their related omics processing records
    for biosample_record in biosample_records:
        biosample__id = biosample_record.pop("_id")
        biosample = nmdc.Biosample(**biosample_record)
        legacy_biosample_id = _get_biosample_legacy_id(biosample)
        updated_biosample = update_biosample(biosample, nmdc_study_id, api_client, identifiers_map)
        if legacy_biosample_id != updated_biosample.id:
            updated_record_identifiers.add(("biosample_set", legacy_biosample_id, updated_biosample.id))
        biosample_update = compare_models(biosample, updated_biosample)
        if biosample_update:
            updates["biosample_set"][biosample__id] = (biosample, biosample_update)

        #====== OmicsProcessing Update ======
        # Find all OmicsProcessing records part_of either study and has_input either biosample
        study_ids = [legacy_study_id, nmdc_study_id]
        biosample_ids = [legacy_biosample_id, biosample.id]
        omics_processing_query = {
            "$and": [
                {"part_of": {"$in": study_ids}},
                {"has_input": {"$in": biosample_ids}}
            ]
        }
        omics_processing_records = db_client["omics_processing_set"].find(omics_processing_query)
        num_omics_processing_records = len(list(omics_processing_records.clone()))
        logging.info(f"Found {num_omics_processing_records} OmicsProcessing records for biosample {biosample.id}")

        # Iterate over the omics processing records and update them
        for omics_processing_record in omics_processing_records:

            # Special Case: Lipidomics OmicsProcessing and its has_output data object(s) get deleted
            if omics_processing_record["omics_type"]["has_raw_value"] == "Lipidomics":
                deletions["omics_processing_set"].append(omics_processing_record)
                omics_processing_output_ids = omics_processing_record.get("has_output", [])
                for omics_processing_output_id in omics_processing_output_ids:
                    data_object_record = db_client["data_object_set"].find_one({"id": omics_processing_output_id})
                    if data_object_record:
                        deletions["data_object_set"].append(data_object_record)
                logging.info(f"Adding Lipidomics record to Delete list: {omics_processing_record['id']}")
                continue

            # Update the OmicsProcessing record
            omics_processing_id = omics_processing_record.pop("_id")
            omics_processing = nmdc.OmicsProcessing(**omics_processing_record)
            updated_omics_processing = update_omics_processing(
                omics_processing, nmdc_study_id, updated_biosample.id, api_client, identifiers_map)

            # ===== Additional updates for Metabolomics and Organic Matter Characterization =====
            ANALYSIS_ACTIVITIES = ("Metabolomics", "Organic Matter Characterization")
            if updated_omics_processing.omics_type.has_raw_value in ANALYSIS_ACTIVITIES:
                updated_omics_processing, updated_record_identifiers, updates = get_updates_for_metabolomics_or_nom(
                    omics_processing, updated_omics_processing, api_client, db_client, identifiers_map,
                    updated_record_identifiers, updates
                )

            if omics_processing.id != updated_omics_processing.id:
                updated_record_identifiers.add(("omics_processing_set", omics_processing.id, updated_omics_processing.id))
            omics_processing_update = compare_models(omics_processing, updated_omics_processing)
            if omics_processing_update:
                updates["omics_processing_set"][omics_processing_id] = (omics_processing, omics_processing_update)

    if no_update:
        # Log the updates that would be made
        logging.info("No update flag set - Not updating the database")
    else:
        # Update the records in the database
        logging.info("Updating the database")
        with session.start_transaction():
            try:
                update_count_by_collection = {}
                for collection_name, record_updates in updates.items():
                    update_count_by_collection[collection_name] = 0
                    for _id, (model, update) in record_updates.items():
                        # update the record
                        filter_criteria = {"_id": _id}
                        update_criteria = {"$set": update}
                        result = db_client[collection_name].update_one(filter_criteria, update_criteria)
                        update_count_by_collection[collection_name] += result.modified_count
                session.commit_transaction()
                logging.info("Database update successful")
                for collection_name, count in update_count_by_collection.items():
                    logging.info(f"Updated {count} records in {collection_name}")

                # Delete the records that need to be deleted if any
                for collection_name, records in deletions.items():
                    delete_count = 0
                    for record in records:
                        result = db_client[collection_name].delete_one({"_id": record["_id"]})
                        delete_count += result.deleted_count
                    logging.info(f"Deleted {delete_count} records in {collection_name}")
                session.commit_transaction()

            except Exception as e:
                logging.error(f"An error occurred - aborting transaction")
                session.abort_transaction()
                logging.exception(f"An error occurred while updating records: {e}")
                sys.exit(1)

    logging.info("Writing updates and updated record identifiers to files")
    _write_updates(updates, nmdc_study_id)
    write_updated_record_identifiers(updated_record_identifiers, nmdc_study_id)
    if deletions:
        _write_deletions(deletions, nmdc_study_id)
    logging.info(f"Elapsed time: {time.time() - start_time}")
    sys.exit()


@cli.command()
@click.argument("study_id", type=str)
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

    config = UserConfig(ctx.obj["site_config"])
    api_client = NmdcApi(config.base_url)

    # 1. Retrieve all OmicsProcessing records for the updated NMDC study ID
    omics_processing_records = (
        api_client.get_omics_processing_records_part_of_study(
        study_id
    ))
    logging.info(
        f"Retrieved {len(omics_processing_records)} OmicsProcessing records for study {study_id}"
    )

    retrieved_databases = []
    retrieved_failed_databases = []
    omics_level_failure_count = 0
    read_qc_level_failure_count = 0
    # 2. For each OmicsProcessing record, find the legacy identifier:
    for omics_processing_record in omics_processing_records:
        db = nmdc.Database()
        db_failed = nmdc.Database()
        is_failed_data = False
        is_omics_missing_has_output = False

        logging.info(f"omics_processing_record: " f"{omics_processing_record['id']}")
        legacy_id = _get_legacy_id(omics_processing_record)
        logging.info(f"legacy_id: {legacy_id}")

        omics_type = omics_processing_record["omics_type"]["has_raw_value"]
        omics_id = omics_processing_record["id"]
        if omics_type not in ["Metagenome", "Metatranscriptome"]:
            continue


        omics_processing_has_outputs = omics_processing_record.get("has_output", [])
        # if no has_output, fail the record and its workflow activities and data objects
        if not omics_processing_has_outputs:
            logging.warning(f"No has_output for {omics_id} searching for has_input from ReadQC")
            # look for has_input from ReadQC
            has_input_data_objects = _get_has_input_from_read_qc(api_client, legacy_id)
            if has_input_data_objects:
                logging.info(f"has_input_data_objects: {len(has_input_data_objects)}")
                omics_processing_record["has_output"] = has_input_data_objects
                db.omics_processing_set.append(omics_processing_record)
                omics_processing_has_outputs = has_input_data_objects
            else:
                logging.error(f"OmicsMissingHasOutput: {omics_id} failing")
                is_failed_data = True
                is_omics_missing_has_output = True
                omics_level_failure_count += 1
                db_failed.omics_processing_set.append(omics_processing_record)
        else:
            logging.info(f"Adding OmicsProcessing: {omics_id}")
            db.omics_processing_set.append(omics_processing_record)

        for data_object_id in omics_processing_has_outputs:
            data_object_record = api_client.get_data_object(data_object_id)
            # If the data object is Missing, fail the omics processing record and its data objects
            if not data_object_record:
                logging.error(f"OmicsProcessingMissingDataObject: {data_object_id} for {omics_id}")
                is_failed_data = True
                is_omics_missing_has_output = True
                omics_level_failure_count += 1
                db_failed.data_object_set.append(data_object_record)
                db_failed.omics_processing_set.append(omics_processing_record)
                db.omics_processing_set.remove(omics_processing_record)
            else:
                logging.info(f"Adding OmicsProcessing {data_object_record.get('data_object_type')} has_output "
                             f"DataObject:{data_object_id}")
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

        downstream_workflow_activity_sets = (
            ("read_qc_analysis_activity_set", read_qc_records),
            ("read_based_taxonomy_analysis_activity_set", readbased_records),
            ("metagenome_assembly_set", metagenome_assembly_records),
            ("metagenome_annotation_activity_set", metagenome_annotation_records),
            ("mags_activity_set", mags_records),
            ("metatranscriptome_activity_set", metatranscriptome_activity_records),
        )
        is_reads_qc_missing_data_objects = False
        for set_name, workflow_records in downstream_workflow_activity_sets:
            logging.info(f"set_name: {set_name} for {legacy_id}")
            workflow_records = api_client.get_workflow_activities_informed_by(set_name,
                                                                   legacy_id)
            logging.info(f"found {len(workflow_records)} records")
            passing_records = []
            failing_records = []

            # Get workflow record(s) for each activity set - generally only one but could be more
            for workflow_record in workflow_records:

                logging.info(f"record: {workflow_record['id']}, {workflow_record['name']}")
                input_output_data_object_ids = set()
                # if "has_input" in workflow_record:
                #     input_output_data_object_ids.update(workflow_record["has_input"])
                if "has_output" in workflow_record:
                    input_output_data_object_ids.update(workflow_record["has_output"])

                if is_omics_missing_has_output:
                    logging.error(f"OmicsMissingHasOutput: {workflow_record['id']}, {workflow_record['name']} failing")
                    failing_records.append(workflow_record)


                is_workflow_missing_data_objects = False
                passing_data_objects = []
                failing_data_objects = []
                for data_object_id in input_output_data_object_ids:
                    data_object_record = api_client.get_data_object(
                        data_object_id
                    )
                    # Check for orphaned data objects
                    if not data_object_record:
                        logging.error(f"DataObjectNotFound {data_object_id} for {workflow_record['type']}"
                                      f"/{workflow_record['id']}")
                        is_workflow_missing_data_objects = True
                        is_failed_data = True
                        if set_name == "read_qc_analysis_activity_set":
                            is_reads_qc_missing_data_objects = True
                            read_qc_level_failure_count += 1
                            logging.error(f"ReadsQCMissingDataObjects: {workflow_record['id']}, "
                                          f"{workflow_record['name']} failing all data objects")
                        # All other data objects fail if one is missing
                        failing_data_objects.extend(passing_data_objects)
                        passing_data_objects.clear()

                        continue
                    # If OmicsProcessing failed for empty has_output or ReadQC was failed for missing Data Objects,
                    # every data object is failed
                    if is_reads_qc_missing_data_objects or is_omics_missing_has_output:
                        if is_reads_qc_missing_data_objects:
                            error_msg = f"ReadsQCMissingDataObjects: {data_object_id},"
                        else:
                            error_msg = f"OmicsMissingHasOutput: {data_object_id},"
                        logging.error(f"FailedDataObject: {error_msg},")
                        if data_object_record not in failing_data_objects:
                            failing_data_objects.append(data_object_record)
                        failing_data_objects.extend(passing_data_objects)
                        passing_data_objects.clear()
                        continue
                    # If we found a missing data object for  this workflow record, we fail all its data objects
                    if is_workflow_missing_data_objects:
                        logging.error(f"FailedDataObject: {data_object_id},")
                        if data_object_record not in failing_data_objects:
                            failing_data_objects.append(data_object_record)
                        failing_data_objects.extend(passing_data_objects)
                        passing_data_objects.clear()
                        continue

                    # Some legacy Data Objects cannot be be typed. fail the workflow and its data objects
                    data_object_type = data_object_record.get("data_object_type")
                    data_object_url = data_object_record.get("url")
                    if not data_object_type and not data_object_url:
                        logging.error(f"DataObjectNoType: {data_object_id}")
                        if data_object_record not in failing_data_objects:
                            failing_data_objects.append(data_object_record)
                        failing_data_objects.extend(passing_data_objects)
                        passing_data_objects.clear()
                        is_workflow_missing_data_objects = True
                        continue
                    else:
                        logging.info(f"PassingDataObject: {data_object_id}")
                        if data_object_record not in passing_data_objects:
                            passing_data_objects.append(data_object_record)
                        continue

                if passing_data_objects:
                    logging.info(f"passing_data_objects: {len(passing_data_objects)}")
                    db.data_object_set.extend(passing_data_objects)
                if failing_data_objects:
                    logging.error(f"failing_data_objects: {len(failing_data_objects)}")
                    db_failed.data_object_set.extend(failing_data_objects)
                    is_failed_data = True

                # if ReadsQC was failed for missing Data Objects or OmicsProcessing failed has_output, every other
                # workflow record is failed as well
                if is_reads_qc_missing_data_objects or is_omics_missing_has_output:
                    if is_omics_missing_has_output:
                        logging.error(f"OmicsMissingHasOutput: {workflow_record['id']}, {workflow_record['name']}")
                    else:
                        logging.error(f"ReadsQCMissingDataObjects: {workflow_record['id']},  {workflow_record['name']}")
                    failing_records.append(workflow_record)
                # if this workflow had missing data objects, fail it
                elif is_workflow_missing_data_objects:
                    logging.error(f"WorkflowActivityMissingDataObjects: {workflow_record['id']},"
                                    f" {workflow_record['name']}")
                    failing_records.append(workflow_record)
                    is_failed_data = True
                else:
                    passing_records.append(workflow_record)

            if failing_records:
                logging.error(f"FailedRecords: {set_name}, {len(failing_records)}")
                db_failed.__setattr__(set_name, failing_records)
            if passing_records:
                logging.info(f"PassingRecords: {set_name}, {len(passing_records)}")
                db.__setattr__(set_name, passing_records)



        if is_failed_data:
            retrieved_failed_databases.append(db_failed)
        # db is empty if omics_processing has_output is missing
        if not is_omics_missing_has_output:
            retrieved_databases.append(db)

    json_data = json.loads(json_dumper.dumps(retrieved_databases, inject_type=False))
    db_outfile = DATA_DIR.joinpath(f"{study_id}_associated_record_dump.json")
    logging.info(f"Writing {len(retrieved_databases)} records to {db_outfile}")
    logging.info(f"Elapsed time: {time.time() - start_time}")
    with open(db_outfile, "w") as f:
        f.write(json.dumps(json_data, indent=4))

    # write failed records to a separate file if they exist
    if retrieved_failed_databases:
        db_failed_outfile = DATA_DIR.joinpath(f"{study_id}_failed_record_dump.json")
        logging.info(f"Writing {len(retrieved_failed_databases)} failed records to {db_failed_outfile}")
        logging.info(f"Found {omics_level_failure_count} omics processing records with missing has_output")
        logging.info(f"Found {read_qc_level_failure_count} read qc records with missing data objects")
        with open(db_failed_outfile, "w") as f:
            json_data = json.loads(json_dumper.dumps(retrieved_failed_databases, inject_type=False))
            f.write(json.dumps(json_data, indent=4))


@cli.command()
@click.argument("study_id", type=str)
@click.option(
    "--data-dir",
    default=PROD_DATAFILE_DIR,
    help=f"Optional base datafile directory. Default: {PROD_DATAFILE_DIR}",
)
@click.option("--update-links", is_flag=True, default=False)
@click.option("--identifiers-file", type=click.Path(exists=True), required=False)
@click.pass_context
def process_records(ctx, study_id, data_dir, update_links=False, identifiers_file=None):
    """
    Read the JSON file of extracted workflow records and their data objects and
    re-ID the records with newly-minted NMDC IDs, update data file headers.

    Write the results to a new JSON file of nmdc Database instances.
    """
    start_time = time.time()
    logging.info(f"Processing workflow records for study_id: {study_id}")

    # Get API client
    config = ctx.obj["site_config"]
    api_client = NmdcRuntimeApi(config)

    # Get Database dump file paths and the data directory
    db_infile, db_outfile = _get_database_paths(study_id)
    logging.info(f"Using data_dir: {data_dir}")

    # Read the identifiers file if provided as a .tsv file with columns: collection_name, legacy_id, new_id
    if identifiers_file:
        with open(identifiers_file, "r") as f:
            reader = csv.DictReader(f, delimiter="\t")
            identifiers = list(reader)
            logging.info(f"Using {len(identifiers)} identifiers from {identifiers_file}")
        # convert the identifiers to a mapping of (collection_name, legacy_id) -> new_id
        identifiers_map = {(record["collection_name"], record["legacy_id"]): record["new_id"] for record in identifiers}
    else:
        identifiers_map = None

    # Initialize re-ID tool
    reid_tool = ReIdTool(api_client, data_dir, identifiers_map=identifiers_map)

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
        # update Read QC Analysis Activity
        new_db = reid_tool.update_reads_qc_analysis_activity_set(db_record, new_db, update_links)
        # update Metagenome Assembly
        new_db = reid_tool.update_metagenome_assembly_set(db_record, new_db, update_links)
        # update Read Based Taxonomy Analysis
        new_db = reid_tool.update_read_based_taxonomy_analysis_activity_set(
            db_record, new_db, update_links
        )
        # update Metatraanscriptome Activity
        new_db = reid_tool.update_metatranscriptome_activity_set(db_record, new_db, update_links)

        re_ided_db_records.append(new_db)

    write_updated_record_identifiers(reid_tool.updated_record_identifiers, study_id)

    logging.info(f"Writing {len(re_ided_db_records)} records to {db_outfile}")
    logging.info(f"Elapsed time: {time.time() - start_time}")
    json_data = json.loads(json_dumper.dumps(re_ided_db_records, inject_type=False))
    with open(db_outfile, "w") as f:
        f.write(json.dumps(json_data, indent=4))


@cli.command()
@click.option("--mongo-uri",required=False, default="mongodb://localhost:27017",)
@click.option(
    "--production", is_flag=True, default=False,
    help="Use the data file directory for production, default is local"
)
@click.option("--write-to-file", is_flag=True, default=False)
@click.pass_context
def find_affected_workflows(ctx, mongo_uri=None, production=False, write_to_file=False):
    """
    Search for workflow records with incorrectly versioned NMDC IDs. Incorrectly
    versioned IDs have more than one decimal point in the version number. These can
    exist in the database and/or in the data file directory. This command builds a map
    of omics_processing records and their associated workflow records and data paths.
    It then prunes the map to only include records with incorrectly versioned workflow IDs
    and/or data paths. The pruned map is then used to identify the affected records.

    Example of an incorrectly versioned NMDC ID:
        Incorrect: nmdc:wfrqc-11-zbyqeq59.1.1
        Correct: nmdc:wfrqc-11-zbyqeq59.1
    """
    start_time = time.time()
    local_test_omics_processing_ids = ["nmdc:omprc-11-gqbhbd17", "nmdc:omprc-11-wmzpa354"]
    if production:
        data_dir = PROD_DATAFILE_DIR
    else:
        data_dir = LOCAL_DATAFILE_DIR

    # connect to db
    is_direct_connection = ctx.obj["is_direct_connection"]
    database_name = ctx.obj["database_name"]
    client = pymongo.MongoClient(mongo_uri, directConnection=is_direct_connection)
    with pymongo.timeout(5):
        assert (database_name in client.list_database_names()), f"Database {database_name} not found"
    logging.info(f"Connected to MongoDB server at {mongo_uri}")
    db_client = client[database_name]

    # database collections to check
    workflow_collections = [
        "mags_activity_set",
        "metabolomics_analysis_activity_set",
        "metagenome_annotation_activity_set",
        "metagenome_assembly_set",
        "metatranscriptome_activity_set",
        "read_based_taxonomy_analysis_activity_set",
        "read_qc_analysis_activity_set",
    ]
    # directory structure is based on omics_processing_id so
    # we map omics_processing_id, workflow_id, and data_path
    # example_map = {
    #     "nmdc:ompcrc-11-1t150432": [
    #         {"workflow_id": "nmdc:wfrqc-11-zbyqeq59.1.1",
    #         "type": "nmdc:ReadQCAnalysisActivity",
    #         "data_objects": [
    #           {
    #               "id": "nmdc:dobj-11-1tfde585",
    #               "name": ""nmdc_wfrqc-11-pbxpdr12.1.1_filtered.fastq.gz"",
    #               "url": "https://data.microbiomedata.org/data/nmdc:omprc-11-wmzpa354/nmdc:wfrqc-11-pbxpdr12.1.1/nmdc_wfrqc-11-pbxpdr12.1.1_filtered.fastq.gz"
    #            }
    #         ],
    #         "data_paths":
    #           [
    #               "nmdc:omdcrc-11-1t150432/nmdc:wfrqc-11-zbyqeq59.1.1",
    #               "nmdc:omdcrc-11-1t150432/nmdc:wfrqc-11-zbyqeq59.1.1.1",
    #           ]
    #         },
    #     ]
    # }
    omics_processing_workflows_map = {}

    # We will scan all omics_processing records for both malformed workflow IDs and malformed data paths
    # since they can exist independently of each other

    # first get all omics_processing IDs from the database and use them to initialize the map
    logging.info("Initializing omics_processing_workflows_map")
    omics_processing_records = db_client["omics_processing_set"].find({})
    for omics_processing_record in omics_processing_records:
        omics_processing_id = omics_processing_record["id"]
        if production:
            omics_processing_workflows_map[omics_processing_id] = []
        else:
            # for local testing, only initialize the map for the local test omics_processing_id
            if omics_processing_id in local_test_omics_processing_ids:
                omics_processing_workflows_map[omics_processing_id] = []
            else:
                continue

    logging.info(f"Initialized map for {len(omics_processing_workflows_map)} omics_processing records")

    # For each omics_processing_id, find all the workflow records that are informed_by it and add them to the map
    logging.info("Adding workflow records to the map")
    for omics_processing_id in omics_processing_workflows_map.keys():
        for collection_name in workflow_collections:
            workflow_records = db_client[collection_name].find({"was_informed_by": omics_processing_id})
            for workflow_record in workflow_records:
                workflow_id = workflow_record["id"]
                data_objects = []
                for data_object_id in workflow_record.get("has_output", []):
                    data_object_record = db_client["data_object_set"].find_one({"id": data_object_id})
                    if data_object_record:
                        data_objects.append({
                            "id": data_object_record["id"],
                            "name": data_object_record.get("name"),
                            "url": data_object_record.get("url")
                        })
                if not data_objects:
                    logging.warning(f"No data objects found for workflow: {workflow_id}")

                # Look on the filesystem for data file dir path(s) that contain the workflow ID root (non-versioned e.g.
                # nmdc:wfrqc-11-zbyqeq59. These may be different from the workflow ID in the database)
                omics_processing_dir = data_dir.joinpath(omics_processing_id)
                if not omics_processing_dir.exists():
                    logging.warning(f"Directory not found: {omics_processing_dir}")
                    continue
                data_paths = []
                for data_path in omics_processing_dir.iterdir():
                    if workflow_id in data_path.name:
                        data_paths.append(data_path)

                omics_processing_workflows_map[omics_processing_id].append(
                    {
                        "workflow_id": workflow_id,
                        "type": workflow_record["type"],
                        "data_objects": data_objects,
                        "data_paths": [str(data_path) for data_path in data_paths]
                    }
                )

    total_workflow_records = sum([len(records) for records in omics_processing_workflows_map.values()])
    logging.info(f"Added {total_workflow_records} workflow records to the map")

    # Iterate over the map to get  records with malformed workflow IDs and/or data paths
    # anything other that a single decimal point in the workflow ID is considered malformed
    # example incorrect workflow ID: nmdc:wfrqc-11-zbyqeq59.1.1
    # example correct workflow ID: nmdc:wfrqc-11-zbyqeq59.1
    logging.info("Pruning the map to only include records with malformed workflow IDs and/or data paths")
    pruned_map = {}
    for omics_processing_id, workflow_records in omics_processing_workflows_map.items():
        for record in workflow_records:
            workflow_id = record["workflow_id"]
            # look for anything other than a single decimal point in the workflow ID
            if  workflow_id.count(".") != 1:
                logging.info(f"Found record with malformed workflow ID: {workflow_id}")
                if omics_processing_id not in pruned_map:
                    pruned_map[omics_processing_id] = []
                pruned_map[omics_processing_id].append(record)
                continue

            data_paths = record["data_paths"]
            for data_path in data_paths:
                if data_path.count(".") != 1:
                    logging.info(f"Found record with malformed data path: {data_path}")
                    if omics_processing_id not in pruned_map:
                        pruned_map[omics_processing_id] = []
                    pruned_map[omics_processing_id].append(record)



    # Serialize the map for writing to a file or displaying
    serialized_map = json.dumps(pruned_map, indent=4)
    if write_to_file:
        map_outfile = Path("affected_workflow_records.json")
        logging.info(f"Writing affected workflow records to {map_outfile}")
        with open(map_outfile, "w") as f:
            f.write(serialized_map)
    else:
        logging.info(serialized_map)


@cli.command()
@click.pass_context
def update_affected_workflows(ctx):
    """
    Read the JSON file of affected workflow records and their data paths and
    fix the malformed workflow IDs and/or data paths and update the data files:
    - Fix malformed workflow IDs and write out update changes to a JSON file, one per affected collection to be used
        with the /queries:run endpoint
    """
    start_time = time.time()

    affected_records_file = Path("affected_workflow_records.json")
    logging.info(f"Reading affected workflow records from {affected_records_file}")
    with open(affected_records_file, "r") as f:
        affected_records = json.load(f)

    # Iterate over the affected records and fix the malformed workflow IDs and/or data paths and output the changes
    # to a JSON file

    updates_map = {}
    for omics_processing_id, records in affected_records.items():
        for record in records:
            workflow_id = record["workflow_id"]
            collection_name = get_collection_name_from_workflow_id(workflow_id)
            # Fix the workflow ID
            fixed_workflow_id = fix_malformed_workflow_id_version(workflow_id)
            if collection_name not in updates_map:
                updates_map[collection_name] = {"update": collection_name, "updates": []}
            updates_map[collection_name]["updates"].append(
                {"q": {"id": workflow_id}, "u": {"$set": {"id": fixed_workflow_id}}}
            )
    # Write updates to JSON files, one per affected collection
    for collection_name, update in updates_map.items():
        update_outfile = Path(f"{collection_name}_updates.json")
        logging.info(f"Writing updates to {update_outfile}")
        with open(update_outfile, "w") as f:
            f.write(json.dumps(update, indent=4))

    elapsed_time = time.time() - start_time
    logging.info(f"Elapsed time: {elapsed_time}")

@cli.command()
@click.option("--production", is_flag=True, default=False)
@click.option("--update-files", is_flag=True, default=False)
@click.pass_context
def update_affected_data_files(ctx, production=False, update_files=False):
    """
    Read the JSON file of affected workflow records and their data paths and
    fix the malformed workflow IDs and/or data paths and update the data files:
    """
    start_time = time.time()
    if production:
        data_dir = PROD_DATAFILE_DIR
    else:
        data_dir = LOCAL_DATAFILE_DIR

    affected_records_file = Path("affected_workflow_records.json")
    logging.info(f"Reading affected workflow records from {affected_records_file}")
    with open(affected_records_file, "r") as f:
        affected_records = json.load(f)

    # Iterate over the affected records and fix the malformed workflow IDs and/or data paths and update the data files
    for omics_processing_id, records in affected_records.items():
        for record in records:
            workflow_id = record["workflow_id"]
            data_paths = record["data_paths"]
            fixed_workflow_id = fix_malformed_workflow_id_version(workflow_id)
            for data_path in data_paths:
                data_path = Path(data_path)
                fixed_data_path = data_path.parent.joinpath(fixed_workflow_id)
                if update_files:
                    logging.info(f"Updating data file: {data_path}")
                    data_path.rename(fixed_data_path)
                    # for backwards compatibility, symlink the malformed data path to the fixed data path
                    data_path.symlink_to(fixed_data_path)



                else:
                    logging.info(f"Would update data file: {data_path} to {fixed_data_path}")

    elapsed_time = time.time() - start_time
    logging.info(f"Elapsed time: {elapsed_time}")


@cli.command()
@click.argument("reid_records_file", type=click.Path(exists=True))
@click.option("--mongo-uri",required=False, default="mongodb://localhost:27017",)
@click.pass_context
def ingest_records(ctx, reid_records_file, mongo_uri):
    """
    Read in json dump of re_id'd records and:
    - validate the records against the /metadata/json:validate endpoint
    - insert the records into the MongoDB database defined by the --mongo-uri and --database-name options

    """
    start_time = time.time()
    logging.info(f"Submitting re id'd records from : {reid_records_file}")
    reid_records_filename = Path(reid_records_file).name
    reid_base_name = reid_records_filename.split("_")[0]

    # Get API client(s)
    config = ctx.obj["site_config"]
    api_user_client = NmdcRuntimeUserApi(config)
    logging.info(f"Using: {api_user_client.base_url}")
    logging.info(f"Using MongoDB URI: {mongo_uri}")

    # Connect to the MongoDB server and check the database name
    is_direct_connection = ctx.obj["is_direct_connection"]
    database_name = ctx.obj["database_name"]
    client = pymongo.MongoClient(mongo_uri, directConnection=is_direct_connection)
    with pymongo.timeout(5):
        assert (database_name in client.list_database_names()), f"Database {database_name} not found"
    logging.info(f"Connected to MongoDB server at {mongo_uri}")
    db_client = client[database_name]
    session = client.start_session()


    with open(reid_records_file, "r") as f:
        db_records = json.load(f)
    with session.start_transaction():
        try:
            _ingest_records(db_records, db_client, api_user_client)
            session.commit_transaction()
        except Exception as e:
            logging.error(f"An error occurred - aborting transaction")
            session.abort_transaction()
            logging.exception(f"An error occurred while ingesting records: {e}")


    logging.info(f"Elapsed time: {time.time() - start_time}")


@cli.command()
@click.argument("old_records_file", type=click.Path(exists=True))
@click.option("--mongo-uri",required=False, default="mongodb://localhost:27017",)
@click.pass_context
def delete_old_records(ctx, old_records_file, mongo_uri):
    """
    Read in json dump of old records and:
    delete them using
    /queries/run endpoint

    Outputs a tsv file with the (collection_name, optional(type), id) of the deleted records
    """
    start_time = time.time()
    logging.info(f"Deleting old objects found in : {old_records_file}")
    old_records_filename = Path(old_records_file).name
    old_base_name = old_records_filename.split("_")[0]
    deleted_record_identifiers = []

    # Get PyMongo client
    is_direct_connection = ctx.obj["is_direct_connection"]
    database_name = ctx.obj["database_name"]
    client = pymongo.MongoClient(mongo_uri, directConnection=is_direct_connection)
    with pymongo.timeout(5):
        assert (database_name in client.list_database_names()), f"Database {database_name} not found"
    db = client[database_name]
    session = client.start_session()

    # get old db records
    with open(old_records_file, "r") as f:
        old_db_records = json.load(f)

    # set list to capture annotation genes for agg set
    annotation_ids = set()
    with session.start_transaction():
        try:
            for record_identifier in old_db_records:
                for set_name, object_record in record_identifier.items():
                    # we don't want to delete the omics_processing_set
                    if set_name == "omics_processing_set":
                        continue
                    delete_ids = []
                    if isinstance(object_record, list):
                        for item in object_record:
                            delete_ids.append(item["id"])
                            deleted_record_identifiers.append((set_name, item.get("type", ""), item["id"]))
                            if set_name in ["metagenome_annotation_activity_set", "metatranscriptome_activity_set"]:
                                annotation_ids.add(item["id"])

                    # Construct filter query
                    filter_query = {"id": {"$in": delete_ids}}
                    logging.info(f"Deleting {len(delete_ids)} records from {set_name}")
                    # Delete the records
                    try:
                        delete_result = db[set_name].delete_many(filter_query)
                        logging.info(f"Deleted {delete_result.deleted_count} records from {set_name}")
                    except Exception as e:
                        logging.exception(f"An error occurred while deleting {set_name} records: {e}")

            # delete functional annotation agg records
            if annotation_ids:
                logging.info(f"Searching for functional annotations for {len(annotation_ids)} annotation activities")
                filter_query = {"metagenome_annotation_id": {"$in": list(annotation_ids)}}
                try:
                    delete_result = db["functional_annotation_agg"].delete_many(filter_query)
                    logging.info(f"Deleted {delete_result.deleted_count} functional annotation records")
                except Exception as e:
                    logging.exception(f"An error occurred while deleting functional annotation records: {e}")
            session.commit_transaction()
        except Exception as e:
            logging.error(f"An error occurred - dumping deleted record identifiers")
            _write_deleted_record_identifiers(deleted_record_identifiers, old_base_name)
            logging.exception(f"An error occurred while deleting records: {e}")
            session.abort_transaction()

    _write_deleted_record_identifiers(deleted_record_identifiers, old_base_name)

    logging.info(f"Elapsed time: {time.time() - start_time}")


@cli.command()
@click.argument("mongo_uri", type=str)
@click.option("--no-delete", is_flag=True, default=False)
@click.pass_context
def delete_old_binning_data(ctx, mongo_uri, no_delete=False):
    """
    Delete old binning data with non-comforming IDs from the MongoDB database.

    Some binning data objects can be found by their data_object_type: 'Metagenome Bins' or 'CheckM Statistics'
    Un-typed data objects can be found by looking for 'metabat2' in the description

    Also deletes proteomics data objects with an ID pattern of 'emsl:output_'

    If the --no-delete flag is set, the script will not delete any records, but will log the records that would be
    deleted.
    """
    start_time = time.time()
    database_name = ctx.obj["database_name"]
    logging.info(f"Deleting old binning data from {database_name} database at {mongo_uri}")

    # Connect to the MongoDB server and check the database name
    is_direct_connection = ctx.obj["is_direct_connection"]
    client = pymongo.MongoClient(mongo_uri, directConnection=is_direct_connection)
    with pymongo.timeout(5):
        assert (database_name in client.list_database_names()), f"Database {database_name} not found"
    logging.info(f"Connected to MongoDB server at {mongo_uri}")
    db_client = client[database_name]

    logging.info("Searching for old binning data records with a known data object type and non-comforming IDs")
    # Find and delete old binning data with a known data object type and non-comforming IDs
    binning_data_query = {
          # Exclude data objects with conforming IDs nmdc:dobj-*
        "id": {"$not": {"$regex": "^nmdc:dobj-"}},
        "data_object_type": {"$in": ["Metagenome Bins", "CheckM Statistics"]},
    }
    binning_data = db_client["data_object_set"].find(binning_data_query)
    logging.info(f"Found {len(list(binning_data.clone()))} old binning data records")
    if not no_delete:
        for record in binning_data:
            logging.info(f"Deleting binning data record: {record['id']} {record['data_object_type']} {record['description']}")
        logging.info(f"Deleting old binning data records")
        delete_result = db_client["data_object_set"].delete_many(binning_data_query)
        logging.info(f"Deleted {delete_result.deleted_count} old binning data records")
    else:
        logging.info("No-delete flag is set, skipping delete")
        for record in binning_data:
            logging.info(f"Skipping delete for record: {record['id']} {record['data_object_type']} {record['description']}")

    # Find and delete old binning data with a null data object type and 'metabat2' in the description and
    # non-comforming IDs
    logging.info("Searching for old binning data records with a null data object type and 'metabat2' in the description")
    null_binning_data_query = {
        # Exclude data objects with conforming IDs nmdc:dobj-*
        "id": {"$not": {"$regex": "^nmdc:dobj-"}},
        "data_object_type": None,
        "description": {"$regex": "metabat2"},
    }
    null_binning_data = db_client["data_object_set"].find(null_binning_data_query)
    logging.info(f"Found {len(list(null_binning_data.clone()))} old null binning data records")
    if not no_delete:
        for record in null_binning_data:
            logging.info(f"Deleting null binning data record: {record['id']} {record['description']}")
        logging.info(f"Deleting old null binning data records")
        delete_result = db_client["data_object_set"].delete_many(null_binning_data_query)
        logging.info(f"Deleted {delete_result.deleted_count} old null binning data records")
    else:
        logging.info("No-delete flag is set, skipping delete")
        for record in null_binning_data:
            logging.info(f"Skipping delete for record: {record['id']} /{record['description']}")

    # Find Lipidomics OmicsProcessing and their associated DataObjects and delete them
    logging.info("Searching for Lipidomics OmicsProcessing records and their associated DataObjects")
    lipidomics_omics_processing_query = {
        "omics_type.has_raw_value": "Lipidomics",
    }
    lipidomics_omics_processing = db_client["omics_processing_set"].find(lipidomics_omics_processing_query)
    logging.info(f"Found {len(list(lipidomics_omics_processing.clone()))} lipidomics omics processing records")

    # Go through the lipidomics omics processing records and get the data object IDs to be deleted
    lipidomics_data_object_ids = set()
    for record in lipidomics_omics_processing:
        logging.info(f"Found lipidomics omics processing record: {record['id']}")
        for data_object_id in record["has_output"]:
            lipidomics_data_object_ids.add(data_object_id)
    logging.info(f"Found {len(lipidomics_data_object_ids)} lipidomics data object records")

    if not no_delete:
        for data_object_id in lipidomics_data_object_ids:
            logging.info(f"Deleting lipidomics data object record: {data_object_id}")
        logging.info(f"Deleting lipidomics data object records")
        delete_result = db_client["data_object_set"].delete_many({"id": {"$in": list(lipidomics_data_object_ids)}})
        logging.info(f"Deleted {delete_result.deleted_count} lipidomics data object records")
        # delete the lipidomics omics processing records
        delete_result = db_client["omics_processing_set"].delete_many(lipidomics_omics_processing_query)
        logging.info(f"Deleted {delete_result.deleted_count} lipidomics omics processing records")
    else:
        logging.info("No-delete flag is set, skipping delete")
        for data_object_id in lipidomics_data_object_ids:
            logging.info(f"Skipping delete for lipidomics data object record: {data_object_id}")
        for record in lipidomics_omics_processing:
            logging.info(f"Skipping delete for lipidomics omics processing record: {record['id']}")


    logging.info(f"Elapsed time: {time.time() - start_time}")


@cli.command()
@click.argument("study_id", type=str)
@click.option("--api-base-url", default=NAPA_BASE_URL,
              help=f"Optional base URL for the NMDC API. Default: {NAPA_BASE_URL}")
@click.option("--untyped-data-objects", is_flag=True, default=False)
@click.pass_context
def find_missing_data_objects(ctx, study_id, api_base_url, untyped_data_objects=False):
    """
    Scan project data directories, read in the data object records from 'data_objects.json'
    and find data objects that:
    - are associated with one or more workflow activities has_input or has_output
    - are not present in the data_objects collection in the NMDC database

    Write the results to a JSON file of nmdc DataObject instances.
    """
    start_time = time.time()
    logging.info(f"Scanning for missing data objects for {study_id}")


    api_client = NmdcApi(api_base_url)
    with open("unique_data_objects.json", "r") as f:
        data_objects = json.load(f)
    # index the data objects by ID
    data_objects_by_id = {data_object["id"]: data_object for data_object in data_objects}


    # 1. Retrieve all OmicsProcessing records for the updated NMDC study ID
    omics_processing_records = (
        api_client.get_omics_processing_records_part_of_study(
            study_id
        ))
    missing_data_object_ids = set()
    untyped_data_objects = []
    # 2. For each OmicsProcessing record, find the legacy identifier:
    for omics_processing_record in omics_processing_records:
        informed_by_id = _get_legacy_id(omics_processing_record)
        for activity_set_name in ANALYSIS_ACTIVITIES:
            workflow_records = api_client.get_workflow_activities_informed_by(activity_set_name, informed_by_id)
            for workflow_record in workflow_records:
                data_object_ids = set()
                data_object_ids.update(workflow_record["has_input"])
                data_object_ids.update(workflow_record["has_output"])

                # Search the data object IDs
                for data_object_id in data_object_ids:
                    data_object_record = api_client.get_data_object(data_object_id)

                    if untyped_data_objects:
                        # if missing url and data_object_type, add to untyped_data_objects
                        if not data_object_record.get("url") and not data_object_record.get("data_object_type"):
                            untyped_data_objects.append(data_object_record)
                            continue
                        else:
                            continue

                    if not data_object_record:
                        logging.warning(f"{informed_by_id} : {workflow_record['id']} "
                                       f"{workflow_record['name']} missing: {data_object_id}")
                        missing_data_object_ids.add(data_object_id)
                        continue

    logging.info(f"Elapsed time: {time.time() - start_time}")
    if untyped_data_objects:
        logging.info(f"Writing {len(untyped_data_objects)} untyped data objects to untyped_data_objects.json")
        with open(f"{study_id}_untyped_data_objects.json", "w") as f:
            f.write(json.dumps(untyped_data_objects, indent=4))
    else:
        logging.info(f"Found {len(missing_data_object_ids)} missing data objects")
        # get missing data objects from the data_objects_by_id if present
        missing_data_objects = []
        for data_object_id in missing_data_object_ids:
            if data_object_id in data_objects_by_id:
                missing_data_objects.append(data_objects_by_id[data_object_id])
            else:
                logging.warning(f"Missing data object {data_object_id} not found in data_objects.json")
        logging.info(f"Writing {len(missing_data_objects)} missing data objects to missing_data_objects.json")
        if missing_data_objects:
            with open(f"{study_id}_missing_data_objects.json", "w") as f:
                f.write(json.dumps(missing_data_objects, indent=4))


@cli.command()
@click.argument("data-objects-file", type=click.Path(exists=True))
def get_unique_data_objects(data_objects_file):
    """
    Read in a raw json dump of data objects and return a list of unique data objects
    as a json dump.
    """
    with open(data_objects_file, "r") as f:
        data_objects = json.load(f)

    unique_data_objects = []
    unique_data_object_ids = set()
    for data_object in data_objects:
        if data_object["id"] not in unique_data_object_ids:
            unique_data_objects.append(data_object)
            unique_data_object_ids.add(data_object["id"])
    with open("unique_data_objects.json", "w") as f:
        f.write(json.dumps(unique_data_objects, indent=4))


def _get_database_paths(study_id):
    """
    Return the paths to the input and output data files
    """
    db_infile_suffix = "_associated_record_dump.json"
    db_outfile_suffix = "_re_ided_record_dump.json"
    db_infile = DATA_DIR.joinpath(study_id, f"{study_id}{db_infile_suffix}")
    db_outfile = DATA_DIR.joinpath(study_id, f"{study_id}{db_outfile_suffix}")
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
        logging.debug(
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


def _get_has_input_from_read_qc(api_client, legacy_id):
    """
    Get the has_input data objects for the given legacy ID
    """
    read_qc_records = api_client.get_workflow_activities_informed_by(
        "read_qc_analysis_activity_set", legacy_id
    )
    has_input_data_objects = set()
    for record in read_qc_records:
        has_input_data_objects.update(record.get("has_input", []))
    return list(has_input_data_objects)


def _update_study(study: nmdc.Study, legacy_study_id: str, nmdc_study_id: str) -> nmdc.Study:
    """
    Update the study record.
     - Update the ID
        - Add the legacy ID to gold_study_identifiers if it is not already there
    """
    updated_study = deepcopy(study)
    updated_study.id = nmdc_study_id
    if legacy_study_id.startswith("gold:"):
        updated_study.gold_study_identifiers = list(set(updated_study.gold_study_identifiers + [legacy_study_id]))
    return updated_study


def _log_updates(updates):
    for collection_name, record_updates in updates.items():
        logging.info(f"{len(record_updates)} updates for collection: {collection_name}")
        for _id, (model, update) in record_updates.items():
            logging.info(f"Updating {_id} / {model.id} in {collection_name} with {len(update)} changes")
            for attr, updated_value in update.items():
                # original_value = getattr(model, attr)
                logging.info(f"  {attr}: {updated_value}")


def _write_updates(updates, nmdc_study_id):
    # Create a directory for the study if it doesn't exist
    study_dir = DATA_DIR.joinpath(nmdc_study_id)
    study_dir.mkdir(parents=True, exist_ok=True)

    # Write the updated records to a tsv file using csv writer in data_dir/study_id/study_id_updates.tsv
    updates_file = study_dir.joinpath(f"{nmdc_study_id}_updates.tsv")
    logging.info(f"Writing {len(updates)} updates to {updates_file}")
    # see if the file already exists - if so, append to it
    if updates_file.exists():
        logging.info(f"Appending to existing file: {updates_file}")
        mode = "a"
    else:
        logging.info(f"Creating new file: {updates_file}")
        mode = "w"
    with open(updates_file, mode) as f:
        writer = csv.writer(f, delimiter="\t")
        if mode == "w":
            writer.writerow(["collection_name", "id", "_id", "update"])
        for collection_name, record_updates in updates.items():
            for _id, (model, update) in record_updates.items():
                updated_fields = ", ".join(update.keys())
                writer.writerow([collection_name, model.id, _id, update])


def _write_deletions(deletions, nmdc_study_id):
    # Create a directory for the study if it doesn't exist
    study_dir = DATA_DIR.joinpath(nmdc_study_id)
    study_dir.mkdir(parents=True, exist_ok=True)

    # Write the deleted records to a tsv file using csv writer in data_dir/study_id/study_id_deletions.tsv
    deletions_file = study_dir.joinpath(f"{nmdc_study_id}_deletions.tsv")
    logging.info(f"Writing {len(deletions)} deletions to {deletions_file}")
    # see if the file already exists - if so, append to it
    if deletions_file.exists():
        logging.info(f"Appending to existing file: {deletions_file}")
        mode = "a"
    else:
        logging.info(f"Creating new file: {deletions_file}")
        mode = "w"
    with open(deletions_file, mode) as f:
        writer = csv.writer(f, delimiter="\t")
        if mode == "w":
            writer.writerow(["collection_name", "id", "_id"])
        for collection_name, records in deletions.items():
            for record in records:
                writer.writerow([collection_name, record["id"], record["_id"]])


def _ingest_records(db_records, db_client, api_user_client):
    for record in db_records:
        # remove the omics_processing_set and use it to generate
        # changes to omics_processing has_output
        omics_processing_set = record.pop("omics_processing_set")
        for omics_processing_record in omics_processing_set:
            omics_processing_id = omics_processing_record["id"]
            logging.info(f"omics_processing_id: {omics_processing_id}")
            # Update the omics_processing_record with the new has_output via PyMongo
            filter_criteria = {"id": omics_processing_id}
            update_criteria = {"$set": {"has_output": omics_processing_record["has_output"]}}
            result = db_client["omics_processing_set"].update_one(filter_criteria, update_criteria)
            logging.info(f"Updated {result.modified_count} omics_processing_set records")

        # validate the record
        if api_user_client.validate_record(record):
            logging.info("DB Record validated - submitting to API")
            # json:submit endpoint does not work on the Napa API
            # submission_response = api_user_client.submit_record(record)
            # logging.info(f"Record submission response: {submission_response}")

            # submit the record documents directly via the MongoDB client
            # this isa workaround for the json:submit endpoint not working
            for collection_name, collection in record.items():
                # collection shouldn't be empty but check just in case
                if not collection:
                    logging.warning(f"Empty collection: {collection_name}")
                    continue
                logging.info(f"Inserting {len(collection)} records into {collection_name}")

                insertion_result = db_client[collection_name].insert_many(collection, ordered=False)
                logging.info(f"Inserted {len(insertion_result.inserted_ids)} records into {collection_name}")
        else:
            logging.error("Workflow Record validation failed")


def _write_deleted_record_identifiers(deleted_record_identifiers, old_base_name):
    # write the deleted records to a tsv file
    deleted_record_identifiers_file = DATA_DIR.joinpath(f"{old_base_name}_deleted_record_identifiers.tsv")
    logging.info(
        f"Writing {len(deleted_record_identifiers)} deleted record identifiers to {deleted_record_identifiers_file}"
        )
    with open(deleted_record_identifiers_file, "w") as f:
        f.write("collection_name\ttype\tid\n")
        for record_identifier in deleted_record_identifiers:
            f.write("\t".join(record_identifier) + "\n")




if __name__ == "__main__":
    cli(obj={})

