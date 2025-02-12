import json
import requests
import click
from typing import Dict, List, Optional

_BASE_URL = "https://api.microbiomedata.org/"


# File Operations
def save_json(data: Dict, filename: str):
    """Save data to JSON file."""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)


def load_json(filename: str) -> Dict:
    """Load data from JSON file."""
    with open(filename) as f:
        return json.load(f)


# API Query Functions
def query_collection(base_url: str, collection_name: str,
                     max_page_size: Optional[int] = None,
                     filter_param: Optional[str] = None) -> Dict:
    """
	Query the metadata from a specific collection.

	:param base_url: The base URL of the API
	:param collection_name: The name of the collection to query
	:param max_page_size: Maximum number of records to query per page (optional)
	:return: The response from the API call
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
	Retrieve and print all URLs from the data_object_set collection with a filter.
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
		base_api_url (str): Base URL for the API endpoint
		max_page_size (int): Maximum number of records to retrieve per query

	Returns:
		Dict[str, List[dict]]: Dictionary where:
			- keys are workflow types (str)
			- values are lists of validated output records (dict)
	"""
    # TODO: support pagination if records exceed max_page_size
    # try:
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
        workflow_execution = record.get("type")
        workflow_execution_id = record.get("id")
        valid_records = []
        for output_id in has_output_list:
            # Cross-reference workflow outputs against data_object_set to filter out invalid/missing records
            output_record = data_object_set.get(output_id)
            if output_record:
                valid_records.append(output_record)
        workflow_outputs_dict[workflow_execution_id] = [workflow_execution, valid_records]

    # Save results
    try:
        save_json(workflow_outputs_dict, "valid_data.json")
    except (IOError, OSError) as e:
        print(f"error {e}", err=True)

    return workflow_outputs_dict


def create_json_structure(workflow_execution_id: str, workflow_execution: str, metadata_keys_list: List[Dict]) -> Dict:
    """Create the JSON structure for all records of type workflow_execution."""
    # contains list of dicts of metadata specific to each file
    outputs = []
    for metadata_keys in metadata_keys_list:
        # generates metadata specific to each file
        output = {
            "file": metadata_keys["file"],
            "label": metadata_keys["label"],
            "metadata": {
                "file_format": metadata_keys["file_format"],
                "data_object_id": metadata_keys["data_object_id"],
                "was_informed_by": metadata_keys["was_informed_by"]
            }
        }
        outputs.append(output)

    return {
        "metadata": {
            "workflow_execution": workflow_execution,
            "workflow_execution_id": workflow_execution_id

        },
        "outputs": outputs
    }


def generate_metadata_file(workflow_execution_id: str, workflow_execution: str, records: List):
    metadata_keys_list: List[Dict] = []

    for record in records:
        """Process a single record and extract relevant information."""
        metadata_keys: Dict = {}

        url = record["url"]
        metadata_keys["url"] = url
        prefix = "https://data.microbiomedata.org/data/"
        metadata_keys["was_informed_by"] = url.removeprefix(prefix).split('/')[0]

        file = record["name"]
        metadata_keys["file"] = file
        metadata_keys["file_format"] = file.split('.')[-1]

        metadata_keys["data_object_id"] = record["id"]
        metadata_keys["label"] = record["data_object_type"]

        metadata_keys_list.append(metadata_keys)

    json_structure = create_json_structure(workflow_execution_id, workflow_execution, metadata_keys_list)
    save_json(json_structure, f"metadata_{workflow_execution_id}.json")


def process_data(valid_data: Dict[str, List]):
    """Process valid data and generate metadata files for each workflow type."""
    """input is valid_data is of type json: key is workflow_execution_id (str), and value is list[workflow_execution (str), workflow output records (list)   
    valid_data: Dict[str, List[str, List[Dict]]] 
    """
    for workflow_execution_id, [workflow_execution, records] in valid_data.items():
        generate_metadata_file(workflow_execution_id, workflow_execution, records)


def main():
    """Main function to run the workflow."""
    # Produces valid_data.json
    valid_data = get_workflow_execution_set()

    # Process valid data
    # valid_data = load_json("valid_data.json")
    process_data(valid_data)  # Pass valid_data as argument

if __name__ == "__main__":
    main()

# todo import into jamo
# jat import template.yaml metadata.json

# todo logging
