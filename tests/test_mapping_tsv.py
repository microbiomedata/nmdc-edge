import os
import json
from pathlib import Path
import mongomock
import pandas as pd
import pytest
from unittest.mock import patch

from tests.fixtures import db_utils

from nmdc_automation.jgi_file_staging.mapping_tsv import (
    get_gold_ids,
    get_gold_analysis_project,
    get_study_id,
    create_mapping_tsv,
)
from nmdc_automation.jgi_file_staging.models import SequencingProject


@pytest.fixture
def insert_sequencing_project(test_db):
    @mongomock.patch(servers=(('localhost', 27017),))
    def _insert():
        projects = [
            {'proposal_id': '507130', 'project_name': 'bioscales', 'nmdc_study_id': 'nmdc:sty-11-r2h77870',
             'analysis_projects_dir': 'nmdc_automation/jgi_file_staging/tests/fixtures/test_project'},
            {'proposal_id': '508306', 'project_name': '1000_soils', 'nmdc_study_id': 'nmdc:sty-11-28tm5d36',
             'analysis_projects_dir': '/global/cfs/cdirs/m3408/aim2/dev'},
        ]
        for p in projects:
            obj = SequencingProject(**p)
            test_db.sequencing_projects.insert_one(obj.dict())
        return test_db
    return _insert


@patch('nmdc_automation.jgi_file_staging.mapping_tsv.get_request')
@mongomock.patch(servers=(('localhost', 27017),))
def test_get_study_id(mock_get_request, insert_sequencing_project):
    mdb = insert_sequencing_project()
    mock_get_request.return_value = {'resources': [{'id': 'nmdc:sty-11-r2h77870'}]}
    study_id = get_study_id('bioscales', mdb)
    assert study_id == 'nmdc:sty-11-r2h77870'


@patch('nmdc_automation.jgi_file_staging.mapping_tsv.get_request')
@mongomock.patch(servers=(('localhost', 27017),))
def test_get_gold_ids(mock_get_request, fixtures_dir):
    with open(fixtures_dir / 'data_generation_set_response.json', 'r', encoding='utf-8') as f:
        response = json.load(f)
    mock_get_request.return_value = response
    df = get_gold_ids('nmdc:sty-11-r2h77870', '')
    assert len(df) == 318


@patch('nmdc_automation.jgi_file_staging.mapping_tsv.get_request')
@mongomock.patch(servers=(('localhost', 27017),))
def test_get_gold_analysis_project(mock_get_request):
    mock_get_request.return_value = [{
        'apGoldId': 'Ga0268315',
        'apType': 'Metagenome Analysis',
        'projects': ['Gp0307487'],
    }]
    row = {'gold_project': 'Gp0307487'}
    result = get_gold_analysis_project(row, '')
    assert result == {'gold_analysis_project': 'Ga0268315', 'ap_type': 'Metagenome Analysis', 'gold_project': 'Gp0307487'}


@patch('nmdc_automation.jgi_file_staging.mapping_tsv.get_request')
@mongomock.patch(servers=(('localhost', 27017),))
def test_get_gold_analysis_project_multiple_metag(mock_get_request, fixtures_dir):
    with open(fixtures_dir / 'analysis_proj_multi_metag_response.json', 'r', encoding='utf-8') as f:
        response = json.load(f)
    mock_get_request.return_value = response
    row = pd.Series({'gold_project': 'Gp0061139'})
    result = get_gold_analysis_project(row, '')
    expected = pd.Series({'gold_project': 'Gp0061139', 'gold_analysis_project': None,
                                                     'ap_type':'Metagenome Analysis'})
    pd.testing.assert_series_equal(result, expected)


@patch('nmdc_automation.jgi_file_staging.mapping_tsv.get_request')
@patch('nmdc_automation.jgi_file_staging.mapping_tsv.get_access_token')
@mongomock.patch(servers=(('localhost', 27017),))
def test_create_mapping_tsv(mock_get_access_token, mock_get_request, fixtures_dir, tmp_path, insert_sequencing_project):
    mock_get_access_token.return_value = 'dummy_token'
    test_file = fixtures_dir / 'data_generation_set_response_mapping_tsv.json'
    # if not test_file.exists():
    #     pytest.skip(f"Fixture file not found: {test_file}")

    with open(test_file, 'r', encoding='utf-8') as f:
        data_response = json.load(f)

    mock_get_request.side_effect = [
        data_response,
        [{
            'apGoldId': 'Ga0268315',
            'apType': 'Metagenome Analysis',
        }],
        [{'apGoldId': 'Ga0222738', 'apType': 'Metatranscriptome Analysis'},
         {'apGoldId': 'Ga0224388','referenceApGoldId': 'Ga0222738','apType': 'Metatranscriptome mapping (self)'}]
    ]

    mdb = insert_sequencing_project()
    metag_file = tmp_path / 'bioscales.metag.map.tsv'
    metat_file = tmp_path / 'bioscales.metat.map.tsv'

    create_mapping_tsv('bioscales', mdb, 'nmdc:sty-11-r2h77870', tmp_path)

    reference_metag_tsv = pd.read_csv(fixtures_dir / 'metag_mapping.tsv', sep='\t')
    reference_metat_tsv = pd.read_csv(fixtures_dir / 'metat_mapping.tsv', sep='\t')
    metag_tsv = pd.read_csv(metag_file, sep='\t')
    metat_tsv = pd.read_csv(metat_file, sep='\t')
    pd.testing.assert_frame_equal(reference_metag_tsv, metag_tsv)
    pd.testing.assert_frame_equal(reference_metat_tsv, metat_tsv)

@patch('nmdc_automation.jgi_file_staging.mapping_tsv.get_request')
@patch('nmdc_automation.jgi_file_staging.mapping_tsv.get_access_token')
@mongomock.patch(servers=(('localhost', 27017),))
def test_create_mapping_tsv_missing_analysis_project(mock_get_access_token, mock_get_request, fixtures_dir, tmp_path, insert_sequencing_project):
    mock_get_access_token.return_value = 'dummy_token'
    test_file = fixtures_dir / 'data_generation_set_response_mapping_tsv.json'
    # if not test_file.exists():
    #     pytest.skip(f"Fixture file not found: {test_file}")

    with open(test_file, 'r', encoding='utf-8') as f:
        data_response = json.load(f)

    mock_get_request.side_effect = [
        data_response,
        [{
            'apGoldId': 'Ga0268315',
            'apType': 'Metagenome Analysis',
        }],
        [{'apGoldId': 'Ga0222738', 'apType': 'Metatranscriptome Analysis','referenceApGoldId':None}]
    ]

    mdb = insert_sequencing_project()
    metag_file = tmp_path / 'bioscales.metag.map.tsv'
    metat_file = tmp_path / 'bioscales.metat.map.tsv'

    create_mapping_tsv('bioscales', mdb, 'nmdc:sty-11-r2h77870', tmp_path)

    reference_metag_tsv = pd.read_csv(fixtures_dir / 'metag_mapping.tsv', sep='\t')
    reference_metat_tsv = pd.read_csv(fixtures_dir / 'metat_mapping.tsv', sep='\t')
    reference_metat_tsv.loc[1, 'project_id'] = None
    reference_metat_tsv.loc[1, 'project_path'] = None
    metag_tsv = pd.read_csv(metag_file, sep='\t')
    metat_tsv = pd.read_csv(metat_file, sep='\t')
    pd.testing.assert_frame_equal(reference_metag_tsv, metag_tsv)
    pd.testing.assert_frame_equal(reference_metat_tsv, metat_tsv)