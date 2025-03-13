"""
DB Tools.
"""
import logging
import json
import os

import click

from nmdc_automation.config import SiteConfig
from nmdc_automation.api import NmdcRuntimeApi

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    pass


@cli.command()
@click.argument("config_file", type=click.Path(exists=True))
@click.option("--update-db", is_flag=True, help="Update the database")
def update_zero_size_files(config_file, update_db):

    # logger.info(f"Updating zero size files from {config_file}")

    site_config = SiteConfig(config_file)
    username = site_config.username
    password = site_config.password


    import requests
    headers = {'accept': 'application/json', 'Authorization': f'Basic {username}:{password}'}

    params = {
        'filter': '{"$or": [{"file_size_bytes": {"$exists": false}},{"file_size_bytes": null},{"file_size_bytes": 0}],"$and": [{"url": {"$exists": true}},{"url": {"$regex": "^https://data.microbiomedata.org/data/"}}]}',
        'max_page_size': '10000', }

    response = requests.get(
        'https://api-dev.microbiomedata.org/nmdcschema/data_object_set', params=params, headers=headers
    )
    if response.status_code != 200:
        logger.error(f"Error in response: {response.status_code}")
        return
    data_objects = response.json().get("resources", [])

    logger.info(f"Found {len(data_objects)} data objects with zero size data files")


    update_query = {
        "update": "data_object_set",
        "updates": [],
    }
    num_zero_size_files = 0
    num_files_not_found = 0
    num_with_file_size = 0
    for dobj in data_objects:
        # get everything after 'data/' in the url
        file_path = dobj['url'].split('data/')[1]
        file_path = os.path.join(site_config.data_dir, file_path)

        logger.info(f"Updating {dobj['id']} /  File size: {dobj.get('file_size_bytes', None)} / File: {file_path}")
        # try to get the file size in bytes
        try:
            file_size = os.path.getsize(file_path)
            logger.info(f"File size: {file_size}")

            # There are zero size files on the file system - log a warning and continue
            if file_size == 0:
                logger.warning(f"Zero size file: {file_path}")
                num_zero_size_files += 1
                continue

            num_with_file_size += 1
            update = {
                "q": {"id": dobj['id']},
                "u": {"$set": {"file_size_bytes": file_size}},
            }
            update_query["updates"].append(update)
        except FileNotFoundError:
            logger.warning(f"File not found: {file_path}")
            num_files_not_found += 1
            continue

    logger.info(f"Number of zero size files: {num_zero_size_files}")
    logger.info(f"Number of files not found: {num_files_not_found}")
    logger.info(f"Number of files with file size: {num_with_file_size}")


    if update_db:
        response = requests.post(
            'https://api-dev.microbiomedata.org/queries:run', json=update_query, headers=headers
        )
        if response.status_code != 200:
            logger.error(f"Error in response: {response.status_code}")
            return
        logger.info("Successfully updated the database")
    else:
        logger.info("Dry run. Database not updated")
        print(json.dumps(update_query, indent=2))



@cli.command()
@click.argument("config_file", type=click.Path(exists=True))
@click.option("--update-db", is_flag=True, help="Update the database")
def fix_data_object_urls(config_file, update_db):

    site_config = SiteConfig(config_file)
    username = site_config.username
    password = site_config.password

    runtime_api = NmdcRuntimeApi(site_config)

    import requests
    headers = {'accept': 'application/json', 'Authorization': f'Basic {username}:{password}'}

    params = {
        'filter': '{"url": {"$regex": "/ficus/"}}',
        'max_page_size': '1000', }

    response = requests.get(
        'https://api-dev.microbiomedata.org/nmdcschema/data_object_set', params=params, headers=headers
    )
    if response.status_code != 200:
        logger.error(f"Error in response: {response.status_code}")
        return
    data_objects = response.json().get("resources", [])

    logger.info(f"Found {len(data_objects)} data objects with incorrect urls")

    data_object_set = []


    for dobj in data_objects:

        logger.info(f"Updating {dobj['id']} {dobj['data_object_type']}")
        # Raw reads don't get a URL
        if dobj['data_object_type'] == 'Metagenome Raw Reads':
            # delete the url
            dobj.delete('url')
            data_object_set.append(dobj)
            continue

        # splitting on / and taking the last 3 elements
        url_parts = dobj['url'].split('/')[-3:]
        new_url = f"https://data.microbiomedata.org/data/{url_parts[0]}/{url_parts[1]}/{url_parts[2]}"
        # logger.info(f"New URL: {new_url}")
        dobj['url'] = new_url
        data_object_set.append(dobj)

    data_objects_update = {"data_object_set": data_object_set}
    data_objects_json = json.dumps(data_objects_update, indent=2)
    print(data_objects_json)

    # check that the json is valid
    logger.info("Validating metadata")
    val_result = runtime_api.validate_metadata(data_objects_update)
    if val_result['result'] == "All Okay!":
        logger.info("Metadata is valid")
    else:
        logger.error("Metadata is not valid")
        logger.error(val_result)
        return






if __name__ == "__main__":
    cli()
