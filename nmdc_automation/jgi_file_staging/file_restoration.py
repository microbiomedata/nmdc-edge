import configparser
import sys

import pandas as pd
import requests
import os
import logging
from datetime import datetime
from nmdc_automation.db.nmdc_mongo import get_db
from nmdc_automation.jgi_file_staging.models import Sample
from pydantic import ValidationError
import argparse
import json


logging.basicConfig(filename='file_staging.log',
                    format='%(asctime)s.%(msecs)03d %(levelname)s {%(module)s} [%(funcName)s] %(message)s',
                    datefmt='%Y-%m-%d,%H:%M:%S', level=logging.DEBUG)


def update_sample_in_mongodb(sample: dict, update_dict: dict, mdb) -> bool:
    update_dict.update({'update_date': datetime.now()})
    sample.update(update_dict)
    try:
        sample_update = Sample(**sample)
        sample_update_dict = sample_update.dict()
        mdb.samples.update_one({'jdp_file_id': sample_update_dict['jdp_file_id']}, {'$set': update_dict})
        return True
    except ValidationError as e:
        logging.debug(f'Update error: {e}')
        return False


def restore_files(project: str, config_file: str, mdb, restore_csv=None) -> str:
    """
    Restore files from tape backup at JGI.

    1. Update file statuses
    2. Submit restore requests for files that are not in transit, transferred, or restored
    Limitations: max restore request size is 10TB/day, and max number of files is 750

    :param project: Name of project (e.g., 'grow', 'bioscales').
    :param config_file: Path to config file.
    :param mdb: MongoDB connection.
    :param restore_csv: Optional CSV file with files to restore.
    :return: Status message.
    """
    # Read config file
    config = configparser.ConfigParser()
    config.read(config_file)

    # Update statuses first
    # update_file_statuses(project, mdb, config_file)

    # Load restore DataFrame
    if restore_csv:
        restore_df = pd.read_csv(restore_csv)
    else:
        samples = list(
            mdb.samples.find(
                {
                    'project_name': project,
                    'file_status': {'$nin': ['in transit', 'transferred', 'RESTORED']}
                }
            )
        )
        if not samples:
            return 'No samples to restore'
        restore_df = pd.DataFrame(samples)


    JDP_TOKEN = os.environ.get('JDP_TOKEN')
    if not JDP_TOKEN:
        sys.exit('JDP_TOKEN environment variable not set')
    headers = {'Authorization': JDP_TOKEN, "accept": "application/json"}
    url = 'https://files.jgi.doe.gov/download_files/'

    try:
        proxies = json.loads(config['JDP'].get('proxies', '{}'))
    except json.JSONDecodeError:
        logging.error("Failed to parse proxies from config file.")
        proxies = {}

    begin_idx = restore_df.iloc[0, :].name
    # break requests up into batches because of the limit to the size of the request
    batch_size = 750
    count = 0
    # total size of files requested for restoration must be less than 10TB per day, set in config file
    sum_files = 0
    while begin_idx < len(restore_df):
        end_idx = begin_idx + batch_size
        sum_files += restore_df.loc[begin_idx:end_idx, 'file_size'].sum()
        if sum_files > float(config['JDP']['max_restore_request']):
            break
        request_ids = list(restore_df.loc[begin_idx:end_idx, 'jdp_file_id'].values)
        if request_ids:
            data = {'ids': request_ids, "restore_related_ap_data": 'false', "api_version": "2",
                    "globus_user_name": config['GLOBUS']['globus_user_name'],
                    "href": f"mailto: {config['GLOBUS']['mailto']}", "send_mail": "true"}

            r = requests.post(url, headers=headers, json=data, proxies=proxies)
            if r.status_code != 200:
                logging.debug(count)
                logging.debug(r.text)
                return r.text
            request_json = r.json()
            count += len(request_ids)
            restore_df.loc[begin_idx:end_idx, 'request_id'] = request_json['request_id']
            restore_df.loc[begin_idx:end_idx, 'file_status'] = 'pending'
            logging.debug(f"{begin_idx, end_idx, restore_df.loc[begin_idx:end_idx, 'file_size'].sum(), sum_files}")
        begin_idx = end_idx
    restore_df.apply(lambda x: update_sample_in_mongodb(x, {'request_id': x['request_id'],
                                                            'file_status': x['file_status']}, mdb), axis=1)

    return f"requested restoration of {count} files"


def get_file_statuses(samples_df, config):
    jdp_response_df = pd.DataFrame()
    for request_id in samples_df[pd.notna(samples_df.request_id)].request_id.unique():
        JDP_TOKEN = os.environ.get('JDP_TOKEN')
        headers = {'Authorization': JDP_TOKEN, "accept": "application/json"}
        url = f"https://files.jgi.doe.gov/request_archived_files/requests/{request_id}?api_version=1"

        proxies = json.loads(config['JDP'].get('proxies', '{}'))
        r = requests.get(url, headers=headers, proxies=proxies)
        response_json = r.json()
        file_status_list = [response_json['status'] for _ in response_json['file_ids']]
        jdp_response_df = pd.concat([jdp_response_df, pd.DataFrame({'jdp_file_id': response_json['file_ids'],
                                                                    'file_status': file_status_list})])
        logging.debug(jdp_response_df.jdp_file_id.unique())
        logging.debug(jdp_response_df[pd.isna(jdp_response_df['jdp_file_id'])])
    restore_response_df = pd.merge(samples_df, jdp_response_df, left_on='jdp_file_id', right_on='jdp_file_id')
    return restore_response_df


def update_file_statuses(project: str, mdb, config_file: str=None, config: configparser.ConfigParser=None):
    if config is None:
        config = configparser.ConfigParser()
        config.read(config_file)

    samples_cursor = mdb.samples.find({'project_name': project})
    samples_list = list(samples_cursor)
    if not samples_list:
        logging.debug(f"no samples to update for {project}")
        return
    samples_df = pd.DataFrame(samples_list)

    if 'request_id' not in samples_df.columns:
        logging.debug(f"no samples with request_id to update for {project}")
        return

    # get file statuses from JGI Data Portal
    try:
        restore_response_df = get_file_statuses(samples_df, config)
    except Exception as e:
        logging.error(f"Error getting file statuses: {e}")
        return

    if 'file_status_x' not in restore_response_df.columns or 'file_status_y' not in restore_response_df.columns:
        logging.debug(f"no file statuses to update for {project}")
        return

    changed_rows = restore_response_df.loc[
        restore_response_df.file_status_x != restore_response_df.file_status_y, :]
    if changed_rows.empty:
        logging.debug(f"no file statuses changed for {project}")
        return
    logging.debug(f"updating {len(changed_rows)} file statuses for {project}")

    # update file statuses in MongoDB
    for idx, row in changed_rows.iterrows():
        sample = row[row.keys().drop(['file_status_x', 'file_status_y'])].to_dict()
        try:
            update_sample_in_mongodb(sample, {'jdp_file_id': row.jdp_file_id, 'file_status': row.file_status_y}, mdb)
        except Exception as e:
            logging.error(f"Error updating sample {sample['jdp_file_id']}: {e}")
            continue


def check_restore_status(restore_request_id, config):
    """
    Status of a restore request made to the JGI Data Portal restore API
    :param restore_request_id: ID of request returned by restore_files
    :param config: ConfigParser instance
    :return:
    """
    JDP_TOKEN = os.environ.get('JDP_TOKEN')
    headers = {'Authorization': JDP_TOKEN, "accept": "application/json"}

    url = f"https://files.jgi.doe.gov/request_archived_files/requests/{restore_request_id}?api_version=1"
    proxies = json.loads(config['JDP'].get('proxies', '{}'))
    r = requests.get(url, headers=headers, proxies=proxies)
    if r.status_code == 200:
        return r.json()
    else:
        logging.exception(r.text)
        return None


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('project_name')
    parser.add_argument('config_file')
    parser.add_argument('-u', '--update_file_statuses', action='store_true', help='update status of file restorations',
                        default=False)
    parser.add_argument('-r', '--restore_csv', default=None,  help='csv with files to restore')
    args = vars((parser.parse_args()))

    mdb = get_db()

    if args['update_file_statuses']:
        update_file_statuses(args['project_name'], mdb, config_file=args['config_file'])
    else:
        restore_files(args['project_name'], args['config_file'], mdb, args['restore_csv'])
