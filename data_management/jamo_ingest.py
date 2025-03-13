"""
NMDC Workflow Data Processing Script
Retrieves workflow execution data from NMDC API, processes it, and generates metadata files.
Handles workflow execution records and their associated data objects.
"""

import json
import yaml
import os
import requests
import click
from typing import Dict, List, Optional
import logging
import traceback
import argparse

_BASE_URL = "https://api.microbiomedata.org/"


# File Operations
def save_json(data: Dict, filename: str):
    """
    Save dictionary data to a JSON file with proper formatting.

    Args:
        data: Dictionary to be saved
        filename: Target JSON file path

    Raises:
        OSError: If directory creation or file writing fails
    """
    # Create directory path if it doesn't exist
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, 'w+') as f:
        json.dump(data, f, indent=4)


def load_json(filename: str) -> Dict:
    """
    Load and parse a JSON file into a dictionary.

    Args:
        filename: Path to JSON file to load

    Returns:
        Dictionary containing parsed JSON data
    """
    with open(filename) as f:
        return json.load(f)


# API Query Functions
def query_collection(base_url: str, collection_name: str,
                     max_page_size: Optional[int] = None,
                     filter_param: Optional[str] = None) -> Dict:
    """
    Query the metadata from a specific collection.

    Args:
        base_url: The base URL of the API
        collection_name: The name of the collection to query
        max_page_size: Maximum number of records to query per page
        filter_param: Optional MongoDB-style filter query string

    Returns:
        Dictionary containing the API response data

    Raises:
        requests.RequestException: If the API request fails
    """
    url = f"{base_url}nmdcschema/{collection_name}"
    params = {}
    if max_page_size:
        params['max_page_size'] = max_page_size
    if filter_param:
        params['filter'] = filter_param

    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def get_data_object_set(base_api_url: str, max_page_size: int) -> Dict:
    """
    Retrieve data objects with URLs from the data_object_set collection.

    Creates a lookup dictionary mapping object IDs to their full record data.
    Only includes records that have a URL field.

    Args:
        base_api_url: Base API URL
        max_page_size: Maximum number of records to retrieve

    Returns:
        Dictionary mapping object IDs to their complete record data
    """
    collection_name = "data_object_set"
    filter_param = '{"url": {"$exists": true}}'  # Filter to retrieve only records with a URL
    collection_data = query_collection(base_api_url, collection_name, max_page_size, filter_param)

    kv_store = {}
    for item in collection_data.get("resources", []):
        item_id = item.get("id")
        if item_id:
            kv_store[item_id] = item
    return kv_store


def get_workflow_execution_set(base_api_url: str = _BASE_URL, max_page_size: int = 100000) -> Dict[str, List[str]]:
    """
    Query workflow execution records and organize them by workflow type.

    Queries the workflow_execution_set collection, validates each record against
    the data_object_set collection, and groups valid records by their workflow type.
    Results are saved to a JSON file.

    Args:
        base_api_url: Base URL for the API endpoint
        max_page_size: Maximum number of records to retrieve per query

    Returns:
        Dictionary where:
            - key (str): workflow_execution_id
            - value (List): [workflow_execution_type (str), list_of_records (List[Dict])]
    """
    # TODO: support pagination if records exceed max_page_size

    # Get workflow records
    workflow_records = query_collection(base_api_url, "workflow_execution_set", max_page_size)
    click.echo(f"Workflow Executions Set: {len(workflow_records.get('resources', []))} records retrieved.")

    # Get data object set
    data_object_set = get_data_object_set(base_api_url, max_page_size)
    click.echo(f"Data Object Set: {len(data_object_set)} records retrieved.")

    # Process workflows
    workflow_outputs_dict = {}
    for record in workflow_records.get("resources", []):
        has_output_list = record.get("has_output", [])
        workflow_execution = record.get("type").removeprefix("nmdc:")
        workflow_execution_id = record.get("id")
        valid_records = []
        for output_id in has_output_list:
            # Cross-reference workflow outputs against data_object_set to filter out invalid/missing records
            output_record = data_object_set.get(output_id)
            if output_record:
                valid_records.append(output_record)
        workflow_outputs_dict[workflow_execution_id] = [workflow_execution, valid_records]

    # Save results
    save_json(workflow_outputs_dict, "valid_data/valid_data.json")
    # throws an exception due to makedirs in save_json if filename does not contain dir in path
    # add try except block, and print stack trace using traceback module

    return workflow_outputs_dict


def create_json_structure(workflow_execution_id: str, workflow_execution: str, metadata_keys_list: List[Dict]) -> Dict:
    """
    Create a standardized JSON structure for workflow execution metadata.

    Args:
        workflow_execution_id: Unique identifier for the workflow execution
        workflow_execution: Type/name of the workflow execution
        metadata_keys_list: List of dictionaries containing file metadata

    Returns:
        Dictionary with structure:
        {
            "metadata": {
                "workflow_execution": str,
                "workflow_execution_id": str
            },
            "outputs": [
                {
                    "file": str,
                    "label": str,
                    "metadata": {
                        "file_format": str,
                        "data_object_id": str,
                        "was_informed_by": str
                    }
                },
                ...
            ]
        }
    """
    # contains list of dicts of metadata specific to each file
    outputs = []

    for metadata_keys in metadata_keys_list:
        # generates metadata specific to each file
        try:
            file = metadata_keys["file"]
            output = {
                "file": file,
                "label": metadata_keys["label"],
                "metadata": {
                    "data_object_id": metadata_keys["data_object_id"],
                    "was_informed_by": metadata_keys["was_informed_by"]
                }
            }
            outputs.append(output)
        except KeyError:
            logging.error(f"ERROR: key not found error: {file} \n stack trace: {traceback.format_exc()}")

    return {
        "metadata": {
            "workflow_execution": workflow_execution,
            "workflow_execution_id": workflow_execution_id

        },
        "outputs": outputs
    }


def _get_file_suffix():
    config_yaml = 'config.yaml'

    with open(config_yaml, 'r') as config_file:
        config_yaml_data = yaml.safe_load(config_file)
    config_json = json.loads(json.dumps(config_yaml_data, indent=4))

    data_object_type_suffix_dict = {}
    for data_object in config_json["Data Objects"]["Unique"]:
        data_object_type_suffix_dict[data_object['data_object_type']] = data_object['nmdc_suffix']

    return data_object_type_suffix_dict


def generate_metadata_file(workflow_execution_id: str, workflow_execution: str, records: List):
    """
    Generate and save metadata file for a specific workflow execution.

    Processes each record to extract relevant metadata and creates a structured JSON file.
    The output file is named 'metadata_{workflow_execution_id}.json'.

    Args:
        workflow_execution_id: Unique identifier for the workflow execution
        workflow_execution: Type/name of the workflow execution
        records: List of record dictionaries containing workflow output data
    """
    metadata_keys_list: List[Dict] = []
    data_object_type_suffix_dict = _get_file_suffix()

    for record in records:
        """Process a single record and extract relevant information."""
        metadata_keys: Dict = {}

        url = record["url"]
        metadata_keys["url"] = url
        prefix = "https://data.microbiomedata.org/data/"
        metadata_keys["was_informed_by"] = url.removeprefix(prefix).split('/')[0]

        file = record["name"] = url.split('/')[-1] # todo - replace with url **
        metadata_keys["file"] = file

        metadata_keys["data_object_id"] = record["id"]
        data_object_type = record["data_object_type"]

        # if file.endsWith(data_object_type_suffix_dict[data_object_type]): # check if the file suffix matches what is given in the config file
            # if file.endsWith(".gz") or file.endsWith(".zip"):
            #     metadata_keys["compression"] = file.split('.')[-1]
            # metadata_keys["file_format"] = file.split('.')[-1]
        # else:
        try:
            if file.endswith(data_object_type_suffix_dict[data_object_type]):
                logging.info("match found")
                with open('workflow_labels.json', 'r') as workflow_labels_file:
                    workflow_labels = json.load(workflow_labels_file)
                    # json structure: {"mags": {data_object_type1, label1},..}
                    try:
                        metadata_keys["label"] = workflow_labels[workflow_execution][data_object_type]
                    except KeyError:
                        logging.error(f"ERROR: key not found {url}, {workflow_execution}, {data_object_type}  \n Stack trace: {traceback.format_exc()}")
        except KeyError:
            logging.error(f"ERROR: mismatch between expected and actual file format or data_object_type {url} \n Stack trace: {traceback.format_exc()}")



        metadata_keys_list.append(metadata_keys)

    json_structure = create_json_structure(workflow_execution_id, workflow_execution, metadata_keys_list)
    save_json(json_structure, f"metadata_files/metadata_{workflow_execution_id}.json")


def process_data(valid_data: Dict[str, List]):
    """
    Process valid data and generate metadata files for each workflow type.

    Args:
        valid_data: Dictionary where:
            - key (str): workflow_execution_id
            - value (List): [workflow_execution_type (str), list_of_records (List[Dict])]
    """
    for workflow_execution_id, [workflow_execution, records] in valid_data.items():
        generate_metadata_file(workflow_execution_id, workflow_execution, records)


def main():
    """
    Main execution function that orchestrates the workflow:
    1. Retrieves workflow execution data from API
    2. Processes and validates the data
    3. Generates individual metadata files for each workflow execution
    """
    parser = argparse.ArgumentParser(description="Run specific methods based on flags")
    parser.add_argument("-clean", action="store_true", help="Start a clean run with a fresh pull of NMDC data from the runtime api")
    args = parser.parse_args()
    if args.clean:
        get_workflow_execution_set() # Produces valid_data.json

    with open('valid_data/valid_data.json', 'r') as valid_data_file:
        valid_data = json.load(valid_data_file)

    # Process valid data
    process_data(valid_data)  # Pass valid_data as argument

if __name__ == "__main__":
    main()

# todo import into jamo
# jat import template.yaml metadata.json

# todo logging
