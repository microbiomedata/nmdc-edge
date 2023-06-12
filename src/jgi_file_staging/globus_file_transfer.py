import configparser

import pandas as pd
import os
import logging

import click
from mongo import get_mongo_db
import subprocess
import argparse
from file_restoration import update_sample_in_mongodb

logging.basicConfig(filename='file_staging.log',
                    format='%(asctime)s.%(msecs)03d %(levelname)s {%(module)s} [%(funcName)s] %(message)s',
                    datefmt='%Y-%m-%d,%H:%M:%S', level=logging.DEBUG)


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
        sub_output = subprocess.run(['globus', 'ls', f'{jgi_globus_id}:/{globus_root_dir}/{sub_dir}'],
                                    capture_output=True, text=True)
        sub_output_split = sub_output.stdout.split('\n')
        manifest_file_name = [fn for fn in sub_output_split if 'Globus_Download' in fn][0]

        if 'Globus_Download' in manifest_file_name:
            logging.debug(f"transferring {manifest_file_name}")
            # Use Globus to transfer manifest file to destination directory
            subprocess.run(['globus', 'transfer', '--sync-level', 'exists',
                            f"{jgi_globus_id}:/{globus_root_dir}/{sub_dir}{manifest_file_name}",
                            f"{nersc_globus_id}:{nersc_manifests_directory}{manifest_file_name}"])


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


def update_globus_statuses():
    mdb = get_mongo_db()
    tasks = [t for t in mdb.globus.find({'task_status': {'$ne': 'SUCCEEDED'}})]
    for task in tasks:
        task_status = get_globus_task_status(task['task_id'])
        update_globus_task_status(task['task_id'], task_status)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('project_name')
    parser.add_argument('config_file')
    parser.add_argument('-u', '--update_globus_statuses', action='store_true', help='update globus task statuses',
                        default=False)
    args = vars((parser.parse_args()))

    if args['update_globus_statuses']:
        update_globus_statuses()
    else:
        submit_globus_batch_file(args['project_name'], args['config_file'])
