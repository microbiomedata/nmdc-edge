import configparser
import sys

import pandas as pd
import requests
import os
import logging
from datetime import datetime
import time

import click
from mongo import get_mongo_db
from models import Sample
from typing import List
from pydantic import ValidationError
import subprocess

logging.basicConfig(filename='file_staging.log',
                    format='%(asctime)s.%(msecs)03d %(levelname)s {%(module)s} [%(funcName)s] %(message)s',
                    datefmt='%Y-%m-%d,%H:%M:%S', level=logging.DEBUG)


@click.group()
def cli():
    pass


@cli.command()
@click.argument('samples_csv_file', type=click.Path(dir_okay=True, resolve_path=True))
@click.argument('project')
@click.argument('proposal_id')
def get_samples_data(samples_csv_file: str, proposal_id: int, project: str) -> None:
    # check_restore_status()
    ACCESS_TOKEN = get_access_token()
    all_files_list = get_sample_files(samples_csv_file, ACCESS_TOKEN)
    gold_analysis_data = get_analysis_projects_from_proposal_id(proposal_id, ACCESS_TOKEN)
    files_df = pd.DataFrame(all_files_list)
    gold_analysis_data_df = pd.DataFrame(gold_analysis_data)
    gold_analysis_files_df = pd.merge(gold_analysis_data_df, files_df, left_on='itsApId',
                                      right_on='analysis_project_id')
    gold_analysis_files_df['project'] = project
    insert_samples_into_mongodb(gold_analysis_files_df.to_dict('records'))


def get_access_token() -> str:
    OFFLINE_TOKEN = os.environ.get('OFFLINE_TOKEN')
    url = f'https://gold-ws.jgi.doe.gov/exchange?offlineToken={OFFLINE_TOKEN}'
    response = requests.get(url)
    sys.exit(f"get_access_token: {response.text}") if response.status_code != 200 else None

    return response.text


def get_sample_files(samples_csv_file: str, ACCESS_TOKEN: str) -> List[dict]:
    """
    Get all sample files for a project
    :param samples_csv_file: csv file with biosample id's
    :param ACCESS_TOKEN: gold api token
    :return: list of sample files for each biosample
    """

    samples_df = pd.read_csv(samples_csv_file)
    all_files_list = []
    for idx, biosample_id in samples_df.itertuples():
        logging.debug(f"biosample {biosample_id}")
        ACCESS_TOKEN = check_access_token(ACCESS_TOKEN)
        try:
            seq_id = get_sequence_id(biosample_id, ACCESS_TOKEN)
            sample_files_list, agg_id_list = get_sample_files_list(seq_id, ACCESS_TOKEN)
        except IndexError as e:
            logging.exception(f'skipping biosample_id: {biosample_id}')
            continue
        combine_sample_ids_with_agg_ids(sample_files_list, agg_id_list, biosample_id, seq_id, all_files_list)
    return all_files_list


def get_sequence_id(gold_id: str, ACCESS_TOKEN: str):
    # given a gold biosample id, get the JGI sequencing ID
    gold_biosample_url = f'https://gold-ws.jgi.doe.gov/api/v1/projects?biosampleGoldId={gold_id}'
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "accept": "application/json", 'User-agent': 'nmdc bot 0.1'}
    time.sleep(0.5)
    gold_biosample_response = requests.get(gold_biosample_url, headers=headers)
    if gold_biosample_response.status_code == 200:
        gold_biosample_data = gold_biosample_response.json()[0]
        return gold_biosample_data['itsSpid']
    else:
        logging.debug(f"gold_biosample_response: {gold_biosample_response.text}")
        return None


def get_analysis_projects_from_proposal_id(proposal_id: int, ACCESS_TOKEN: str) -> List[dict]:
    gold_analysis_url = f'https://gold-ws.jgi.doe.gov/api/v1/analysis_projects?itsProposalId={proposal_id}'
    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}', "accept": "application/json"}
    gold_analysis_response = requests.get(gold_analysis_url, headers=headers)
    gold_analysis_data = gold_analysis_response.json()
    return gold_analysis_data


def check_access_token(ACCESS_TOKEN: str) -> str:
    gold_biosample_url = f'https://gold-ws.jgi.doe.gov/api/v1/projects?biosampleGoldId=Gb0291582'
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "accept": "application/json", 'User-agent': 'nmdc bot 0.1'}
    time.sleep(0.5)
    gold_biosample_response = requests.get(gold_biosample_url, headers=headers)
    if gold_biosample_response.status_code == 200:
        return ACCESS_TOKEN
    else:
        return get_access_token()


def insert_samples_into_mongodb(sample_list: list) -> None:
    """ create workflows from list of samples to process"""
    mdb = get_mongo_db()
    try:
        db_records_list = []
        for d in sample_list:
            db_records_list.append({key: value for (key, value) in d.items() if key in
                                    list(Sample.__fields__.keys())})
        sample_objects = [Sample(**sample).dict() for sample in sample_list]
        mdb.samples.insert_many(sample_objects)
    except ValidationError:
        logging.exception(f'ValidationError {sample_list[0]["biosample_id"]}')
        return None


def update_sample_in_mongodb(sample: dict, update_dict: dict) -> bool:
    mdb = get_mongo_db()
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


def combine_sample_ids_with_agg_ids(sample_files_list, agg_id_list, biosample_id, seq_id, all_files_list) -> None:
    for sample, agg_id in zip(sample_files_list, agg_id_list):
        for files_dict in sample:
            all_files_list.append({'biosample_id': biosample_id, 'seq_id': seq_id, 'file_name': files_dict['file_name'],
                                   'file_status': files_dict['file_status'], 'file_size': files_dict['file_size'],
                                   'jdp_file_id': files_dict['_id'], 'md5sum': files_dict['md5sum'],
                                   'analysis_project_id': agg_id})
            if 'metadata' not in files_dict.keys():
                print(f"biosample_id {biosample_id}, seq_id{seq_id}")


def get_sample_files_list(sequencing_id, ACCESS_TOKEN) -> (List[dict], List[str]):
    # Given a JGI sequencing ID, get the list of files associated with the biosample
    logging.debug(f"sequencing_id {sequencing_id}")
    seqid_url = f"https://files.jgi.doe.gov/search/?q={sequencing_id}&a=false&h=false&d=asc&p=1&x=10&api_version=2"
    headers = {'X-CSRFToken': f'Token {ACCESS_TOKEN}', "accept": "application/json"}
    seqid_response = requests.get(seqid_url, headers=headers)
    sys.exit(f"{seqid_response.text}") if seqid_response.status_code != 200 else None
    files_data = seqid_response.json()
    files_data_list = []
    agg_id_list = []
    if 'organisms' in files_data.keys():
        for org in files_data['organisms']:
            files_data_list.append(org['files'])
            agg_id_list.append(org['agg_id'])
        return files_data_list, agg_id_list
    else:
        return None, []


@cli.command()
@click.argument('config_file', type=click.Path(dir_okay=True, resolve_path=True))
@click.argument('project')
def restore_files(project: str, config_file: str) -> str:
    """
    restore files from tape backup on JGI
    1) update file statuses
    2) for any files that are still PURGED, submit request to restore from tape
    There is a limit of 10TB/day for restore requests
    :param project: name of project (i.e. grow or bioscales)
    :param config_file: config file
    :return:
    """
    config = configparser.ConfigParser()
    config.read(config_file)
    update_file_statuses(project, config)
    mdb = get_mongo_db()
    restore_df = pd.DataFrame([sample for sample in mdb.samples.find({'file_status': 'PURGED', 'project': project})])
    JDP_TOKEN = os.environ.get('JDP_TOKEN')
    headers = {'Authorization': JDP_TOKEN, "accept": "application/json"}
    url = f'https://files.jgi.doe.gov/download_files/'
    proxies = eval(config['JDP']['proxies'])
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
            logging.debug(begin_idx, end_idx, restore_df.loc[begin_idx:end_idx, 'file_size'].sum(), sum_files)
        begin_idx = end_idx
    restore_df.apply(lambda x: update_sample_in_mongodb(x, {'request_id': x['request_id'],
                                                            'file_status': x['file_status']}), axis=1)

    return f"requested restoration of {count} files"


def update_file_statuses(project, config):
    mdb = get_mongo_db()

    restore_df = pd.DataFrame([sample for sample in mdb.samples.find({'file_status': 'pending', 'project': project})])
    for request_id in restore_df.request_id.unique():
        response = check_restore_status(request_id, config)
        for jdp_file_id in response['file_ids']:
            update_sample_in_mongodb(restore_df.loc[restore_df.jdp_file_id == jdp_file_id, :].to_dict('records')[0],
                                     {'jdp_file_id': jdp_file_id, 'file_status': response['status']})


def check_restore_status(restore_request_id, config):
    """
    Status of a restore request made to the JGI Data Portal restore API
    :param restore_request_id: ID of request returned by restore_files
    :param JDP_TOKEN: Token from JDP website
    :return:
    """
    JDP_TOKEN = os.environ.get('JDP_TOKEN')
    headers = {'Authorization': JDP_TOKEN, "accept": "application/json"}

    url = f"https://files.jgi.doe.gov/request_archived_files/requests/{restore_request_id}?api_version=1"
    r = requests.get(url, headers=headers, proxies=eval(config['JDP']['proxies']))
    if r.status_code == 200:
        return r.json()
    else:
        logging.exception(r.text)
        return None


def get_globus_manifests(config_file):
    """
    This gets the Globus file manifests with the list of Globus paths for each requested file
    This function requires installation of the Globus CLI
    :return:
    """
    config = configparser.ConfigParser()
    config.read(config_file)
    jgi_globus_id = config['GLOBUS']['jgi_globus_id']
    nersc_globus_id = config['GLOBUS']['nersc_globus_id']
    nersc_manifests_directory = config['GLOBUS']['nersc_manifests_directory']
    globus_root_dir = config['GLOBUS']['globus_root_dir']

    # list directories with restored files
    ls_output = subprocess.run(['globus', 'ls', f'{jgi_globus_id}:/{globus_root_dir}/'], capture_output=True, text=True)

    for sub_dir in ls_output.stdout.split('\n'):
        if not sub_dir:
            break
        # list contents of subdirectory and get Globus Download manifest file name
        sub_output = subprocess.run(['globus', 'ls', f'{jgi_globus_id}:/{globus_root_dir}/{sub_dir}'], capture_output=True, text=True)
        sub_output_split = sub_output.stdout.split('\n')
        manifest_file_name = [fn for fn in sub_output_split if 'Globus_Download' in fn][0]

        print(f"potential manifest file {manifest_file_name}")
        if 'Globus_Download' in manifest_file_name:
            logging.debug(f"transferring {manifest_file_name}")
            # Use Globus to transfer manifest file to destination directory
            subprocess.run(['globus', 'transfer', '--sync-level', 'exists',
                            f"{jgi_globus_id}:/{globus_root_dir}/{sub_dir}{manifest_file_name}",
                            f"{nersc_globus_id}:{nersc_manifests_directory}{manifest_file_name}"]) \
                if manifest_file_name else None


def create_globus_dataframe(manifests_dir):
    globus_df = pd.DataFrame()
    for manifest in os.listdir(manifests_dir):
        mani_df = pd.read_csv(os.path.join(manifests_dir, manifest))
        subdir = f"R{manifest.split('_')[2]}"
        mani_df['subdir'] = subdir
        globus_df = pd.concat([globus_df, mani_df], ignore_index=True)
    return globus_df


def create_globus_batch_file(project, config):

    root_dir = config['GLOBUS']['globus_root_dir']
    dest_root_dir = os.path.join(config['GLOBUS']['dest_root_dir'], f'{project}_analysis_projects')
    globus_df = create_globus_dataframe(config['GLOBUS']['nersc_manifests_directory'])
    mdb = get_mongo_db()
    samples_df = pd.DataFrame(mdb.samples.find({'file_status': 'RESTORED'}))
    globus_analysis_df = pd.merge(samples_df, globus_df, left_on='jdp_file_id', right_on='file_id')
    write_list = []
    for idx, row in globus_analysis_df.iterrows():
        filepath = os.path.join(root_dir, row.subdir, row['directory/path'], row.filename)
        dest_file_path = os.path.join(dest_root_dir, row.apGoldId, row.filename)
        write_list.append(f"{filepath} {dest_file_path}")
    globus_batch_filename = f'{project}_globus_batch_file.txt'
    with open(globus_batch_filename, 'w') as f:
        f.write('\n'.join(write_list))
    return globus_batch_filename, globus_analysis_df

@cli.command()
@click.argument('config_file', type=click.Path(dir_okay=True, resolve_path=True))
@click.argument('project')
def submit_globus_batch_file(project, config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    jgi_globus_id = config['GLOBUS']['jgi_globus_id']
    nersc_globus_id = config['GLOBUS']['nersc_globus_id']
    try:
        batch_file, globus_analysis_df = create_globus_batch_file(project,
                                                                  config)

        output = subprocess.run(['globus', 'transfer', '--batch', batch_file, jgi_globus_id,
                                 nersc_globus_id], capture_output=True, text=True)

        logging.debug(output.stdout)
        globus_analysis_df.apply(lambda x: update_sample_in_mongodb(x, {'file_status': 'transferring'}), axis=1)
        insert_globus_status_into_mongodb(output.stdout.split('\n')[1].split(':')[1], 'submitted')
        return output.stdout
    finally:
        os.remove(f'{project}_globus_batch_file.txt') if os.path.exists(f'{project}_globus_batch_file.txt') else None


def insert_globus_status_into_mongodb(task_id, task_status):
    mdb = get_mongo_db()
    mdb.globus.insert_one({'task_id': task_id, 'task_status': task_status})


def get_globus_task_status(task_id):
    output = subprocess.run(['globus', 'task', 'show', task_id], capture_output=True, text=True)
    return output.stdout.split('\n')[6].split(':')[1].strip()


def update_globus_task_status(task_id, task_status):
    mdb = get_mongo_db()
    mdb.globus.update_one({'task_id': task_id}, {'$set': {'task_status': task_status}})


@cli.command()
def update_globus_statuses():
    mdb = get_mongo_db()
    tasks = [t for t in mdb.globus.find({'task_status': {'$ne': 'SUCCEEDED'}})]
    for task in tasks:
        task_status = get_globus_task_status(task['task_id'])
        update_globus_task_status(task['task_id'], task_status)


cli.add_command(get_samples_data)
cli.add_command(restore_files)
cli.add_command(submit_globus_batch_file)
cli.add_command(update_globus_statuses)

if __name__ == '__main__':
    cli()


