import sys
import configparser

import pandas as pd
import requests
import os
import argparse
import logging

logging.basicConfig(
    filename="downloads.log",
    format="%(asctime)s.%(msecs)03d %(levelname)s {%(module)s} [%(funcName)s] %(message)s",
    datefmt="%Y-%m-%d,%H:%M:%S",
    level=logging.DEBUG,
)


def download_files(project, config_file, csv_file):
    # Download all files for a JAMO ID from the JGI Data Portal
    # purged_list = get_purged_jamo_ids(sample_files_list)
    # download_list = [f for f in sample_files_list if f['_id'] not in purged_list]
    JDP_TOKEN = os.environ.get("JDP_TOKEN")
    config = configparser.ConfigParser()
    config.read(config_file)
    base_dir = os.path.join(
        config["GLOBUS"]["dest_root_dir"], f"{project}_analysis_projects"
    )
    download_df = pd.read_csv(csv_file)
    for sample_dict in download_df.to_dict("records"):
        save_dir = os.path.join(base_dir, sample_dict["apGoldId"])
        os.mkdir(save_dir) if not os.path.exists(save_dir) else None
        download_sample_file(JDP_TOKEN, save_dir, sample_dict)


def download_sample_file(JDP_TOKEN, save_dir, files_dict):
    logging.debug(f"JDP_token {JDP_TOKEN}")
    save_file = os.path.join(save_dir, files_dict["file_name"])
    if not os.path.exists(save_file):
        logging.debug(f"filename {save_file}")
        headers = {"Authorization": f"{JDP_TOKEN}", "accept": "application/json"}
        url = f"https://files.jgi.doe.gov/download_files/{files_dict['jdp_file_id']}/"
        response = requests.get(url, headers=headers, stream=True)
        if response.status_code == 200:
            logging.debug(f"downloading {save_file}")
            with open(save_file, "wb") as fd:
                for chunk in response.iter_content(chunk_size=256):
                    fd.write(chunk)
        elif response.status_code == 409:
            logging.debug(f"response: {response.text}")
        else:
            logging.debug(f"response: {response.text}")
            sys.exit(response.text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("project_name")
    parser.add_argument("config_file")
    parser.add_argument(
        "sample_csv_file", help="save list of staged files to output file"
    )
    args = vars((parser.parse_args()))
    download_files(args["project_name"], args["config_file"], args["sample_csv_file"])
