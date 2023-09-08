import unittest
import os
from unittest.mock import patch, Mock
import mongomock
import json
import pymongo
import yaml
import pandas as pd
import configparser
import sys
from datetime import datetime
from jgi_file_metadata import get_access_token, check_access_token, get_analysis_projects_from_proposal_id, \
    get_sample_files, get_sequence_id, insert_samples_into_mongodb, get_mongo_db, get_files_and_agg_ids, \
    combine_sample_ids_with_agg_ids, remove_unneeded_files, get_samples_data, remove_duplicate_analysis_files, \
    remove_large_files, get_seq_unit_names
from file_restoration import update_sample_in_mongodb


class JgiFileTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.fixtures = os.path.join(os.path.dirname(__file__), 'fixtures')
        self.config_file = os.path.join(self.fixtures, 'config.ini')
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(self.config_file)
        self.config = config

    def tearDown(self) -> None:
        mdb = get_mongo_db()
        mdb.samples.drop()
        mdb.globus.drop()

    @patch('jgi_file_metadata.requests.get')
    def test_get_access_token(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = "ed42ef1556708305eaf8"
        ACCESS_TOKEN = get_access_token()
        self.assertEqual(ACCESS_TOKEN, "ed42ef1556708305eaf8")

    @patch('jgi_file_metadata.requests.get')
    def test_check_access_token(self, mock_get):
        mock_get.return_value.status_code = 200
        ACCESS_TOKEN = "ed42ef1556708305eaf8"
        ACCESS_TOKEN = check_access_token(ACCESS_TOKEN, eval(self.config['JDP']['delay']))
        self.assertEqual(ACCESS_TOKEN, "ed42ef1556708305eaf8")

    @patch('jgi_file_metadata.requests.get')
    def test_check_access_token_invalid(self, mock_get):
        response_mock1 = Mock()
        response_mock1.status_code = 400
        response_mock1.text = "ed42ef1556"
        response_mock2 = Mock()
        response_mock2.status_code = 200
        response_mock2.text = "ed42ef155670"
        mock_get.side_effect = [response_mock1, response_mock2]

        ACCESS_TOKEN = "ed42ef1556708305eaf8"
        ACCESS_TOKEN = check_access_token(ACCESS_TOKEN, eval(self.config['JDP']['delay']))
        self.assertEqual(ACCESS_TOKEN, "ed42ef155670")

    @patch('jgi_file_metadata.requests.get')
    def test_get_sequence_id(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [{'itsSpid': 1323348}]
        sequence_id = get_sequence_id('Ga0499978', "ed42ef155670", eval(self.config['JDP']['delay']))
        self.assertEqual(sequence_id, 1323348)

        mock_get.return_value.status_code = 403
        sequence_id = get_sequence_id('Ga0499978', "ed42ef155670", eval(self.config['JDP']['delay']))
        self.assertEqual(sequence_id, None)

    @patch('jgi_file_metadata.requests.get')
    def test_get_analysis_projects_from_proposal_id(self, mock_get):
        mock_get.return_value.json.return_value = pd.read_csv(
            os.path.join(self.fixtures, 'grow_gold_analysis_projects.csv')).to_dict('records')
        gold_analysis_data = get_analysis_projects_from_proposal_id('11111', 'ed42ef155670')
        self.assertEqual(gold_analysis_data[0], {'apGoldId': 'Ga0499978', 'apType': 'Metagenome Analysis', 'studyId': 'Gs0149396', 'itsApId': 1323348,
                                                 'projects': "['Gp0587070']"})
        self.assertEqual(gold_analysis_data[5], {'apGoldId': 'Ga0451723', 'apType': 'Metagenome Analysis', 'studyId': 'Gs0149396', 'itsApId': 1279803,
                                                 'projects': "['Gp0503551']"})

    @mongomock.patch(servers=(('localhost', 27017),))
    def test_insert_samples_into_mongodb(self):
        grow_analysis_df = pd.read_csv(os.path.join(self.fixtures, 'grow_analysis_projects.csv'))
        grow_analysis_df.columns = ['apGoldId', 'studyId', 'itsApId', 'projects', 'biosample_id', 'seq_id', 'file_name',
                                    'file_status', 'file_size', 'jdp_file_id', 'md5sum', 'analysis_project_id']
        grow_analysis_df = grow_analysis_df[['apGoldId', 'studyId', 'itsApId', 'biosample_id', 'seq_id',
                                             'file_name', 'file_status', 'file_size', 'jdp_file_id', 'md5sum',
                                             'analysis_project_id']]
        grow_analysis_df['project'] = 'test_project'
        insert_samples_into_mongodb(grow_analysis_df.to_dict('records'))
        mdb = get_mongo_db()
        sample = mdb.samples.find_one({'apGoldId': 'Ga0499978'})
        self.assertEqual(sample['studyId'], 'Gs0149396')
        sample = mdb.samples.find_one({'jdp_file_id': '61a9d6ee8277d7ede604d0f6'})
        self.assertEqual(sample['file_name'], 'Ga0499978_imgap.info')
        self.assertEqual(sample['file_status'], 'RESTORED')

    @mongomock.patch(servers=(('localhost', 27017),))
    def test_insert_samples_into_mongodb_fail_valid(self):
        grow_analysis_df = pd.read_csv(os.path.join(self.fixtures, 'grow_analysis_projects.csv'))
        grow_analysis_df.columns = ['apGoldId', 'studyId', 'itsApId', 'projects', 'biosample_id', 'seq_id', 'file_name',
                                    'file_status', 'file_size', '_id', 'md5sum', 'analysis_project_id']
        grow_analysis_df = grow_analysis_df[['apGoldId', 'studyId', 'itsApId', 'biosample_id', 'seq_id',
                                             'file_name', 'file_status', 'file_size', '_id', 'md5sum',
                                             'analysis_project_id']]
        grow_analysis_df['project'] = 'test_project'
        insert_samples_into_mongodb(grow_analysis_df.to_dict('records'))
        mdb = get_mongo_db()
        sample = mdb.samples.find_one({'apGoldId': 'Ga0499978'})
        self.assertEqual(sample, None)

    @mongomock.patch(servers=(('localhost', 27017),))
    def test_update_samples_in_mongodb(self):
        grow_analysis_df = pd.read_csv(os.path.join(self.fixtures, 'grow_analysis_projects.csv'))
        grow_analysis_df.columns = ['apGoldId', 'studyId', 'itsApId', 'projects', 'biosample_id', 'seq_id', 'file_name',
                                    'file_status', 'file_size', 'jdp_file_id', 'md5sum', 'analysis_project_id']
        grow_analysis_df = grow_analysis_df[['apGoldId', 'studyId', 'itsApId', 'biosample_id', 'seq_id',
                                             'file_name', 'file_status', 'file_size', 'jdp_file_id', 'md5sum',
                                             'analysis_project_id']]
        grow_analysis_df['project'] = 'test_project'
        insert_samples_into_mongodb(grow_analysis_df.to_dict('records'))
        mdb = get_mongo_db()
        sample = mdb.samples.find_one({'jdp_file_id': '6190d7d30de2fc3298da6f7a'})
        update_sample_in_mongodb(sample, {'file_status': 'RESTORE_IN_PROGRESS', 'request_id': 217934})
        updated_sample = mdb.samples.find_one(sample)
        self.assertEqual(updated_sample['file_status'], 'RESTORE_IN_PROGRESS')
        self.assertEqual(updated_sample['request_id'], 217934)

        sample = mdb.samples.find_one({'jdp_file_id': '6190d7d30de2fc3298da6f7a'})
        sample.pop('file_name')
        success = update_sample_in_mongodb(sample, {'file_status': 'RESTORE_IN_PROGRESS', 'request_id': 217934})
        self.assertFalse(success)

    @patch('jgi_file_metadata.requests.get')
    def test_get_files_and_agg_ids(self, mock_get):
        with open(os.path.join(self.fixtures, 'files_data.json'), 'r') as f:
            files_json = json.load(f)
        mock_get.return_value.json.return_value = files_json
        mock_get.return_value.status_code = 200
        files_dict, agg_id_list = get_files_and_agg_ids(1323459, 'ed42ef155670')
        self.assertEqual(files_dict[0][0]['file_name'], 'Table_8_-_3300049478.taxonomic_composition.txt')
        self.assertEqual(files_dict[0][0]['file_type'], 'report')
        self.assertEqual(agg_id_list[0], 1323348)

    @patch('jgi_file_metadata.requests.get')
    def test_get_files_and_agg_ids_no_organisms(self, mock_get):
        with open(os.path.join(self.fixtures, 'files_data.json'), 'r') as f:
            files_json = json.load(f)
        files_json.pop('organisms')
        mock_get.return_value.json.return_value = files_json
        mock_get.return_value.status_code = 200
        files_dict, agg_id_list = get_files_and_agg_ids(1323459, 'ed42ef155670')
        self.assertEqual(files_dict, None)
        self.assertEqual(agg_id_list, [])

    @patch('jgi_file_metadata.get_files_and_agg_ids')
    @patch('jgi_file_metadata.requests.get')
    @patch('jgi_file_metadata.get_access_token')
    def test_get_sample_files(self, mock_token, mock_get, mock_get_files_list):
        with open(os.path.join(self.fixtures, 'files_data.json'), 'r') as f:
            files_json = json.load(f)
        files_data_list = []
        agg_id_list = []
        for org in files_json['organisms']:
            files_data_list.append(org['files'])
            agg_id_list.append(org['agg_id'])
        mock_get_files_list.return_value = (files_data_list, [1295131, 1309801])
        mock_token.return_value = "ed42ef155670"
        mock_get.return_value.json.return_value = [{'itsSpid': 1323348}]
        mock_get.return_value.status_code = 200
        grow_samples = get_sample_files(os.path.join(self.fixtures, 'grow_samples.txt'), 'ed42ef155670',
                                        eval(self.config['JDP']['delay']))
        self.assertEqual(grow_samples[0]['file_name'], 'Table_8_-_3300049478.taxonomic_composition.txt')

    @patch('jgi_file_metadata.get_files_and_agg_ids')
    @patch('jgi_file_metadata.requests.get')
    @patch('jgi_file_metadata.get_access_token')
    def test_remove_large_files(self, mock_token, mock_get, mock_get_files_list):
        with open(os.path.join(self.fixtures, 'seq_files_df.json'), 'r') as f:
            files_data_list = json.load(f)
        seq_files_df = pd.DataFrame(files_data_list)
        self.assertFalse(seq_files_df[seq_files_df.file_name == 'Ga0451670_proteins.img_nr.last.blasttab'].empty)
        self.assertFalse(seq_files_df[seq_files_df.file_name == 'Ga0451670_proteins.supfam.domtblout'].empty)
        seq_files_df = remove_large_files(seq_files_df, ['img_nr.last.blasttab', 'domtblout'])
        self.assertEqual(len(seq_files_df), 71)
        self.assertTrue(seq_files_df[seq_files_df.file_name == 'Ga0451670_proteins.img_nr.last.blasttab'].empty)
        self.assertTrue(seq_files_df[seq_files_df.file_name == 'Ga0451670_proteins.supfam.domtblout'].empty)

    def test_get_seq_unit_names(self):
        seq_files_df = pd.read_csv(os.path.join(self.fixtures, 'seq_unit_names_df.csv'))
        seq_unit_names = get_seq_unit_names(seq_files_df, 'Ga0451670')
        self.assertEqual(seq_unit_names, ['52444.3.336346.GAGCTCAA-GAGCTCAA'])

    def test_remove_duplicate_analysis_files(self):
        seq_files_df = pd.read_csv(os.path.join(self.fixtures, 'seq_unit_names_df.csv'))
        self.assertFalse(seq_files_df[seq_files_df.file_name == '52554.2.382557.CCCTGTAT-GGATAACG.fastq.gz'].empty)
        grow_samples_df = remove_duplicate_analysis_files(seq_files_df)
        self.assertTrue(grow_samples_df[grow_samples_df.file_name == '52554.2.382557.CCCTGTAT-GGATAACG.fastq.gz'].empty)

    @patch('jgi_file_metadata.get_files_and_agg_ids')
    @patch('jgi_file_metadata.requests.get')
    @patch('jgi_file_metadata.get_access_token')
    def test_remove_unneeded_files(self, mock_token, mock_get, mock_get_files_list):
        seq_files_df = pd.read_csv(os.path.join(self.fixtures, 'seq_unit_names_df.csv'))

        self.assertFalse(seq_files_df[seq_files_df.file_name == '52554.2.382557.CCCTGTAT-GGATAACG.fastq.gz'].empty)
        self.assertFalse(seq_files_df[seq_files_df.file_name == 'Ga0451670_proteins.img_nr.last.blasttab'].empty)
        grow_samples_df = remove_unneeded_files(seq_files_df, ['img_nr.last.blasttab', 'domtblout'])
        self.assertEqual(len(grow_samples_df), 70)
        self.assertTrue(grow_samples_df[grow_samples_df.file_name == '52554.2.382557.CCCTGTAT-GGATAACG.fastq.gz'].empty)
        self.assertTrue(grow_samples_df[grow_samples_df.file_name == 'Ga0451670_proteins.img_nr.last.blasttab'].empty)

    def test_combine_sample_ids_with_agg_ids(self):
        with open(os.path.join(self.fixtures, 'files_data.json'), 'r') as f:
            files_json = json.load(f)
        files_data_list = []
        agg_id_list = []
        if files_json['organisms']:
            for org in files_json['organisms']:
                files_data_list.append(org['files'])
                agg_id_list.append(org['agg_id'])
        all_files_list = []
        combine_sample_ids_with_agg_ids(files_data_list, agg_id_list, 'Gb0291644', 1310172, all_files_list)
        self.assertEqual(len(all_files_list), 85)
        self.assertEqual(all_files_list[0]['file_name'], 'Table_8_-_3300049478.taxonomic_composition.txt')
        self.assertEqual(all_files_list[0]['file_status'], 'PURGED')
        self.assertEqual(all_files_list[12]['md5sum'], 'c407751c775a82b72053b72532690e21')
        self.assertEqual(all_files_list[12]['file_size'], 965025)
        self.assertEqual(all_files_list[-1]['seq_id'], 1310172)
        self.assertEqual(all_files_list[-1]['jdp_file_id'], '61b40ec08277d7ede605605c')

    @patch('jgi_file_metadata.requests.get')
    @patch('jgi_file_metadata.get_sequence_id')
    @patch('jgi_file_metadata.check_access_token')
    @patch('jgi_file_metadata.get_access_token')
    @patch('jgi_file_metadata.get_analysis_projects_from_proposal_id')
    @mongomock.patch(servers=(('localhost', 27017),))
    def test_get_samples_data(self, mock_analysis_projects, mock_token, mock_check_token, mock_sequence_id, mock_get):
        with open(os.path.join(self.fixtures, 'gold_analysis_data.txt'), 'r') as f:
            files_json = json.load(f)
        mock_analysis_projects.return_value = files_json
        mock_token.return_value = "ed42ef155670"
        mock_check_token.return_value = "ed42ef155670"
        mock_sequence_id.return_value = 1323348
        with open(os.path.join(self.fixtures, 'files_data.json'), 'r') as f:
            files_json = json.load(f)
        mock_get.return_value.json.return_value = files_json
        mock_get.return_value.status_code = 200
        get_samples_data(os.path.join(self.fixtures, 'grow_samples.txt'), 505780, 'grow', self.config_file)
        mdb = get_mongo_db()
        sample = mdb.samples.find_one({'apGoldId': 'Ga0499978'})
        self.assertEqual(sample['studyId'], 'Gs0149396')


if __name__ == '__main__':
    unittest.main()
