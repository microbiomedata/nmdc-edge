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
    study_df = study_df.apply(
        lambda x: get_gold_analysis_project(x, ACCESS_TOKEN), axis=1)
    study_df = study_df.loc[pd.notna(study_df.gold_analysis_project), :]
    metat_study_df = study_df.loc[study_df.ap_type == 'Metatranscriptome Analysis', ['id', 'gold_analysis_project']]
    new_row_list = []
    for idx, row in metat_study_df.iterrows():
        new_row_list.append({'id': row.id, 'ap_gold_id': row.gold_analysis_project[0]})
        new_row_list.append({'id': row.id, 'ap_gold_id': row.gold_analysis_project[1]})
    metat_study_df = pd.DataFrame(new_row_list)
    metag_study_df = study_df.loc[study_df.ap_type == 'Metagenome Analysis', ['id', 'gold_analysis_project']]
    create_tsv_file(metag_study_df, mapping_file_path, project_name, 'metag')
    if not metat_study_df.empty:
        create_tsv_file(metat_study_df, mapping_file_path, project_name, 'metat')


def create_tsv_file(study_df, mapping_file_path, project_name, ap_type):
    mdb = get_mongo_db()
    sequencing_project = mdb.sequencing_projects.find_one({'project_name': project_name})
    study_df['project_path'] = study_df.apply(lambda x: str(
        Path(sequencing_project['analysis_projects_dir'], sequencing_project['project_name'],
             f"{sequencing_project['project_name']}_analysis_projects", x['gold_analysis_project']) if x[
            'gold_analysis_project'] else None), axis=1)
    study_df = study_df[['id', 'gold_analysis_project', 'project_path']]
    study_df.columns = ['nucleotide_sequencing_id', 'project_id', 'project_path']
    study_df.to_csv(Path(mapping_file_path, f'{project_name}.{ap_type}.map.tsv'), sep='\t', index=False)


def get_study_id(project_name, ACCESS_TOKEN):
    """
    Given a proposal_id for a project, return the corresponding NMDC study id
    """
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
    """
    Find the gold ids for a given NMDC study by querying the nmdc schema data_generation_set endpoint
    """
    url = (f'https://api.microbiomedata.org/nmdcschema/data_generation_set?filter='
           f'{{"associated_studies":"{nmdc_study_id}",'
           f'"gold_sequencing_project_identifiers":{{"$exists":true}}}}&max_page_size=1000')
    study_samples = get_request(url, ACCESS_TOKEN)
    study_df = pd.DataFrame(study_samples['resources'])
    return study_df.loc[pd.notna(study_df['gold_sequencing_project_identifiers']), :]


def get_gold_analysis_project(row, ACCESS_TOKEN):
    url = f"https://gold-ws.jgi.doe.gov/api/v1/analysis_projects?projectGoldId={row['gold_project']}"
    study_samples_json = get_request(url, ACCESS_TOKEN)
    if not study_samples_json:
        logging.debug(f"failed {row['gold_project']}")
        row['gold_analysis_project'] = None
        row['ap_type'] = None
    else:

        analysis_df = pd.DataFrame(study_samples_json)

        filter_values = analysis_df.loc[
            (analysis_df.apType == 'Metagenome Analysis') | (analysis_df.apType == 'Metatranscriptome Analysis'),
            ['apGoldId', 'apType']].sort_values('apGoldId', ascending=False).values[0]
        ap_gold_id = filter_values[0]
        ap_type = filter_values[1]
        if ap_type == 'Metatranscriptome Analysis':
            mapping_type = f"{ap_type.split(' ')[0]} mapping (self)"
            ap_gold_id = analysis_df.loc[(analysis_df.apGoldId == ap_gold_id) |
                                         ((analysis_df.apType == mapping_type) &
                                          (analysis_df.referenceApGoldId == ap_gold_id)), 'apGoldId'].values
        elif ap_type == 'Metagenome Analysis' and len(analysis_df[(analysis_df.apType == 'Metagenome Analysis')]) > 1:
            return None, ap_type
        row['gold_analysis_project'] = ap_gold_id
        row['ap_type'] = ap_type
    return row


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('project_name')
    parser.add_argument('-s', '--study_id', default=None)
    parser.add_argument('-f', '--file_path', default='.')
    args = vars((parser.parse_args()))
    create_mapping_tsv(args['project_name'], args['file_path'], args['study_id'])
