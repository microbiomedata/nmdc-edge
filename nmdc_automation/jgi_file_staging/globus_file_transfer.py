import configparser
import sys
from datetime import datetime
import pandas as pd
import os
import logging
from pathlib import Path, PurePosixPath
import subprocess
import argparse
from typing import List, Optional, Union
from nmdc_automation.jgi_file_staging.file_restoration import update_sample_in_mongodb, update_file_statuses
from nmdc_automation.db.nmdc_mongo import get_db

logging.basicConfig(filename='file_staging.log',
                    format='%(asctime)s.%(msecs)03d %(levelname)s {%(module)s} [%(funcName)s] %(message)s',
                    datefmt='%Y-%m-%d,%H:%M:%S', level=logging.DEBUG)

OUTPUT_DIR = Path(".")


def get_project_globus_manifests(project_name: str, mdb, config_file: str = None,
                                 config: configparser.ConfigParser = None) -> List[str]:
    """
    Retrieve the globus manifest files for files to be transferred from Globus to MongoDB
    """
    if config_file:
        config = configparser.ConfigParser()
        config.read(config_file)
    samples_df = pd.DataFrame(mdb.samples.find({'project_name': project_name, 'file_status':
        {'$nin': ['in transit', 'transferred', 'expired', 'PURGED']}}))
    samples_df = samples_df[pd.notna(samples_df.request_id)]
    samples_df['request_id'] = samples_df['request_id'].astype(int)
    manifests_list = []
    globus_manifest_files = [get_globus_manifest(int(request_id), config=config) for request_id in
                             samples_df.request_id.unique()]

    return globus_manifest_files


def get_globus_manifest(request_id: int, config_file: str = None, config: configparser.ConfigParser = None) -> str:
    if config_file:
        config = configparser.ConfigParser()
        config.read(config_file)
    jgi_globus_id = config['GLOBUS']['jgi_globus_id']
    nersc_globus_id = config['GLOBUS']['nersc_globus_id']
    nersc_manifests_directory = config['GLOBUS']['nersc_manifests_directory']
    globus_root_dir = config['GLOBUS']['globus_root_dir'].lstrip('/')

    globus_path = PurePosixPath(globus_root_dir) / f"R{request_id}"

    sub_output = subprocess.run(['globus', 'ls', f'{jgi_globus_id}:/{globus_path}'],
                                capture_output=True, text=True)
    sub_output.check_returncode()
    sub_output_split = sub_output.stdout.split('\n')
    logging.debug(f"request_id: {request_id} globus ls: {sub_output_split}")

    manifest_files = [fn for fn in sub_output_split if 'Globus_Download' in fn]
    if not manifest_files:
        logging.warning("No Globus_Download file found")
        return ''
    manifest_file_name = manifest_files[0]
    logging.debug(f"manifest filename {manifest_file_name}")

    if Path(nersc_manifests_directory, manifest_file_name).exists():
        return manifest_file_name

    logging.debug(f"transferring {manifest_file_name}")
    manifest_sub_out = subprocess.run(['globus', 'transfer', '--sync-level', 'exists',
        f"{jgi_globus_id}:/{globus_path}/{manifest_file_name}",
        f"{nersc_globus_id}:{nersc_manifests_directory}/{manifest_file_name}"],
        capture_output=True, text=True)
    manifest_sub_out.check_returncode()
    logging.debug(f"manifest globus transfer: {manifest_sub_out.stdout}, errors: {manifest_sub_out.stderr}")

    return manifest_file_name


def create_globus_dataframe(project_name: str, config: configparser.ConfigParser, mdb) -> pd.DataFrame:

    globus_manifest_files = get_project_globus_manifests(project_name, mdb, config=config)

    globus_df = pd.DataFrame()
    manifest_relative_path = os.path.join(config['GLOBUS']['nersc_manifests_directory'])
    project_root = Path(__file__).parent.parent.parent
    nersc_manifests_directory = os.path.join(project_root, manifest_relative_path)
    for manifest in globus_manifest_files:
        mani_df = pd.read_csv(os.path.join(nersc_manifests_directory, manifest))
        subdir = f"R{manifest.split('_')[2]}"
        mani_df['subdir'] = subdir
        globus_df = pd.concat([globus_df, mani_df], ignore_index=True)
    return globus_df


def create_globus_batch_file(project: str, config: configparser.ConfigParser, mdb,
                             output_dir: Optional[Union[str, Path]]) -> (str, pd.DataFrame):
    """
    Creates batch file for the globus file transfer
    :param project: name of project
    :param config: configparser object with parameters for globus transfers
    :return: globus batch file name and dataframe with sample files being transferred
    1) update statuses of files
    1) get samples from database that have been restored from tape (file_status: 'ready')
    2) create a dataframe from the Globus manifests
    3) write to globus batch file
    """
    if output_dir is None:
        output_dir = Path(".")
    else:
        output_dir = Path(output_dir)

    update_file_statuses(project=project, mdb=mdb, config=config)
    samples_df = pd.DataFrame(mdb.samples.find({'file_status': 'ready'}))
    if samples_df.empty:
        logging.debug(f"no samples ready to transfer")
        sys.exit('no samples ready to transfer, try running file_restoration.py -u')
    samples_df = samples_df[pd.notna(samples_df.request_id)]
    samples_df['request_id'] = samples_df['request_id'].astype(int)
    # logging.debug(f"nan request_ids {samples_df['request_id']}")
    root_dir = config['GLOBUS']['globus_root_dir']
    dest_root_dir = os.path.join(config['PROJECT']['analysis_projects_dir'], f'{project}_analysis_projects')
    globus_df = create_globus_dataframe(project, config, mdb)

    logging.debug(f"samples_df columns {samples_df.columns}, globus_df columns {globus_df.columns}")
    globus_analysis_df = pd.merge(samples_df, globus_df, left_on='jdp_file_id', right_on='file_id')
    write_list = []
    for idx, row in globus_analysis_df.iterrows():
        filepath = os.path.join(root_dir, row.subdir, row['directory/path'], row.filename)
        dest_file_path = os.path.join(dest_root_dir, row.apGoldId, row.filename)
        write_list.append(f"{filepath} {dest_file_path}")
    globus_batch_filename = (
            output_dir / f"{project}_{samples_df['request_id'].unique()[0]}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_globus_batch_file.txt"
    )

    with open(globus_batch_filename, 'w') as f:
        f.write('\n'.join(write_list))
    return str(globus_batch_filename), globus_analysis_df


def submit_globus_batch_file(project: str, config_file: str, mdb) -> str:
    """
    *Must run globus login first!*
    create a globus batch file and submit it to globus
    :param project: name of project
    :param config_file: path to configuration file
    1) create the globus batch file
    2) submit the globus batch file using the globus CLI
    3) insert globus task into the database
    """
    config = configparser.ConfigParser()
    config.read(config_file)
    jgi_globus_id = config['GLOBUS']['jgi_globus_id']
    nersc_globus_id = config['GLOBUS']['nersc_globus_id']

    batch_file, globus_analysis_df = create_globus_batch_file(project,
                                                              config=config, mdb=mdb)

    output = subprocess.run(['globus', 'transfer', '--batch', batch_file, jgi_globus_id,
                             nersc_globus_id], capture_output=True, text=True)

    logging.debug(output.stdout)
    globus_analysis_df.apply(lambda x: update_sample_in_mongodb(x, {'file_status': 'in transit'}, mdb), axis=1)

    insert_globus_status_into_mongodb(output.stdout.split('\n')[1].split(':')[1], 'submitted', mdb)
    return output.stdout


def insert_globus_status_into_mongodb(task_id: str, task_status: str, mdb):
    mdb.globus.insert_one({'task_id': task_id, 'task_status': task_status})


def get_globus_task_status(task_id: str):
    output = subprocess.run(['globus', 'task', 'show', task_id], capture_output=True, text=True)
    return output.stdout.split('\n')[6].split(':')[1].strip()


def update_globus_task_status(task_id: str, task_status: str, mdb):
    mdb.globus.update_one({'task_id': task_id}, {'$set': {'task_status': task_status}})


def update_globus_statuses(mdb):
    tasks = [t for t in mdb.globus.find({'task_status': {'$ne': 'SUCCEEDED'}})]
    for task in tasks:
        task_status = get_globus_task_status(task['task_id'])
        update_globus_task_status(task['task_id'], task_status, mdb)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('project_name')
    parser.add_argument('config_file')
    parser.add_argument('-r', '--request_id', help='Globus request id (from file restoration api)')
    parser.add_argument('-u', '--update_globus_statuses', action='store_true',
                        help='update globus task statuses', default=False)
    parser.add_argument('-g', '--get_project_manifests', action='store_true',
                        help='get all globus project manifests', default=False)

    args = vars((parser.parse_args()))
    config_file = args['config_file']
    mdb = get_db()
    if not mdb:
        logging.error("MongoDB connection failed")
        sys.exit(1)
    if args['request_id']:
        get_globus_manifest(args['request_id'], config_file=config_file)
    elif args['update_globus_statuses']:
        update_globus_statuses(mdb)
    elif args['get_project_manifests']:
        get_project_globus_manifests(args['project_name'], mdb, config_file)
    else:
        submit_globus_batch_file(args['project_name'], args['config_file'])

