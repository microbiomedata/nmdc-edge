import os
import json
from pathlib import Path
import mongomock
import pandas as pd
import pytest
from unittest.mock import patch

from nmdc_automation.jgi_file_staging.mapping_tsv import (
    get_gold_ids,
    get_gold_analysis_project,
    get_study_id,
    create_mapping_tsv,
)
from nmdc_automation.db.nmdc_mongo import get_test_db
from nmdc_automation.jgi_file_staging.models import SequencingProject


@pytest.fixture
def fixtures_dir():
    return Path(__file__).parent / 'fixtures'


@pytest.fixture
def insert_sequencing_project():
    @mongomock.patch(servers=(('localhost', 27017),))
    def _insert():
        mdb = get_test_db()
        projects = [
            {'proposal_id': '507130', 'project_name': 'bioscales', 'nmdc_study_id': 'nmdc:sty-11-r2h77870',
             'analysis_projects_dir': 'nmdc_automation/jgi_file_staging/tests/fixtures/test_project'},
            {'proposal_id': '508306', 'project_name': '1000_soils', 'nmdc_study_id': 'nmdc:sty-11-28tm5d36',
             'analysis_projects_dir': '/global/cfs/cdirs/m3408/aim2/dev'},
        ]
        for p in projects:
            obj = SequencingProject(**p)
            mdb.sequencing_projects.insert_one(obj.dict())
        return mdb
    return _insert


@patch('nmdc_automation.jgi_file_staging.mapping_tsv.get_request')
@mongomock.patch(servers=(('localhost', 27017),))
def test_get_study_id(mock_get_request, insert_sequencing_project):
    mdb = insert_sequencing_project()
    mock_get_request.return_value = {'resources': [{'id': 'nmdc:sty-11-r2h77870'}]}
    study_id = get_study_id('bioscales', '', mdb)
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
    row = {'gold_project': 'Gp0061139'}
    result = get_gold_analysis_project(row, '')
    assert result == (None, 'Metagenome Analysis')


@patch('nmdc_automation.jgi_file_staging.mapping_tsv.get_request')
@patch('nmdc_automation.jgi_file_staging.mapping_tsv.get_access_token')
@mongomock.patch(servers=(('localhost', 27017),))
def test_create_mapping_tsv(mock_get_access_token, mock_get_request, fixtures_dir, tmp_path, insert_sequencing_project):
    mock_get_access_token.return_value = 'dummy_token'

    test_file = fixtures_dir / 'data_generation_set_response_create_mapping_file.json'
    if not test_file.exists():
        pytest.skip(f"Fixture file not found: {test_file}")

    with open(test_file, 'r', encoding='utf-8') as f:
        data_response = json.load(f)

    mock_get_request.side_effect = [
        data_response,
        [{
            'apGoldId': 'Ga0268315',
            'apType': 'Metagenome Analysis',
            'projects': ['Gp0307487'],
        }],
    ]

    mdb = insert_sequencing_project()
    output_file = tmp_path / 'bioscales.metag.map.tsv'

    create_mapping_tsv('bioscales', tmp_path, mdb, 'nmdc:sty-11-r2h77870')

    old_tsv = pd.read_csv(fixtures_dir / 'mapping.tsv', sep='\t')
    new_tsv = pd.read_csv(output_file, sep='\t')
    pd.testing.assert_frame_equal(old_tsv, new_tsv)
