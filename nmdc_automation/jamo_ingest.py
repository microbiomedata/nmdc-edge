import json

valid_data = "valid_data.json"

with open("valid_data.json") as f:
	valid_data = json.load(f)

	for record in valid_data:
		url = record['url']
	    file = record['name']
	    data_object_id = record['id']
	    label = record['data_object_type']

	    prefix = "https://data.microbiomedata.org/data/"
	    url_suffix = url.removeprefix(prefix)
	    tokens = url_suffix.split('/')
	    
	    was_informed_by = tokens[0]
	    workflow_execution_id = tokens[1]
	    workflow_execution = workflow_execution_id.split('-')[0].removeprefix('nmdc_')
	    file_format = file.split('.')[-1]


	# create json structure

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

	with open('metadata.json', w) as f:
		json.dump(json_data, f, indent=4)
