import json
import requests
import click



_base_url = "https://api.microbiomedata.org/"

def query_collection(base_url, collection_name, max_page_size=None, filter_param=None):
    """
    Query the metadata from a specific collection.

    :param base_url: The base URL of the API
    :param collection_name: The name of the collection to query
    :param max_page_size: Maximum number of records to query per page (optional)
    :return: The response from the API call
    """
    url = f"{base_url}nmdcschema/{collection_name}"
    if max_page_size:
        url += f"?max_page_size={max_page_size}"
    if filter_param:
        url += f"&filter={filter_param}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

def get_data_object_set(base_api_url, max_page_size):
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

@click.command()
@click.option('--base-api-url', default=_base_url, help='The base URL for the API to query.')
@click.option('--max-page-size', default=100000, help='Maximum number of records to query per page.', show_default=True)
def get_workflow_execution_set(base_api_url, max_page_size):
    """
    Retrieve and print all records from the workflow_execution_set collection.
    """
    # TODO: support pagination if records exceed max_page_size
    workflow_records = query_collection(base_api_url, "workflow_execution_set", max_page_size)
    click.echo(f"Workflow Executions Set: {len(workflow_records.get('resources', []))} records retrieved.")

    data_object_set = get_data_object_set(base_api_url, max_page_size)
    click.echo(f"Data Object Set: {len(data_object_set)} records retrieved.")

    workflow_output_dict = {}

    for record in workflow_records.get("resources", []):
        has_output_list = record.get("has_output", [])
        workflow = record.get("type")
        valid_records = []
        for output_id in has_output_list:
            output_record = data_object_set.get(output_id)
            if output_record:
            	valid_records.append(output_record)
                # click.echo(output_record)
        workflow_output_dict[workflow] = valid_records


if __name__ == "__main__":
    get_workflow_execution_set()
    with open("valid_data.json") as valid_data_file:
	# todo validate json
	valid_data = json.load(valid_data_file)

	# todo iterate over multiple records, and group them using workflow_execution
	url = valid_data["url"]
	file = valid_data["name"]
	data_object_id = valid_data["id"]
	label = valid_data["data_object_type"]

	prefix = "https://data.microbiomedata.org/data/"
	url_suffix = url.removeprefix(prefix)
	tokens = url_suffix.split('/')

	was_informed_by = tokens[0]
	workflow_execution_id = tokens[1]
	workflow_execution = workflow_execution_id.split('-')[0].removeprefix('nmdc:')
	file_format = file.split('.')[-1]


	# create json structure

	# todo error handling

	json_data = {
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

	with open('metadata.json', 'w') as metadata_file:
		json.dump(json_data, metadata_file, indent=4)


# todo import into jamo
# jat import template.yaml metadata.json

# todo logging
