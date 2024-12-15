import configparser
import sys

import pandas as pd
import numpy as np
import requests
import os
import logging
import time
import argparse
from itertools import chain

from mongo import get_mongo_db
from models import Sample
from typing import List
from pydantic import ValidationError

logging.basicConfig(filename='file_staging.log',
                    format='%(asctime)s.%(msecs)03d %(levelname)s {%(module)s} [%(funcName)s] %(message)s',
                    datefmt='%Y-%m-%d,%H:%M:%S', level=logging.DEBUG)

"""
1. Get sample metadata and enter into mongodb
2. Restore files from tape
    repeat until all files restored
3. Get Globus manifests for restored files
4. Create and submit Globus batch file

Config file contains parameters that can change.
"""

ACCEPT = "application/json"


def get_samples_data(samples_csv_file: str, proposal_id: int, project: str, config_file: str) -> None:
    """
    Get JGI sample metadata using the gold API and store in a mongodb
    :param samples_csv_file: CSV file with biosample ID's
    :param proposal_id: JGI proposal ID
    :param project: Name of project (e.g., GROW, Bioscales, NEON)
    :param config_file: Config file with parameters
    :return:
    """
    # check_restore_status()
    config = configparser.ConfigParser()
    config.read(config_file)
    ACCESS_TOKEN = get_access_token()
    all_files_list = get_sample_files(samples_csv_file, ACCESS_TOKEN, eval(config['JDP']['delay']))
    files_df = pd.DataFrame(all_files_list)

    gold_analysis_data = get_analysis_projects_from_proposal_id(proposal_id, ACCESS_TOKEN)
    gold_analysis_data_df = pd.DataFrame(gold_analysis_data)
    gold_analysis_files_df = pd.merge(gold_analysis_data_df, files_df, left_on='itsApId',
                                      right_on='analysis_project_id')
    gold_analysis_files_df = remove_unneeded_files(gold_analysis_files_df, eval(config['JDP']['remove_files']))

    gold_analysis_files_df['project'] = project
    logging.debug(f'number of samples to insert: {len(gold_analysis_files_df)}')
    logging.debug(gold_analysis_files_df.head().to_dict('records'))
    insert_samples_into_mongodb(gold_analysis_files_df.to_dict('records'))


def get_access_token() -> str:
    OFFLINE_TOKEN = os.environ.get('OFFLINE_TOKEN')
    url = f'https://gold-ws.jgi.doe.gov/exchange?offlineToken={OFFLINE_TOKEN}'
    response = requests.get(url)
    sys.exit(f"get_access_token: {response.text}") if response.status_code != 200 else None

    return response.text


def check_access_token(ACCESS_TOKEN: str, delay: float) -> str:
    gold_biosample_url = 'https://gold-ws.jgi.doe.gov/api/v1/projects?biosampleGoldId=Gb0291582'
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "accept": ACCEPT, 'User-agent': 'nmdc bot 0.1'}
    time.sleep(delay)
    gold_biosample_response = requests.get(gold_biosample_url, headers=headers)
    if gold_biosample_response.status_code == 200:
        return ACCESS_TOKEN
    else:
        return get_access_token()


def get_sample_files(samples_csv_file: str, ACCESS_TOKEN: str, delay: float) -> List[dict]:
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
        ACCESS_TOKEN = check_access_token(ACCESS_TOKEN, delay)
        try:
            seq_id = get_sequence_id(biosample_id, ACCESS_TOKEN, delay)
            sample_files_list, agg_id_list = get_files_and_agg_ids(seq_id, ACCESS_TOKEN)
        except IndexError:
            logging.exception(f'skipping biosample_id: {biosample_id}')
            continue
        combine_sample_ids_with_agg_ids(sample_files_list, agg_id_list, biosample_id, seq_id, all_files_list)
    pd.DataFrame(all_files_list).to_csv('all_files_list.csv', index=False)
    # logging.debug(f"all_files_list: {all_files_list}")
    return all_files_list


def get_sequence_id(gold_id: str, ACCESS_TOKEN: str, delay: float):
    # given a gold biosample id, get the JGI sequencing ID
    gold_biosample_url = f'https://gold-ws.jgi.doe.gov/api/v1/projects?biosampleGoldId={gold_id}'
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "accept": ACCEPT, 'User-agent': 'nmdc bot 0.1'}
    time.sleep(delay)
    gold_biosample_response = requests.get(gold_biosample_url, headers=headers)
    if gold_biosample_response.status_code == 200:
        gold_biosample_data = gold_biosample_response.json()[0]
        return gold_biosample_data['itsSpid']
    else:
        logging.debug(f"gold_biosample_response: {gold_biosample_response.text}")
        return None


def get_analysis_projects_from_proposal_id(proposal_id: int, ACCESS_TOKEN: str) -> List[dict]:
    gold_analysis_url = f'https://gold-ws.jgi.doe.gov/api/v1/analysis_projects?itsProposalId={proposal_id}'
    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}', "accept": ACCEPT}
    gold_analysis_response = requests.get(gold_analysis_url, headers=headers)
    gold_analysis_data = gold_analysis_response.json()
    ap_type_gold_analysis_data = [proj for proj in gold_analysis_data if
                                  proj['apType'] in ["Metagenome Analysis", "Metatranscriptome Analysis"]]
    return ap_type_gold_analysis_data


def get_files_and_agg_ids(sequencing_id, ACCESS_TOKEN) -> (List[dict], List[str]):
    # Given a JGI sequencing ID, get the list of files and agg_ids associated with the biosample
    logging.debug(f"sequencing_id {sequencing_id}")
    seqid_url = f"https://files.jgi.doe.gov/search/?q={sequencing_id}&f=project_id&a=false&h=false&d=asc&p=1&x=10&api_version=2"
    headers = {'X-CSRFToken': f'Token {ACCESS_TOKEN}', "accept": ACCEPT}
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


def combine_sample_ids_with_agg_ids(sample_files_list, agg_id_list, biosample_id, seq_id, all_files_list) -> None:
    for sample, agg_id in zip(sample_files_list, agg_id_list):
        for files_dict in sample:
            seq_unit_name = files_dict['metadata']['seq_unit_name'] if 'seq_unit_name' in files_dict[
                'metadata'].keys() else None
            file_format = files_dict['metadata']['file_format'] if 'file_format' in files_dict[
                'metadata'].keys() else None
            md5sum = files_dict['md5sum'] if 'md5sum' in files_dict.keys() else None
            all_files_list.append({'biosample_id': biosample_id, 'seq_id': seq_id, 'file_name': files_dict['file_name'],
                                   'file_status': files_dict['file_status'], 'file_type': files_dict['file_type'],
                                   'file_size': files_dict['file_size'],
                                   'jdp_file_id': files_dict['_id'], 'md5sum': md5sum,
                                   'file_format': file_format,
                                   'analysis_project_id': agg_id, 'seq_unit_name': seq_unit_name})
            if 'metadata' not in files_dict.keys():
                print(f"biosample_id {biosample_id}, seq_id{seq_id}")


def remove_unneeded_files(seq_files_df: pd.DataFrame, remove_files_list: list) -> pd.DataFrame:
    """
    Remove files that are not needed
    large files (*.domtblout and *.img_nr.last.blasttab)
    fastq and filtered fastq files from duplicate analyses
    :param seq_files_df:
    :param remove_files_list
    :return: DataFrame
    """
    seq_files_df = remove_large_files(seq_files_df, remove_files_list)
    seq_files_df = remove_duplicate_analysis_files(seq_files_df)
    return seq_files_df


def remove_large_files(seq_files_df: pd.DataFrame, remove_files_list: list) -> pd.DataFrame:
    for file_type in remove_files_list:
        seq_files_df = seq_files_df[(~seq_files_df['file_name'].str.contains(file_type))]
    return seq_files_df


def remove_duplicate_analysis_files(seq_files_df: pd.DataFrame) -> pd.DataFrame:
    """
    remove fastq and filtered fastq files from duplicate analyses
    :param seq_files_df:
    :return: DataFrame
    """
    ap_gold_ids = list(seq_files_df.apGoldId.unique())

    drop_idx = []
    for gold_id in ap_gold_ids:
        print(gold_id)
        seq_unit_names_list = get_seq_unit_names(seq_files_df, gold_id)
        for idx, row in seq_files_df.loc[seq_files_df.apGoldId == gold_id, :].iterrows():
            # find rows with fastq files to remove (fastq file name is not in list of seq_unit_names and is not
            # input.corr.fastq.gz)
            if 'fastq' in row.file_name and ~np.any(
                    [seq in row.file_name for seq in seq_unit_names_list]) and row.file_name != 'input.corr.fastq.gz':
                drop_idx.append(idx)
    seq_files_df.drop(drop_idx, inplace=True)
    return seq_files_df


def get_seq_unit_names(analysis_files_df, gold_id):
    seq_unit_names = []
    for idx, row in analysis_files_df.loc[pd.notna(analysis_files_df.seq_unit_name)
                                          & (analysis_files_df.apGoldId == gold_id)
                                          & (analysis_files_df.file_type == "['contigs']")
                                              (analysis_files_df.file_name.str.contains('assembly'))].iterrows():
        if type(row.seq_unit_name) is str:
            seq_unit_names.append(row.seq_unit_name)
        elif type(row.seq_unit_name) is list:
            seq_unit_names.extend(row.seq_unit_name)

    seq_unit_names_list = list(set(seq_unit_names))
    seq_unit_names_list = [
        ".".join(filename.split(".")[:4]) for filename in seq_unit_names_list
    ]
    return seq_unit_names_list


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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('sample_file')
    parser.add_argument('proposal_id')
    parser.add_argument('project_name')
    parser.add_argument('config_file')
    args = vars((parser.parse_args()))

    get_samples_data(args['sample_file'], args['proposal_id'], args['project_name'], args['config_file'])
