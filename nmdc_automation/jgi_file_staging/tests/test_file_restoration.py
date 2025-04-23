import unittest
import os
from unittest.mock import patch, Mock
import mongomock
import pandas as pd
import configparser

from file_restoration import restore_files, update_file_statuses, update_sample_in_mongodb, check_restore_status
from mongo import get_mongo_db
from jgi_file_metadata import insert_samples_into_mongodb


class FileRestoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixtures = os.path.join(os.path.dirname(__file__), 'fixtures')
        self.config_file = os.path.join(self.fixtures, 'config.ini')

    def tearDown(self) -> None:
        mdb = get_mongo_db()
        mdb.samples.drop()
        mdb.globus.drop()

    @patch('file_restoration.update_file_statuses')
    @patch('jgi_file_metadata.requests.post')
    @mongomock.patch(servers=(('localhost', 27017),))
    def test_restore_files(self, mock_post, mock_update):
        # mock API call for file restore request
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'updated_count': 0, 'restored_count': 4, 'request_id': 220699, 'request_status_url':
                'https://files.jgi.doe.gov/request_archived_files/requests/220699'}

        # insert samples into database
        grow_analysis_df = pd.read_csv(os.path.join(self.fixtures, 'grow_analysis_projects.csv'))
        grow_analysis_df.columns = ['apGoldId', 'studyId', 'itsApId', 'projects', 'biosample_id', 'seq_id', 'file_name',
                                    'file_status', 'file_size', 'jdp_file_id', 'md5sum', 'analysis_project_id']
        grow_analysis_df = grow_analysis_df[['apGoldId', 'studyId', 'itsApId', 'biosample_id', 'seq_id',
                                             'file_name', 'file_status', 'file_size', 'jdp_file_id', 'md5sum',
                                             'analysis_project_id']]
        grow_analysis_df['project'] = "test_project"
        grow_analysis_df['analysis_project_id'] = grow_analysis_df['analysis_project_id'].apply(lambda x: str(x))
        grow_analysis_df.loc[grow_analysis_df['file_size'] > 30000, 'file_status'] = 'PURGED'
        insert_samples_into_mongodb(grow_analysis_df.to_dict('records'))
        mdb = get_mongo_db()
        num_restore_samples = len([m for m in mdb.samples.find({'file_status': 'PURGED'})])
        self.assertEqual(num_restore_samples, 5)
        output = restore_files('test_project', self.config_file)
        self.assertEqual(output, f"requested restoration of 5 files")
        num_restore_samples = len([m for m in mdb.samples.find({'file_status': 'PURGED'})])
        self.assertEqual(num_restore_samples, 0)
        samples = [s for s in mdb.samples.find({})]
        self.assertEqual(samples[3]['request_id'], 220699)
        self.assertEqual(samples[0]['request_id'], None)

    @patch('file_restoration.update_file_statuses')
    @patch('jgi_file_metadata.requests.post')
    @mongomock.patch(servers=(('localhost', 27017),))
    def test_restore_files_exceed_max(self, mock_post, mock_update):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'updated_count': 0, 'restored_count': 4, 'request_id': 220699, 'request_status_url':
                'https://files.jgi.doe.gov/request_archived_files/requests/220699'}

        grow_analysis_df = pd.read_csv(os.path.join(self.fixtures, 'grow_analysis_projects.csv'))
        grow_analysis_df.columns = ['apGoldId', 'studyId', 'itsApId', 'projects', 'biosample_id', 'seq_id', 'file_name',
                                    'file_status', 'file_size', 'jdp_file_id', 'md5sum', 'analysis_project_id']
        grow_analysis_df = grow_analysis_df[['apGoldId', 'studyId', 'itsApId', 'biosample_id', 'seq_id',
                                             'file_name', 'file_status', 'file_size', 'jdp_file_id', 'md5sum',
                                             'analysis_project_id']]
        grow_analysis_df.loc[grow_analysis_df['file_size'] > 30000, 'file_status'] = 'PURGED'
        grow_analysis_df.loc[grow_analysis_df['jdp_file_id'] == '61a9d6f18277d7ede604d116', 'file_size'] = \
            8012231300000000
        grow_analysis_df['project'] = 'test_project'
        insert_samples_into_mongodb(grow_analysis_df.to_dict('records'))
        output = restore_files('test_project', self.config_file)
        self.assertEqual(output, f"requested restoration of 0 files")

    @patch('file_restoration.update_file_statuses')
    @patch('jgi_file_metadata.requests.post')
    @mongomock.patch(servers=(('localhost', 27017),))
    def test_restore_files_invalid_status_code(self, mock_post, mock_update):
        mock_post.return_value.status_code = 401
        mock_post.return_value.text = {"detail": "Authentication credentials were not provided."}
        grow_analysis_df = pd.read_csv(os.path.join(self.fixtures, 'grow_analysis_projects.csv'))
        grow_analysis_df.columns = ['apGoldId', 'studyId', 'itsApId', 'projects', 'biosample_id', 'seq_id', 'file_name',
                                    'file_status', 'file_size', 'jdp_file_id', 'md5sum', 'analysis_project_id']
        grow_analysis_df = grow_analysis_df[['apGoldId', 'studyId', 'itsApId', 'biosample_id', 'seq_id',
                                             'file_name', 'file_status', 'file_size', 'jdp_file_id', 'md5sum',
                                             'analysis_project_id']]
        grow_analysis_df.loc[grow_analysis_df['file_size'] > 30000, 'file_status'] = 'PURGED'
        grow_analysis_df['project'] = 'test_project'
        insert_samples_into_mongodb(grow_analysis_df.to_dict('records'))
        output = restore_files('test_project', self.config_file)
        self.assertEqual(output, {"detail": "Authentication credentials were not provided."})

    @patch('jgi_file_metadata.requests.get')
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

    @patch('jgi_file_metadata.requests.get')
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
        insert_samples_into_mongodb(grow_analysis_df.to_dict('records'))
        config = configparser.ConfigParser()
        config.read(self.config_file)
        update_file_statuses('test_project', self.config_file)
        mdb = get_mongo_db()
        samples = [s for s in mdb.samples.find({'file_status': 'pending'})]
        self.assertEqual(len(samples), 5)
        self.assertEqual(samples[0]['file_name'], 'Ga0499978_proteins.supfam.domtblout')

    @patch('jgi_file_metadata.requests.get')
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
        mdb = get_mongo_db()
        samples = [s for s in mdb.samples.find({'file_status': 'pending'})]
        self.assertEqual(len(samples), 0)


if __name__ == '__main__':
    unittest.main()
