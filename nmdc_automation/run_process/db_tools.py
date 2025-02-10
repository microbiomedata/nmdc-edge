"""
DB Tools.
"""
import logging
import json
import os

import click

from nmdc_automation.config import SiteConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    pass


@cli.command()
@click.argument("config_file", type=click.Path(exists=True))
@click.option("--update-db", default=False, type=bool, help="Update the database")
def update_zero_size_files(config_file, update_db):
    logger.info(f"Updating zero size files from {config_file}")

    site_config = SiteConfig(config_file)
    client_id = site_config.client_id
    client_secret = site_config.client_secret


    import requests
    headers = {'accept': 'application/json', 'Authorization': f'Bearer {client_id} {client_secret}'}

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
                continue

            update = {
                "q": {"id": dobj['id']},
                "u": {"$set": {"file_size_bytes": file_size}},
            }
            update_query["updates"].append(update)
        except FileNotFoundError:
            logger.warning(f"File not found: {file_path}")
            continue

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


if __name__ == "__main__":
    cli()
