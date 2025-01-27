import requests
import os
import pandas as pd
import numpy as np
import hashlib
# import pysam
# import click
from datetime import datetime
import json
import sys
import configparser
import time
from pathlib import Path

from jgi_file_metadata import get_access_token, check_access_token, get_analysis_projects_from_proposal_id, \
    get_sample_files, get_sequence_id, insert_samples_into_mongodb, get_mongo_db, get_files_and_agg_ids, \
    combine_sample_ids_with_agg_ids, get_samples_data, remove_unneeded_files, remove_large_files, get_seq_unit_names, \
    get_biosample_ids, insert_new_project_into_mongodb, get_request
from models import SequencingProject


def get_study_id(project_name, ACCESS_TOKEN):
    mdb = get_mongo_db()
    sequencing_project = mdb.sequencing_projects.find_one({'project': project_name})
    proposal_id = sequencing_project['proposal_id']
    url = (f'https://api.microbiomedata.org/nmdcschema/study_set?filter='
           f'{{"jgi_portal_study_identifiers":"jgi.proposal:{proposal_id}"}}')

    study_id = get_request(url, ACCESS_TOKEN)
    return study_id


def get_gold_ids(study_id, ACCESS_TOKEN):
    url = (f'https://api.microbiomedata.org/nmdcschema/data_generation_set?filter='
           f'%7B%22associated_studies%22%3A%22{study_id}%22%7D&max_page_size=1000')
    study_samples = get_request(url, ACCESS_TOKEN)
    gold_projects_df = pd.DataFrame()
    for sample in study_samples['resources']:
        print(sample['gold_sequencing_project_identifiers'][0].split(':')[1])
        gold_projects_df = pd.concat([gold_projects_df,
                                      get_project(sample['gold_sequencing_project_identifiers'][0].split(':')[1], ACCESS_TOKEN)])


def get_project(gold_id, ACCESS_TOKEN):
    url = f"https://gold-ws.jgi.doe.gov/api/v1/analysis_projects?projectGoldId={gold_id}"
    study_samples_json = get_request(url, ACCESS_TOKEN)
    gold_project = pd.DataFrame(study_samples_json)
    return gold_project
