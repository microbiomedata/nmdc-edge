import json
import requests
import click
from typing import Dict, List, Optional



_BASE_URL = "https://api.microbiomedata.org/"

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


def create_json_structure(workflow_execution: str, metadata_keys: Dict) -> Dict:
    """Create the JSON structure for all records of type workflow_execution."""
    outputs = []
    for item in metadata_keys_list:
    	output = {}
    	output["file"] = metadata_keys["file"],
        output["label"] = metadata_keys["label"],
        output["metadata"] = 
        		{
                    "file_format": metadata_keys["file_format"]
                    "workflow_execution_id": metadata_keys["workflow_execution_id"],
		            "data_object_id": metadata_keys["data_object_id"],
		            "was_informed_by": metadata_keys["was_informed_by"]
                }
        outputs.append(output)
    
    return {
        "metadata": {
            "workflow_execution": metadata_keys["workflow_execution"],
            
        },
        "outputs": outputs
        }



# File Operations
def save_json(data: Dict, filename: str):
    """Save data to JSON file."""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

def load_json(filename: str) -> Dict:
    """Load data from JSON file."""
    with open(filename) as f:
        return json.load(f)


def generate_metadata_file(workflow_type: str, records: List):
	metadata_keys_list: List[Dict] = []
	metadata_keys: Dict = {}
	for record in records:
		"""Process a single record and extract relevant information."""
	    metadata_keys["url"] = record["url"]
	    metadata_keys["file"] = record["name"]
	    metadata_keys["data_object_id"] = record["id"]
	    metadata_keys["label"] = record["data_object_type"]

	    prefix = "https://data.microbiomedata.org/data/"
	    url_suffix = url.removeprefix(prefix)
	    tokens = url_suffix.split('/')

	    metadata_keys["was_informed_by"] = tokens[0]
	    metadata_keys["workflow_execution_id"] = tokens[1]
	    metadata_keys["workflow_execution"] = workflow_execution_id.split('-')[0].removeprefix('nmdc:')
	    metadata_keys["file_format"] = file.split('.')[-1]

	    metadata_keys_list.append(metadata_keys)


	 save_json(create_json_structure(workflow_type, metadata_keys_list), f"metadata_{workflow_type}".json)


def process_records():
	valid_data = json.load("valid_data.json")

	for workflow in valid_data:
		generate_metadata(workflow, valid_data.get(workflow))


# CLI Commands
@click.command()
@click.option('--base-api-url', default=_base_url, help='The base URL for the API to query.')
@click.option('--max-page-size', default=100000, help='Maximum number of records to query per page.', show_default=True)
def get_workflow_execution_set(base_api_url: str, max_page_size: int) -> Dict[str, List[str]]:
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
    try:
        # Get workflow records
        workflow_records = query_collection(base_api_url, "workflow_execution_set", max_page_size)
        click.echo(f"Workflow Executions Set: {len(workflow_records.get('resources', []))} records retrieved.")

        # Get data object set
        data_object_set = get_data_object_set(base_api_url, max_page_size)
        click.echo(f"Data Object Set: {len(data_object_set)} records retrieved.")

        # Process workflows
        workflow_output_dict = {}
        for record in workflow_records.get("resources", []):
            has_output_list = record.get("has_output", [])
            workflow = record.get("type")
	        valid_records = []
	        for output_id in has_output_list:
	        	# Cross-reference workflow outputs against data_object_set to filter out invalid/missing records
	            output_record = data_object_set.get(output_id)
	            if output_record:
	            	valid_records.append(output_record)
	        if valid_records:
	            workflow_output_dict[workflow] = valid_records

	     # Save results
        save_json(workflow_output_dict, "valid_data.json")

    except requests.RequestException as e:
        click.echo(f"API request failed: {e}", err=True)
    except Exception as e:
        click.echo(f"An error occurred: {e}", err=True)


def main():
    """Main function to run the workflow."""
    try:
        get_workflow_execution_set()
        
        # Process valid data
        valid_data = load_json("valid_data.json")
        processed_data = process_record(valid_data)
        save_json(processed_data, "metadata.json")
        
    except Exception as e:
        click.echo(f"Error in main execution: {e}", err=True)

if __name__ == "__main__":
    main()


# todo import into jamo
# jat import template.yaml metadata.json

# todo logging
