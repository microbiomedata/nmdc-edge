import unittest
import os
from unittest.mock import patch, Mock
import mongomock
import pandas as pd
import configparser

from globus_file_transfer import get_globus_manifests, get_mongo_db, get_globus_task_status, create_globus_batch_file, \
    create_globus_dataframe, insert_globus_status_into_mongodb, update_globus_statuses, submit_globus_batch_file

from jgi_file_metadata import insert_samples_into_mongodb

class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.fixtures = os.path.join(os.path.dirname(__file__), 'fixtures')
        self.config_file = os.path.join(self.fixtures, 'config.ini')

    def tearDown(self) -> None:
        mdb = get_mongo_db()
        mdb.samples.drop()
        mdb.globus.drop()

    @patch('globus_file_transfer.subprocess.run')
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

    @patch('globus_file_transfer.subprocess.run')
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

    @patch('globus_file_transfer.subprocess.run')
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

    @patch('globus_file_transfer.subprocess.run')
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
