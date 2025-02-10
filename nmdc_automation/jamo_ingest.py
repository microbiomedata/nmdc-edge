import json


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
