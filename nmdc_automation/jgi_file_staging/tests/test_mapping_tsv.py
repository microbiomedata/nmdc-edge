import unittest
import os
import pytest
from pathlib import Path
from unittest.mock import patch, Mock
import mongomock
import json
import pandas as pd

from nmdc_automation.jgi_file_staging.mapping_tsv import get_gold_ids, get_gold_analysis_project, get_study_id, create_mapping_tsv
from nmdc_automation.db.nmdc_mongo import get_test_db
from nmdc_automation.jgi_file_staging.models import SequencingProject


class TestMappingFile(unittest.TestCase):
    def setUp(self) -> None:
        self.fixtures = os.path.join(os.path.dirname(__file__), 'fixtures')
        self.config_file = os.path.join(self.fixtures, 'config.ini')

    def tearDown(self) -> None:
        pass

    @staticmethod
    @mongomock.patch(servers=(('localhost', 27017),))
    def insert_sequencing_project():
        insert_dict = {'proposal_id': '507130', 'project_name': 'bioscales',
                       'nmdc_study_id': 'nmdc:sty-11-r2h77870',
                       'analysis_projects_dir': 'nmdc_automation/jgi_file_staging/tests/fixtures/test_project'}
        insert_object = SequencingProject(**insert_dict)
        mdb = get_test_db()
        mdb.sequencing_projects.insert_one(insert_object.dict())
        insert_dict = {'proposal_id': '508306', 'project_name': '1000_soils', 'nmdc_study_id': 'nmdc:sty-11-28tm5d36',
                       'analysis_projects_dir': '/global/cfs/cdirs/m3408/aim2/dev'}
        insert_object = SequencingProject(**insert_dict)
        mdb.sequencing_projects.insert_one(insert_object.dict())

    @patch('nmdc_automation.jgi_file_staging.mapping_tsv.get_request')
    @mongomock.patch(servers=(('localhost', 27017),))
    def test_get_study_id(self, mock_get_request):
        mdb = get_test_db()
        self.insert_sequencing_project()
        mock_get_request.return_value = {'resources': [{'id': 'nmdc:sty-11-r2h77870'}]}

        study_id = get_study_id('bioscales', '', mdb)
        self.assertEqual(study_id, 'nmdc:sty-11-r2h77870')  # add assertion here

    @patch('nmdc_automation.jgi_file_staging.mapping_tsv.get_request')
    @mongomock.patch(servers=(('localhost', 27017),))
    def test_get_gold_ids(self, mock_get_request):
        with open(Path(self.fixtures, 'data_generation_set_response.json'), 'r', encoding="utf-8") as fp:
            data_generation_set_response = json.load(fp)
        mock_get_request.return_value = data_generation_set_response
        study_df = get_gold_ids('nmdc:sty-11-r2h77870', '')
        self.assertEqual(len(study_df), 318)

    @patch('nmdc_automation.jgi_file_staging.mapping_tsv.get_request')
    @mongomock.patch(servers=(('localhost', 27017),))
    def test_get_gold_analysis_project(self, mock_get_request):
        mock_get_request.return_value = \
            [{'apGoldId': 'Ga0268315', 'organismGoldId': None, 'referenceApGoldId': None,
              'apName': 'Phyllosphere microbial comminities from switchgrass, GLBRC, Michigan, United States - '
                        'G5R4_NF_05JUN2017_LD1',
              'apType': 'Metagenome Analysis', 'studyId': 'Gs0128851', 'itsApId': 1191373, 'imgSubmissionId': 191551,
              'imgTaxonOid': 3300028472, 'imgPipelineVersion': 'IMG Annotation Pipeline v.4.16.4',
              'assemblyMethod': 'SPAdes v. 3.11.1', 'publications': [], 'sraRuns': [], 'projects': ['Gp0307487'],
              'contacts': [{'name': 'Ashley Shade', 'email': 'shade.e41se@1.com', 'roles': ['PI']},
                           {'name': 'Keara Grady', 'email': 'gr111kea@1.edu', 'roles': ['other']}],
              'modDate': '2024-11-04', 'addDate': '2018-04-21'}]
        row = {'gold_project': 'Gp0307487'}
        analysis_project_id = get_gold_analysis_project(row, '')
        self.assertEqual(analysis_project_id, {'gold_analysis_project': 'Ga0268315', 'ap_type': 'Metagenome Analysis', 'gold_project': 'Gp0307487'})

    # TODO: find this fixture: nmdc_automation/nmdc_automation/jgi_file_staging/tests/fixtures
    #  /analysis_proj_multi_metag_response.json
    @patch('nmdc_automation.jgi_file_staging.mapping_tsv.get_request')
    @mongomock.patch(servers=(('localhost', 27017),))
    def test_get_gold_analysis_project_multiple_metag(self, mock_get_request):
        with open(Path(self.fixtures, 'analysis_proj_multi_metag_response.json'), 'r', encoding="utf-8") as fp:
            analysis_proj_response = json.load(fp)
        mock_get_request.return_value = analysis_proj_response
        row = {'gold_project': 'Gp0061139'}
        analysis_project_id = get_gold_analysis_project(row, '')
        self.assertEqual(analysis_project_id, (None, 'Metagenome Analysis'))


    @patch('nmdc_automation.jgi_file_staging.mapping_tsv.get_request')
    @patch('nmdc_automation.jgi_file_staging.mapping_tsv.get_access_token')
    def test_create_mapping_tsv(self,mock_get_access_token, mock_get_request, tmp_path):
        # Arrange
        mock_get_access_token.return_value = 'gQEACCb3y5gCjutaktiZdWYyfe7NkuMmvKySSMD_cVEegp6GzW5yig'
        test_fixture_file = Path(self.fixtures, 'data_generation_set_response_create_mapping_file.json')
        if not test_fixture_file.exists():
            raise FileNotFoundError(f"Test fixture file not found: {test_fixture_file}")
        # Load the JSON data from the fixture file
        with open(test_fixture_file, 'r', encoding="utf-8") as fp:
            data_generation_set_response = json.load(fp)
        # Mock the response for the first API call
        mock_get_request.side_effect = [
            data_generation_set_response,
            [{
                'apGoldId': 'Ga0268315',
                'organismGoldId': None,
                'referenceApGoldId': None,
                'apName': 'Phyllosphere microbial comminities from switchgrass, GLBRC, Michigan, United States - G5R4_NF_05JUN2017_LD1',
                'apType': 'Metagenome Analysis',
                'studyId': 'Gs0128851',
                'itsApId': 1191373,
                'imgSubmissionId': 191551,
                'imgTaxonOid': 3300028472,
                'imgPipelineVersion': 'IMG Annotation Pipeline v.4.16.4',
                'assemblyMethod': 'SPAdes v. 3.11.1',
                'publications': [],
                'sraRuns': [],
                'projects': ['Gp0307487'],
                'contacts': [
                    {'name': 'Ashley Shade', 'email': 'shade.aseehy@1.com', 'roles': ['PI']},
                    {'name': 'Keara Grady', 'email': 'eef@1.edu', 'roles': ['other']}
                ],
                'modDate': '2024-11-04',
                'addDate': '2018-04-21'
            }]
        ]

        # Get test DB
        mdb = get_test_db()

        # Use tmp_path as the safe, isolated mapping directory
        mapping_path = tmp_path
        mapping_file_path = mapping_path / 'bioscales.metag.map.tsv'

        # Act
        create_mapping_tsv('bioscales', mapping_path, mdb, 'nmdc:sty-11-r2h77870')

        # Assert
        old_mapping_tsv = pd.read_csv(Path('tests/fixtures/mapping.tsv'), sep='\t')
        new_mapping_tsv = pd.read_csv(mapping_file_path, sep='\t')
        pd.testing.assert_frame_equal(old_mapping_tsv, new_mapping_tsv)

    @patch('nmdc_automation.jgi_file_staging.mapping_tsv.get_request')
    @patch('nmdc_automation.jgi_file_staging.mapping_tsv.get_access_token')
    @mongomock.patch(servers=(('localhost', 27017),))
    def test_create_metat_mapping_tsv(self, mock_token, mock_get_request):
        self.insert_sequencing_project()
        gold_id_response = {'resources': [{'add_date': '2017-08-18',
                                           'analyte_category': 'metagenome',
                                           'associated_studies': ['nmdc:sty-11-8ws97026'],
                                           'gold_sequencing_project_identifiers': ['gold:Gp0225778'],
                                           'has_input': ['nmdc:bsm-11-622k6044'],
                                           'id': 'nmdc:dgns-11-0g2bvk46',
                                           'instrument_used': ['nmdc:inst-14-nn4b6k72']},
                                          {'add_date': '2017-10-23',
                                           'analyte_category': 'metatranscriptome',
                                           'associated_studies': ['nmdc:sty-11-8ws97026'],
                                           'gold_sequencing_project_identifiers': ['gold:Gp0255830'],
                                           'has_input': ['nmdc:bsm-11-622k6044'],
                                           'id': 'nmdc:dgns-11-yqheg664',
                                           'instrument_used': ['nmdc:inst-14-nn4b6k72']}]}
        gold_project_response1 = '''[{"apGoldId": "Ga0210394", "organismGoldId": null, "referenceApGoldId": null, 
        "apType": "Metagenome Analysis", "studyId": "Gs0130354", "itsApId": 1159545, "projects": ["Gp0225778"]}, 
        {"apGoldId": "Ga0505706", "organismGoldId": null, "referenceApGoldId": null, "apType": "Combined Assembly", 
        "studyId": "Gs0130354", "itsApId": 1343191, "projects": ["Gp0225773", "Gp0225794", "Gp0225772", "Gp0225775", 
        "Gp0225774", "Gp0225791", "Gp0225790", "Gp0225771", "Gp0225793", "Gp0225792", "Gp0225770", "Gp0225777", 
        "Gp0225776", "Gp0225779", "Gp0225778", "Gp0225784", "Gp0225783", "Gp0225786", "Gp0225785", "Gp0225780", 
        "Gp0225782", "Gp0225781", "Gp0225769", "Gp0225788", "Gp0225787", "Gp0225768", "Gp0225789", "Gp0225767"]}]'''
        gold_project_response2 = '''[{"apGoldId": "Ga0222738", "organismGoldId": null, "referenceApGoldId": null, 
        "apType": "Metatranscriptome Analysis", "studyId": "Gs0130354", "itsApId": 1167968, "projects": ["Gp0255830"]}, 
        {"apGoldId": "Ga0224388", "organismGoldId": null, "referenceApGoldId": "Ga0222738", "apType": 
        "Metatranscriptome mapping (self)", "studyId": "Gs0130354", "itsApId": 1167969, "projects": ["Gp0255830"]}, 
        {"apGoldId": "Ga0242657", "organismGoldId": null, "referenceApGoldId": null, "apType": 
        "Metatranscriptome Analysis", "studyId": "Gs0130354", "itsApId": 1187601, "projects": ["Gp0255830"]}, 
        {"apGoldId": "Ga0244753", "organismGoldId": null, "referenceApGoldId": "Ga0242657", "apType": 
        "Metatranscriptome mapping (self)", "studyId": "Gs0130354", "itsApId": 1187602, "projects": ["Gp0255830"]}]'''
        mock_get_request.side_effect = [gold_id_response, json.loads(gold_project_response1),
                                        json.loads(gold_project_response2)]
        mapping_path = Path(self.fixtures, 'test_project')
        metag_mapping_file_path = mapping_path / 'bioscales.metag.map.tsv'
        metat_mapping_file_path = mapping_path / 'bioscales.metat.map.tsv'
        mdb = get_test_db()
        create_mapping_tsv('bioscales', mapping_path, mdb,  'nmdc:sty-11-r2h77870')
        self.assertTrue(metat_mapping_file_path.exists())
        self.assertTrue(metag_mapping_file_path.exists())

    @mongomock.patch(servers=(('localhost', 27017),))
    def test_create_tsv_file(self):
        self.insert_sequencing_project()


if __name__ == '__main__':
    unittest.main()
