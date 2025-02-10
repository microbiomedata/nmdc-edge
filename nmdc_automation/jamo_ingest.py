valid_data.json = "/path/to/valid_data.json"

for record in valid_records.json
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
