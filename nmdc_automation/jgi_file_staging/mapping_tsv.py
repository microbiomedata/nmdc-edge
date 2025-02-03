import logging
import pandas as pd
from pathlib import Path
from argparse import ArgumentParser

from jgi_file_metadata import get_access_token, get_mongo_db, get_request


def create_mapping_tsv(project_name, mapping_file_path, study_id=None):
    ACCESS_TOKEN = get_access_token()
    if study_id is None:
        study_id = get_study_id(project_name, ACCESS_TOKEN)
    study_df = get_gold_ids(study_id, ACCESS_TOKEN)
    study_df['gold_project'] = study_df.gold_sequencing_project_identifiers.apply(lambda x: x[0].split(':')[1])
    study_df['gold_analysis_project'] = study_df.gold_project.apply(lambda x: get_gold_project(x, ACCESS_TOKEN))
    study_df = study_df.loc[pd.notna(study_df.gold_analysis_project), :]
    mdb = get_mongo_db()
    sequencing_project = mdb.sequencing_projects.find_one({'project_name': project_name})
    study_df['project_path'] = study_df.apply(lambda x: str(
        Path(sequencing_project['analysis_projects_dir'], sequencing_project['project_name'],
             f"{sequencing_project['project_name']}_analysis_projects", x['gold_analysis_project']) if x[
            'gold_analysis_project'] else None), axis=1)
    study_df = study_df[['id', 'gold_analysis_project', 'project_path']]
    study_df.columns = ['nucleotide_sequencing_id', 'project_id', 'project_path']
    study_df.to_csv(Path(mapping_file_path, 'mapping.tsv'), sep='\t', index=False)


def get_study_id(project_name, ACCESS_TOKEN):
    mdb = get_mongo_db()
    sequencing_project = mdb.sequencing_projects.find_one({'project_name': project_name})
    proposal_id = sequencing_project['proposal_id']
    url = (f'https://api.microbiomedata.org/nmdcschema/study_set?filter='
           f'{{"jgi_portal_study_identifiers":"jgi.proposal:{proposal_id}"}}')
    response_json = get_request(url, ACCESS_TOKEN)
    if response_json:
        return response_json['resources'][0]['id']
    else:
        return None


def get_gold_ids(nmdc_study_id, ACCESS_TOKEN):
    url = (f'https://api.microbiomedata.org/nmdcschema/data_generation_set?filter='
           f'{{"associated_studies":"{nmdc_study_id}",'
           f'"gold_sequencing_project_identifiers":{{"$exists":true}}}}&max_page_size=1000')
    study_samples = get_request(url, ACCESS_TOKEN)
    study_df = pd.DataFrame(study_samples['resources'])
    return study_df.loc[pd.notna(study_df['gold_sequencing_project_identifiers']), :]


def get_gold_project(gold_id, ACCESS_TOKEN):
    url = f"https://gold-ws.jgi.doe.gov/api/v1/analysis_projects?projectGoldId={gold_id}"
    study_samples_json = get_request(url, ACCESS_TOKEN)
    if not study_samples_json:
        logging.debug(f"failed {gold_id}")
    else:
        analysis_df = pd.DataFrame(study_samples_json)
        #     try:
        analysis_filter_df = analysis_df[
            (analysis_df.apType == 'Metagenome Analysis') | (analysis_df.apType == 'Metatranscriptome Analysis')]
        if len(analysis_filter_df.apGoldId.values) == 1:
            apGoldId = analysis_filter_df.apGoldId.values[0]
        else:
            logging.debug(f'{gold_id}, number samples: {len(analysis_filter_df.apGoldId.values)}')
            return None
        return apGoldId


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('project_name')
    parser.add_argument('-s', '--study_id', default=None)
    parser.add_argument('-f', '--file_path', default='.')
    args = vars((parser.parse_args()))
    create_mapping_tsv(args['project_name'], args['file_path'], args['study_id'])
