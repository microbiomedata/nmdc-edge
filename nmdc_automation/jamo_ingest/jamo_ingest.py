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


# Data Processing Functions
def process_record(record: Dict) -> Dict:
    """Process a single record and extract relevant information."""
    url = record["url"]
    file = record["name"]
    data_object_id = record["id"]
    label = record["data_object_type"]

    prefix = "https://data.microbiomedata.org/data/"
    url_suffix = url.removeprefix(prefix)
    tokens = url_suffix.split('/')

    was_informed_by = tokens[0]
    workflow_execution_id = tokens[1]
    workflow_execution = workflow_execution_id.split('-')[0].removeprefix('nmdc:')
    file_format = file.split('.')[-1]

    return create_json_structure(
        workflow_execution, workflow_execution_id, data_object_id,
        was_informed_by, file, label, file_format
    )



def create_json_structure(workflow_execution: str, workflow_execution_id: str,
                         data_object_id: str, was_informed_by: str,
                         file: str, label: str, file_format: str) -> Dict:
    """Create the JSON structure for a record."""
    return {
        "metadata": {
            "workflow_execution": workflow_execution,
            "workflow_execution_id": workflow_execution_id,
            "data_object_id": data_object_id,
            "was_informed_by": was_informed_by
        },
        "outputs": [
            {
                "file": file,
                "label": label,
                "metadata": {
                    "file_format": file_format
                }
            }
        ]
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


# CLI Commands
@click.command()
@click.option('--base-api-url', default=_base_url, help='The base URL for the API to query.')
@click.option('--max-page-size', default=100000, help='Maximum number of records to query per page.', show_default=True)
def get_workflow_execution_set(base_api_url: str, max_page_size: int):
    """
    Retrieve and print all records from the workflow_execution_set collection.
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
	        	# cross-reference workflow_execution_set records against data_object_set collection to ensure they are not invalid
	            output_record = data_object_set.get(output_id)
	            if output_record:
	            	valid_records.append(output_record)
	        if valid_records:
	            workflow_output_dict[workflow] = valid_records

	     # Save results
        save_json(workflow_output_dict, "workflow_outputs.json")

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
