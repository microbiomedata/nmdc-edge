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
import pymongo

from nmdc_automation.api import NmdcRuntimeApi, NmdcRuntimeUserApi
from nmdc_automation.nmdc_common.client import NmdcApi
import nmdc_schema.nmdc as nmdc
from nmdc_automation.re_iding.base import ReIdTool
from nmdc_automation.re_iding.changesheets import Changesheet, ChangesheetLineItem
from nmdc_automation.re_iding.db_utils import get_omics_processing_id, ANALYSIS_ACTIVITIES

# Defaults
GOLD_STUDY_ID = "gold:Gs0114663"
STUDY_ID = "nmdc:sty-11-aygzgv51"
NAPA_CONFIG = Path("../../../configs/.local_napa_config.toml")
NAPA_BASE_URL = "https://api-napa.microbiomedata.org/"

STUDIES = {
    "Stegen": ("nmdc:sty-11-aygzgv51", "gold:Gs0114663"),
    "SPRUCE": ("nmdc:sty-11-33fbta56", "gold:Gs0110138"),
    "EMP": ("nmdc:sty-11-547rwq94", "gold:Gs0154244"),
    "Luquillo": ("nmdc:sty-11-076c9980", "gold:Gs0128850"),
    "CrestedButte": ("nmdc:sty-11-dcqce727", "gold:Gs0135149"),
}


BASE_DATAFILE_DIR = "/global/cfs/cdirs/m3408/results"

DATA_DIR = Path(__file__).parent.absolute().joinpath("data")
DRYRUN_DATAFILE_DIR = DATA_DIR.joinpath("dryrun_data/results")
LOG_PATH = DATA_DIR.joinpath("re_id_tool.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


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
@click.argument("study_id", type=str)
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
    logging.info(f"Extracting workflow records for study_id: {study_id}")
    logging.info(f"study_id: {study_id}")

    config = ctx.obj["site_config"]
    # api_client = NmdcRuntimeUserApi(config)
    api_client = NmdcApi(api_base_url)

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
            # If the data object is an orphan, fail the omics processing record and its data objects
            if not data_object_record:
                logging.error(f"OmicsProcessingOrphanDataObject: {data_object_id} for {omics_id}")
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

                    # Some legacy Data Objects cannot be readily typed - warn but add to passing data objects
                    data_object_type = data_object_record.get("data_object_type")
                    data_object_url = data_object_record.get("url")
                    if not data_object_type and not data_object_url:
                        logging.warning(f"DataObjectNoType: {data_object_id}")
                        if data_object_record not in passing_data_objects:
                            passing_data_objects.append(data_object_record)
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
    default=BASE_DATAFILE_DIR,
    help=f"Optional base datafile directory. Default: {BASE_DATAFILE_DIR}",
)
@click.option("--update-links", is_flag=True, default=False)
@click.pass_context
def process_records(ctx, study_id, data_dir, update_links=False):
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
        new_db = reid_tool.update_reads_qc_analysis_activity_set(db_record, new_db, update_links)
        # files
        # TODO - update reads qc files
        # update Metagenome Assembly
        new_db = reid_tool.update_metagenome_assembly_set(db_record, new_db, update_links)
        # update Read Based Taxonomy Analysis
        new_db = reid_tool.update_read_based_taxonomy_analysis_activity_set(
            db_record, new_db, update_links
        )
        # update Metatraanscriptome Activity
        new_db = reid_tool.update_metatranscriptome_activity_set(db_record, new_db, update_links)

        re_ided_db_records.append(new_db)

    logging.info(f"Writing {len(re_ided_db_records)} records to {db_outfile}")
    logging.info(f"Elapsed time: {time.time() - start_time}")
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
@click.option("--mongo-uri",required=False, default="mongodb://localhost:27017",)
@click.option(
    "--is-direct-connection",
    type=bool,
    required=False,
    default=True,
    show_default=True,
    help=f"Whether you want the script to set the `directConnection` flag when connecting to the MongoDB server. "
         f"That is required by some MongoDB servers that belong to a replica set. ",
)
@click.option(
    "--database-name",
    type=str,
    required=False,
    default="nmdc",
    show_default=True,
    help=f"MongoDB database name",
)
@click.pass_context
def ingest_records(ctx, reid_records_file, changesheet_only, mongo_uri=None,
                   is_direct_connection=True, database_name="nmdc"):
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
    # api_client = NmdcRuntimeApi(config)
    api_user_client = NmdcRuntimeUserApi(config)

    # TODO - need to get mongo_uri credentials for the Napa DB instance in the config file. Meanwhile, we can test
    #  with a local MongoDB instance
    logging.info(f"Using MongoDB URI: {mongo_uri}")

    # Connect to the MongoDB server and check the database name
    client = pymongo.MongoClient(mongo_uri, directConnection=is_direct_connection)
    with pymongo.timeout(5):
        assert (database_name in client.list_database_names()), f"Database {database_name} not found"
    logging.info(f"Connected to MongoDB server at {mongo_uri}")
    db_client = client[database_name]


    with open(reid_records_file, "r") as f:
        db_records = json.load(f)

    changesheet = Changesheet(name=f"{reid_base_name}_changesheet")
    for record in db_records:
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
            # validate the record
            if api_user_client.validate_record(record):
                logging.info("DB Record validated")
                # submit the record documents directly via the MongoDB client
                for collection_name, collection in record.items():
                    # collection shouldn't be empty but check just in case
                    if not collection:
                        logging.warning(f"Empty collection: {collection_name}")
                        continue
                    logging.info(f"Inserting {len(collection)} records into {collection_name}")
                    insertion_result = db_client[collection_name].insert_many(collection)
                    logging.info(f"Inserted {len(insertion_result.inserted_ids)} records into {collection_name}")
            else:
                logging.error("Workflow Record validation failed")
        else:
            logging.info(f"changesheet_only is True, skipping Workflow and Data Object ingest")

    changesheet.write_changesheet()
    logging.info(f"changesheet written to {changesheet.output_filepath}")
    if changesheet.validate_changesheet(api_user_client.base_url):
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
    start_time = time.time()
    logging.info(f"Deleting old objects found in : {old_records_file}")
    old_records_filename = Path(old_records_file).name
    old_base_name = old_records_filename.split("_")[0]

    # Get API client(s)
    config = ctx.obj["site_config"]
    api_user_client = NmdcRuntimeUserApi(config)
    logging.info(f"Using: {api_user_client.base_url}")

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
                            logging.info(f"Deleting {item.get('type')} record: {item['id']}")
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
    logging.info(f"Elapsed time: {time.time() - start_time}")


@cli.command()
@click.argument("study_id", type=str)
@click.option("--api-base-url", default=NAPA_BASE_URL,
              help=f"Optional base URL for the NMDC API. Default: {NAPA_BASE_URL}")
@click.option("--untyped-data-objects", is_flag=True, default=False)
@click.pass_context
def orphan_data_objects(ctx, study_id, api_base_url, untyped_data_objects=False):
    """
    Scan project data directories, read in the data object records from 'data_objects.json'
    and find data objects that:
    - are associated with one or more workflow activities has_input or has_output
    - are not present in the data_objects collection in the NMDC database

    Write the results to a JSON file of nmdc DataObject instances.
    """
    start_time = time.time()
    logging.info(f"Scanning for orphaned data objects for {study_id}")


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
    orphan_data_object_ids = set()
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
                        orphan_data_object_ids.add(data_object_id)
                        continue

    logging.info(f"Elapsed time: {time.time() - start_time}")
    if untyped_data_objects:
        logging.info(f"Writing {len(untyped_data_objects)} untyped data objects to untyped_data_objects.json")
        with open(f"{study_id}_untyped_data_objects.json", "w") as f:
            f.write(json.dumps(untyped_data_objects, indent=4))
    else:
        logging.info(f"Found {len(orphan_data_object_ids)} orphaned data objects")
        # get orphaned data objects from the data_objects_by_id if present
        orphaned_data_objects = []
        for data_object_id in orphan_data_object_ids:
            if data_object_id in data_objects_by_id:
                orphaned_data_objects.append(data_objects_by_id[data_object_id])
            else:
                logging.warning(f"orphaned data object {data_object_id} not found in data_objects.json")
        logging.info(f"Writing {len(orphaned_data_objects)} orphaned data objects to orphaned_data_objects.json")
        if orphaned_data_objects:
            with open(f"{study_id}_orphaned_data_objects.json", "w") as f:
                f.write(json.dumps(orphaned_data_objects, indent=4))


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


if __name__ == "__main__":
    cli(obj={})
