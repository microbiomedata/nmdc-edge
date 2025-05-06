import ast
import unittest
import os
from unittest.mock import patch
import mongomock
import pandas as pd
import configparser

from nmdc_automation.jgi_file_staging.file_restoration import restore_files, update_file_statuses, check_restore_status
from nmdc_automation.jgi_file_staging.jgi_file_metadata import sample_records_to_sample_objects



class FileRestoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixtures = os.path.join(os.path.dirname(__file__), 'fixtures')
        self.config_file = os.path.join(self.fixtures, 'config.ini')
        self.db = get_db()





    @patch('nmdc_automation.jgi_file_staging.jgi_file_metadata.requests.get')
    @mongomock.patch(servers=(('localhost', 27017),))
    def test_check_restore_status(self, mock_get):
        config = configparser.ConfigParser()
        config.read(self.config_file)
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'file_ids': ['6119a224cf09c8006854d171'], 'status': 'pending',
                                                   'expiration_date': '2023-05-18T14:55:41.475890-07:00'}
        response = check_restore_status(220699, config)
        self.assertEqual(response['status'], 'pending')
        self.assertEqual(response['expiration_date'], '2023-05-18T14:55:41.475890-07:00')
        self.assertEqual(response['file_ids'], ['6119a224cf09c8006854d171'])

        mock_get.return_value.status_code = 401
        mock_get.return_value.text = {"detail": "Authentication credentials were not provided."}
        response = check_restore_status(220699, config)
        self.assertEqual(response, None)

    @patch('nmdc_automation.jgi_file_staging.jgi_file_metadata.requests.get')
    @mongomock.patch(servers=(('localhost', 27017),))
    def test_update_file_status(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'file_ids': ['61a9d6ef8277d7ede604d105', '61a9d6ef8277d7ede604d0f8',
                                                                '61a9d6ef8277d7ede604d101', '61a9d6f18277d7ede604d116',
                                                                '619d6f9850d56abc0a99a4f4'], 'status': 'pending',
                                                   'expiration_date': '2023-05-18T14:55:41.475890-07:00'}

        grow_analysis_df = pd.read_csv(os.path.join(self.fixtures, 'grow_analysis_projects.csv'))
        grow_analysis_df.columns = ['apGoldId', 'studyId', 'itsApId', 'projects', 'biosample_id', 'seq_id', 'file_name',
                                    'file_status', 'file_size', 'jdp_file_id', 'md5sum', 'analysis_project_id']
        grow_analysis_df = grow_analysis_df[['apGoldId', 'studyId', 'itsApId', 'biosample_id', 'seq_id',
                                             'file_name', 'file_status', 'file_size', 'jdp_file_id', 'md5sum',
                                             'analysis_project_id']]
        grow_analysis_df.loc[grow_analysis_df['file_size'] > 30000, 'file_status'] = 'pending'
        grow_analysis_df['project'] = 'test_project'
        sample_objects = sample_records_to_sample_objects(grow_analysis_df.to_dict('records'))
        config = configparser.ConfigParser()
        config.read(self.config_file)
        update_file_statuses('test_project', self.config_file)
        mdb = get_db()
        samples = [s for s in mdb.samples.find({'file_status': 'pending'})]
        self.assertEqual(len(samples), 5)
        self.assertEqual(samples[0]['file_name'], 'Ga0499978_proteins.supfam.domtblout')

    @patch('nmdc_automation.jgi_file_staging.jgi_file_metadata.requests.get')
    @mongomock.patch(servers=(('localhost', 27017),))
    def test_update_file_status_no_samples_to_restore(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'file_ids': ['61a9d6ef8277d7ede604d105', '61a9d6ef8277d7ede604d0f8',
                                                                '61a9d6ef8277d7ede604d101', '61a9d6f18277d7ede604d116',
                                                                '619d6f9850d56abc0a99a4f4'], 'status': 'pending',
                                                   'expiration_date': '2023-05-18T14:55:41.475890-07:00'}

        grow_analysis_df = pd.read_csv(os.path.join(self.fixtures, 'grow_analysis_projects.csv'))
        grow_analysis_df.columns = ['apGoldId', 'studyId', 'itsApId', 'projects', 'biosample_id', 'seq_id', 'file_name',
                                    'file_status', 'file_size', 'jdp_file_id', 'md5sum', 'analysis_project_id']
        grow_analysis_df = grow_analysis_df[['apGoldId', 'studyId', 'itsApId', 'biosample_id', 'seq_id',
                                             'file_name', 'file_status', 'file_size', 'jdp_file_id', 'md5sum',
                                             'analysis_project_id']]
        grow_analysis_df['project'] = 'test_project'
        insert_samples_into_mongodb(grow_analysis_df.to_dict('records'))
        config = configparser.ConfigParser()
        config.read(self.config_file)
        update_file_statuses('test_project', self.config_file)
        mdb = get_db()
        samples = [s for s in mdb.samples.find({'file_status': 'pending'})]
        self.assertEqual(len(samples), 0)


if __name__ == '__main__':
    unittest.main()
