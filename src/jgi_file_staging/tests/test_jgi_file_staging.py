import unittest
import os
from unittest.mock import patch, Mock
import mongomock
import json
import pymongo
import yaml
import pandas as pd
import configparser
from datetime import datetime
from src.jgi_file_staging import get_access_token, check_access_token, get_analysis_projects_from_proposal_id, \
    get_sample_files, get_sequence_id, insert_samples_into_mongodb, get_mongo_db, get_files_and_agg_ids, \
    combine_sample_ids_with_agg_ids, update_sample_in_mongodb, restore_files, check_restore_status, \
    get_globus_manifests, create_globus_batch_file, submit_globus_batch_file, update_file_statuses, \
    create_globus_dataframe, insert_globus_status_into_mongodb, update_globus_task_status, update_globus_statuses, \
    get_globus_task_status, remove_unneeded_files

from functools import wraps


def mock_decorator(*args, **kwargs):
    """Decorate by doing nothing."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            return f(*args, **kwargs)
        return decorated_function
    return decorator


patch('jgi_file_staging.click.command', mock_decorator).start()
patch('jgi_file_staging.click.argument', mock_decorator).start()
# patch('jgi_file_staging.cli.command', mock_decorator).start()
patch('jgi_file_staging.click.core', mock_decorator).start()


from jgi_file_staging import get_samples_data


class JgiFileTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.fixtures = os.path.join(os.path.dirname(__file__), 'fixtures')
        self.config_file = os.path.join(self.fixtures, 'config.ini')

    def tearDown(self) -> None:
        mdb = get_mongo_db()
        mdb.samples.drop()
        mdb.globus.drop()

    @patch('jgi_file_staging.requests.get')
    def test_get_access_token(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = "ed42ef1556708305eaf8"
        ACCESS_TOKEN = get_access_token()
        self.assertEqual(ACCESS_TOKEN, "ed42ef1556708305eaf8")

    @patch('jgi_file_staging.requests.get')
    def test_check_access_token(self, mock_get):
        mock_get.return_value.status_code = 200
        ACCESS_TOKEN = "ed42ef1556708305eaf8"
        ACCESS_TOKEN = check_access_token(ACCESS_TOKEN)
        self.assertEqual(ACCESS_TOKEN, "ed42ef1556708305eaf8")

    @patch('jgi_file_staging.requests.get')
    def test_check_access_token_invalid(self, mock_get):
        response_mock1 = Mock()
        response_mock1.status_code = 400
        response_mock1.text = "ed42ef1556"
        response_mock2 = Mock()
        response_mock2.status_code = 200
        response_mock2.text = "ed42ef155670"
        mock_get.side_effect = [response_mock1, response_mock2]

        ACCESS_TOKEN = "ed42ef1556708305eaf8"
        ACCESS_TOKEN = check_access_token(ACCESS_TOKEN)
        self.assertEqual(ACCESS_TOKEN, "ed42ef155670")

    @patch('jgi_file_staging.requests.get')
    def test_get_sequence_id(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [{'itsSpid': 1323348}]
        sequence_id = get_sequence_id('Ga0499978', "ed42ef155670")
        self.assertEqual(sequence_id, 1323348)

        mock_get.return_value.status_code = 403
        sequence_id = get_sequence_id('Ga0499978', "ed42ef155670")
        self.assertEqual(sequence_id, None)

    @patch('jgi_file_staging.requests.get')
    def test_get_analysis_projects_from_proposal_id(self, mock_get):
        mock_get.return_value.json.return_value = pd.read_csv(
            os.path.join(self.fixtures, 'grow_gold_analysis_projects.csv')).to_dict('records')
        gold_analysis_data = get_analysis_projects_from_proposal_id('11111', 'ed42ef155670')
        self.assertEqual(gold_analysis_data[0], {'apGoldId': 'Ga0499978', 'studyId': 'Gs0149396', 'itsApId': 1323348,
                                                 'projects': "['Gp0587070']"})
        self.assertEqual(gold_analysis_data[5], {'apGoldId': 'Ga0451723', 'studyId': 'Gs0149396', 'itsApId': 1279803,
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

        success = update_sample_in_mongodb(sample, {'request_id': '21793b4'})
        self.assertFalse(success)

        sample = mdb.samples.find_one({'jdp_file_id': '6190d7d30de2fc3298da6f7a'})
        sample.pop('file_name')
        success = update_sample_in_mongodb(sample, {'file_status': 'RESTORE_IN_PROGRESS', 'request_id': 217934})
        self.assertFalse(success)

    @patch('jgi_file_staging.requests.get')
    def test_get_files_and_agg_ids(self, mock_get):
        with open(os.path.join(self.fixtures, 'files_data.json'), 'r') as f:
            files_json = json.load(f)
        mock_get.return_value.json.return_value = files_json
        mock_get.return_value.status_code = 200
        files_dict, agg_id_list = get_files_and_agg_ids(1323459, 'ed42ef155670')
        self.assertEqual(files_dict[0][0]['file_name'], 'Table_8_-_3300049478.taxonomic_composition.txt')
        self.assertEqual(files_dict[0][0]['file_type'], 'report')
        self.assertEqual(agg_id_list[0], 1323348)

    @patch('jgi_file_staging.requests.get')
    def test_get_files_and_agg_ids_no_organisms(self, mock_get):
        with open(os.path.join(self.fixtures, 'files_data.json'), 'r') as f:
            files_json = json.load(f)
        files_json.pop('organisms')
        mock_get.return_value.json.return_value = files_json
        mock_get.return_value.status_code = 200
        files_dict, agg_id_list = get_files_and_agg_ids(1323459, 'ed42ef155670')
        self.assertEqual(files_dict, None)
        self.assertEqual(agg_id_list, [])

    @patch('jgi_file_staging.get_files_and_agg_ids')
    @patch('jgi_file_staging.requests.get')
    @patch('jgi_file_staging.get_access_token')
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
        grow_samples = get_sample_files(os.path.join(self.fixtures, 'grow_samples.txt'), 'ed42ef155670')
        self.assertEqual(grow_samples[0]['file_name'], 'Table_8_-_3300049478.taxonomic_composition.txt')

    @patch('jgi_file_staging.get_files_and_agg_ids')
    @patch('jgi_file_staging.requests.get')
    @patch('jgi_file_staging.get_access_token')
    def test_remove_unneeded_files(self, mock_token, mock_get, mock_get_files_list):
        with open(os.path.join(self.fixtures, 'seq_files_df.json'), 'r') as f:
            files_data_list = json.load(f)

        seq_files_df = pd.DataFrame(files_data_list)
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
        self.assertEqual(len(all_files_list), 86)
        self.assertEqual(all_files_list[0]['file_name'], 'Table_8_-_3300049478.taxonomic_composition.txt')
        self.assertEqual(all_files_list[0]['file_status'], 'PURGED')
        self.assertEqual(all_files_list[12]['md5sum'], 'c407751c775a82b72053b72532690e21')
        self.assertEqual(all_files_list[12]['file_size'], 965025)
        self.assertEqual(all_files_list[-1]['seq_id'], 1310172)
        self.assertEqual(all_files_list[-1]['jdp_file_id'], '61b40ec08277d7ede605605c')

    @patch('jgi_file_staging.requests.get')
    @patch('jgi_file_staging.get_sequence_id')
    @patch('jgi_file_staging.check_access_token')
    @patch('jgi_file_staging.get_access_token')
    @patch('jgi_file_staging.get_analysis_projects_from_proposal_id')
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




    @patch('jgi_file_staging.update_file_statuses')
    @patch('jgi_file_staging.requests.post')
    @mongomock.patch(servers=(('localhost', 27017),))
    def test_restore_files(self, mock_post, mock_update):
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
        grow_analysis_df['project'] = 'test_project'
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

    @patch('jgi_file_staging.update_file_statuses')
    @patch('jgi_file_staging.requests.post')
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

    @patch('jgi_file_staging.update_file_statuses')
    @patch('jgi_file_staging.requests.post')
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

    @patch('jgi_file_staging.requests.get')
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

    @patch('jgi_file_staging.requests.get')
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
        update_file_statuses('test_project', config)
        mdb = get_mongo_db()
        samples = [s for s in mdb.samples.find({'file_status': 'pending'})]
        self.assertEqual(len(samples), 5)
        self.assertEqual(samples[0]['file_name'], 'Ga0499978_proteins.supfam.domtblout')

    @patch('jgi_file_staging.subprocess.run')
    def test_get_globus_manifests(self, mock_run):
        attrs = {'stdout': "R201545/\n, R201547/\n, R201572/\n", 'returncode': 0}
        process_mock = Mock()
        process_mock.configure_mock(**attrs)
        process_mock_2 = Mock()
        attrs = {'stdout': "ERLowmetatpilot/\nGlobus_Download_201670_File_Manifest.csv\n", 'returncode': 0}
        process_mock_2.configure_mock(**attrs)
        process_mock_3 = Mock()
        attrs = {'stdout': "", 'returncode': 0}
        process_mock_3.configure_mock(**attrs)

        process_mock_4 = Mock()
        attrs = {'stdout': "NGESur0720SPAdes_8/\nRivsedcS19S_0091_2/\naugS19MG/\nblaS19MG_2/\ncacS19MG/\ncarS19MG/"
                           "\ncobS19MG/\ncolS19MG_3/\ncolS19MG_5/\ngorS19MG/\nlitS19MG/\nlogS19MG/\nlowS19MG/\n"
                           "redS19MG/\nsawS19MG/\nshaS19MG_3/\nwatS19MG/\nwatS19MG_2/\n"
                           "Globus_Download_201984_File_Manifest.csv", 'returncode': 0}
        process_mock_4.configure_mock(**attrs)
        process_mock_5 = Mock()
        attrs = {'stdout': "", 'returncode': 0}
        process_mock_5.configure_mock(**attrs)

        process_mock_6 = Mock()
        attrs = {'stdout': "ERLowmetatpilot/\nGlobus_Download_201670_File_Manifest.csv", 'returncode': 0}
        process_mock_6.configure_mock(**attrs)
        process_mock_7 = Mock()
        attrs = {'stdout': "", 'returncode': 0}
        process_mock_7.configure_mock(**attrs)

        mock_run.side_effect = [process_mock, process_mock_2, process_mock_3, process_mock_4, process_mock_5,
                                process_mock_6, process_mock_7]
        get_globus_manifests(self.config_file)
        self.assertEqual(mock_run.call_count, 7)
        self.assertEqual(mock_run.mock_calls[0].args[0], ['globus', 'ls',
                                                          '65fa2422-e080-11ec-990f-3b4cfda38030:/73709/'])

    def test_create_globus_df(self):
        globus_df = create_globus_dataframe(os.path.join(self.fixtures, 'globus_manifests'))
        self.assertEqual(len(globus_df), 76)
        self.assertEqual(globus_df.loc[0, 'directory/path'], 'ERLowmetatpilot/Sequencing_QC_Reports/Krona_output')
        self.assertEqual(globus_df.loc[0, 'filename'], 'cromwell_root.krona.ssu.html')
        self.assertEqual(globus_df.loc[0, 'file_id'], '6137c364cf09c800685690e0')
        self.assertEqual(globus_df.loc[0, 'subdir'], 'R201572')
        self.assertEqual(globus_df.loc[71, 'directory/path'], 'ERLowmetatpilot/IMG_Data')
        self.assertEqual(globus_df.loc[72, 'md5 checksum'], 'd8457dc907aed0ffe086a99bbbe44512')
        self.assertEqual(globus_df.loc[75, 'filename'], 'Ga0502004_genes.fna')
        self.assertEqual(globus_df.loc[75, 'subdir'], 'R201545')

    @mongomock.patch(servers=(('localhost', 27017),))
    def test_create_globus_batch_file(self):
        config = configparser.ConfigParser()
        config.read(self.config_file)
        grow_analysis_df = pd.read_csv(os.path.join(self.fixtures, 'grow_analysis_projects.csv'))
        grow_analysis_df.columns = ['apGoldId', 'studyId', 'itsApId', 'projects', 'biosample_id', 'seq_id', 'file_name',
                                    'file_status', 'file_size', 'jdp_file_id', 'md5sum', 'analysis_project_id']
        grow_analysis_df = grow_analysis_df[['apGoldId', 'studyId', 'itsApId', 'biosample_id', 'seq_id',
                                             'file_name', 'file_status', 'file_size', 'jdp_file_id', 'md5sum',
                                             'analysis_project_id']]
        grow_analysis_df.loc[grow_analysis_df['file_size'] > 30000, 'file_status'] = 'RESTORED'
        grow_analysis_df['project'] = 'test_project'
        insert_samples_into_mongodb(grow_analysis_df.to_dict('records'))
        try:
            globus_batch_filename, globus_analysis_df = create_globus_batch_file('test_project',
                                                                                 config)
            self.assertEqual(globus_batch_filename, 'test_project_globus_batch_file.txt')
            self.assertEqual(len(globus_analysis_df), 3)
            self.assertEqual(globus_analysis_df.loc[0, 'jdp_file_id'], '6190d7d30de2fc3298da6f7a')
            self.assertEqual(globus_analysis_df.loc[1, 'apGoldId'], 'Ga0499978')
            self.assertEqual(globus_analysis_df.loc[2, 'file_name'], 'Ga0499978_imgap.info')
            self.assertTrue(os.path.exists(globus_batch_filename))
        finally:
            os.remove('test_project_globus_batch_file.txt') if os.path.exists('test_project_globus_batch_file.txt') \
                else None

    @patch('jgi_file_staging.subprocess.run')
    @mongomock.patch(servers=(('localhost', 27017),))
    def test_submit_globus_batch_file(self, mock_run):
        attrs = {
            'stdout': "Message: The transfer has been accepted and a task has been created and queued for execution\n"
                      "Task ID: e5130cf8-ce5d-11ed-a9b9-63ca5f6c6821", 'returncode': 0}
        process_mock = Mock()
        process_mock.configure_mock(**attrs)
        mock_run.return_value = process_mock
        grow_analysis_df = pd.read_csv(os.path.join(self.fixtures, 'grow_analysis_projects.csv'))
        grow_analysis_df.columns = ['apGoldId', 'studyId', 'itsApId', 'projects', 'biosample_id', 'seq_id', 'file_name',
                                    'file_status', 'file_size', 'jdp_file_id', 'md5sum', 'analysis_project_id']
        grow_analysis_df = grow_analysis_df[['apGoldId', 'studyId', 'itsApId', 'biosample_id', 'seq_id',
                                             'file_name', 'file_status', 'file_size', 'jdp_file_id', 'md5sum',
                                             'analysis_project_id']]
        grow_analysis_df.loc[grow_analysis_df['file_size'] > 30000, 'file_status'] = 'RESTORED'
        grow_analysis_df['project'] = 'test_project'
        insert_samples_into_mongodb(grow_analysis_df.to_dict('records'))
        output = submit_globus_batch_file('test_project', self.config_file)
        mdb = get_mongo_db()
        samples = [s for s in mdb.samples.find({'file_status': 'transferring'})]
        self.assertEqual(len(samples), 3)
        self.assertEqual(
            output, "Message: The transfer has been accepted and a task has been created and queued for execution\n"
                    "Task ID: e5130cf8-ce5d-11ed-a9b9-63ca5f6c6821")

    @mongomock.patch(servers=(('localhost', 27017),))
    def test_insert_globus_status_into_mongodb(self):
        insert_globus_status_into_mongodb('e5130cf8-ce5d-11ed-a9b9-63ca5f6c6821', 'SUCCEEDED')
        mdb = get_mongo_db()
        task = mdb.globus.find_one({'task_id': 'e5130cf8-ce5d-11ed-a9b9-63ca5f6c6821'})
        self.assertEqual(task['task_status'], 'SUCCEEDED')

    @patch('jgi_file_staging.subprocess.run')
    def test_get_globus_task_status(self, mock_run):
        attrs = {
            'stdout': '''Label:                        None
Task ID:                      e5130cf8-ce5d-11ed-a9b9-63ca5f6c6821
Is Paused:                    False
Type:                         TRANSFER
Directories:                  0
Files:                        478
Status:                       SUCCEEDED
Request Time:                 2023-03-29T18:16:59+00:00
Faults:                       0
Total Subtasks:               956
Subtasks Succeeded:           956
Subtasks Pending:             0
Subtasks Retrying:            0
Subtasks Failed:              0
Subtasks Canceled:            0
Subtasks Expired:             0
Subtasks with Skipped Errors: 0
Completion Time:              2023-03-29T18:47:10+00:00
Source Endpoint:              JGI Genome Portal shared endpoint 3
Source Endpoint ID:           65fa2422-e080-11ec-990f-3b4cfda38030
Destination Endpoint:         NERSC nmdcda
Destination Endpoint ID:      ae777bc6-bf84-11ed-9917-cb2cff506ca5
Bytes Transferred:            673199360470
Bytes Per Second:             371815009''', 'returncode': 0}
        process_mock = Mock()
        process_mock.configure_mock(**attrs)
        mock_run.return_value = process_mock
        output = get_globus_task_status('e5130cf8-ce5d-11ed-a9b9-63ca5f6c6821')
        self.assertEqual(output, 'SUCCEEDED')

    @patch('jgi_file_staging.subprocess.run')
    def test_update_globus_statuses(self, mock_run):
        attrs = {
            'stdout': '''Label:                        None
        Task ID:                      63ca5f-ce5d-11ed-a9b9-6c6821-e5130cf8
        Is Paused:                    False
        Type:                         TRANSFER
        Directories:                  0
        Files:                        478
        Status:                       SUCCEEDED
        Request Time:                 2023-03-29T18:16:59+00:00
        Faults:                       0
        Total Subtasks:               956
        Subtasks Succeeded:           956
        Subtasks Pending:             0
        Subtasks Retrying:            0
        Subtasks Failed:              0
        Subtasks Canceled:            0
        Subtasks Expired:             0
        Subtasks with Skipped Errors: 0
        Completion Time:              2023-03-29T18:47:10+00:00
        Source Endpoint:              JGI Genome Portal shared endpoint 3
        Source Endpoint ID:           65fa2422-e080-11ec-990f-3b4cfda38030
        Destination Endpoint:         NERSC nmdcda
        Destination Endpoint ID:      ae777bc6-bf84-11ed-9917-cb2cff506ca5
        Bytes Transferred:            673199360470
        Bytes Per Second:             371815009''', 'returncode': 0}
        process_mock2 = Mock()
        process_mock2.configure_mock(**attrs)

        attrs = {
            'stdout': '''Label:                        None
        Task ID:                      a9b96f-ce5d-11ed-63ca-6c6821-e5130cf8
        Is Paused:                    False
        Type:                         TRANSFER
        Directories:                  0
        Files:                        478
        Status:                       SUCCEEDED
        Request Time:                 2023-03-29T18:16:59+00:00
        Faults:                       0
        Total Subtasks:               956
        Subtasks Succeeded:           956
        Subtasks Pending:             0
        Subtasks Retrying:            0
        Subtasks Failed:              0
        Subtasks Canceled:            0
        Subtasks Expired:             0
        Subtasks with Skipped Errors: 0
        Completion Time:              2023-03-29T18:47:10+00:00
        Source Endpoint:              JGI Genome Portal shared endpoint 3
        Source Endpoint ID:           65fa2422-e080-11ec-990f-3b4cfda38030
        Destination Endpoint:         NERSC nmdcda
        Destination Endpoint ID:      ae777bc6-bf84-11ed-9917-cb2cff506ca5
        Bytes Transferred:            673199360470
        Bytes Per Second:             371815009''', 'returncode': 0}
        process_mock3 = Mock()
        process_mock3.configure_mock(**attrs)

        mock_run.side_effect = [process_mock2, process_mock3]
        insert_globus_status_into_mongodb('e5130cf8-ce5d-11ed-a9b9-63ca5f6c6821', 'SUCCEEDED')
        insert_globus_status_into_mongodb('63ca5f-ce5d-11ed-a9b9-6c6821-e5130cf8', 'transferring')
        insert_globus_status_into_mongodb('a9b96f-ce5d-11ed-63ca-6c6821-e5130cf8', 'error')

        update_globus_statuses()
        self.assertEqual(mock_run.call_count, 2)
        mdb = get_mongo_db()
        task = mdb.globus.find_one({'task_id': '63ca5f-ce5d-11ed-a9b9-6c6821-e5130cf8'})
        self.assertEqual(task['task_status'], 'SUCCEEDED')

        task = mdb.globus.find_one({'task_id': 'a9b96f-ce5d-11ed-63ca-6c6821-e5130cf8'})
        self.assertEqual(task['task_status'], 'SUCCEEDED')


if __name__ == '__main__':
    unittest.main()
