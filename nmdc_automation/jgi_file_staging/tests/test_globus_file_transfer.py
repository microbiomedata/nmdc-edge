import shutil
import unittest
import os
from unittest.mock import patch, Mock
import mongomock
import pandas as pd
import configparser
from pathlib import Path
from testfixtures import Replace, mock_datetime

from globus_file_transfer import get_globus_manifest, get_mongo_db, get_globus_task_status, create_globus_batch_file, \
    create_globus_dataframe, insert_globus_status_into_mongodb, update_globus_statuses, submit_globus_batch_file
from staged_files import get_list_missing_staged_files

from jgi_file_metadata import insert_samples_into_mongodb


class GlobusTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.fixtures = os.path.join(os.path.dirname(__file__), 'fixtures')
        self.config_file = os.path.join(self.fixtures, 'config.ini')
        self.config = configparser.ConfigParser()
        self.config.read(self.config_file)

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

        mock_run.side_effect = [process_mock_2, process_mock_3, process_mock_4, process_mock_5,
                                process_mock_6, process_mock_7]
        get_globus_manifest(201670, config=self.config)
        self.assertEqual(mock_run.call_count, 2)
        self.assertEqual(mock_run.mock_calls[0].args[0], ['globus', 'ls',
                                                          '65fa2422-e080-11ec-990f-3b4cfda38030:/73709/R201670'])

    @patch('globus_file_transfer.get_globus_manifest')
    def test_create_globus_df(self, mock_run):
        process_mock_2 = Mock()
        attrs = {'stdout': "Globus_Download_201670_File_Manifest.csv\n", 'returncode': 0}
        process_mock_2.configure_mock(**attrs)
        mock_run.side_effect = ["Globus_Download_201545_File_Manifest.csv", "Globus_Download_201547_File_Manifest.csv",
                                "Globus_Download_201572_File_Manifest.csv"]
        globus_df = create_globus_dataframe(os.path.join(self.fixtures, 'globus_manifests'), self.config,
                                            [201545, 201547, 201572])
        self.assertEqual(len(globus_df), 76)
        self.assertEqual(globus_df.loc[0, 'directory/path'], 'ERLowmetatpilot/IMG_Data')
        self.assertEqual(globus_df.loc[0, 'filename'], 'Ga0502004_genes.fna')
        self.assertEqual(globus_df.loc[0, 'file_id'], '6141a2b4cc4ff44f36c8991a')
        self.assertEqual(globus_df.loc[0, 'subdir'], 'R201545')
        self.assertEqual(globus_df.loc[71, 'directory/path'], 'ERLowmetatpilot/IMG_Data')
        self.assertEqual(globus_df.loc[72, 'md5 checksum'], 'ba5d300cacb6f24dc9130f94ab18d3b5')
        self.assertEqual(globus_df.loc[75, 'filename'], 'Table_6_-_Ga0502004_sigs_annotation_parameters.txt')
        self.assertEqual(globus_df.loc[75, 'subdir'], 'R201572')

    @patch('globus_file_transfer.get_globus_manifest')
    @mongomock.patch(servers=(('localhost', 27017),))
    def test_create_globus_batch_file(self, mock_get_manifest):
        mock_get_manifest.side_effect = ["Globus_Download_201572_File_Manifest.csv"
                                         ]
        grow_analysis_df = pd.read_csv(os.path.join(self.fixtures, 'grow_analysis_projects.csv'))
        grow_analysis_df.columns = ['apGoldId', 'studyId', 'itsApId', 'projects', 'biosample_id', 'seq_id', 'file_name',
                                    'file_status', 'file_size', 'jdp_file_id', 'md5sum', 'analysis_project_id']
        grow_analysis_df = grow_analysis_df[['apGoldId', 'studyId', 'itsApId', 'biosample_id', 'seq_id',
                                             'file_name', 'file_status', 'file_size', 'jdp_file_id', 'md5sum',
                                             'analysis_project_id']]
        grow_analysis_df['file_status'] = 'ready'
        grow_analysis_df['project'] = 'test_project'
        grow_analysis_df['request_id'] = 201572
        insert_samples_into_mongodb(grow_analysis_df.to_dict('records'))
        try:
            with Replace('globus_file_transfer.datetime', mock_datetime(2022, 1, 1, 12, 22, 55, delta=0)) as d:
                globus_batch_filename, globus_analysis_df = create_globus_batch_file('test_project',
                                                                                     self.config)
            self.assertEqual(globus_batch_filename, 'test_project_201572_2022-01-01_12-22-55_globus_batch_file.txt')
            self.assertEqual(len(globus_analysis_df), 3)
            self.assertEqual(globus_analysis_df.loc[0, 'jdp_file_id'], '6190d7d30de2fc3298da6f7a')
            self.assertEqual(globus_analysis_df.loc[1, 'apGoldId'], 'Ga0499978')
            self.assertEqual(globus_analysis_df.loc[2, 'file_name'], 'Ga0499978_imgap.info')
            self.assertTrue(os.path.exists(globus_batch_filename))
        finally:
            os.remove('test_project_201572_2022-01-01_12-22-55_globus_batch_file.txt') if os.path.exists('test_project_201572_2022-01-01_12-22-55_globus_batch_file.txt') \
                else None

    @patch('globus_file_transfer.get_globus_manifest')
    @patch('globus_file_transfer.subprocess.run')
    @mongomock.patch(servers=(('localhost', 27017),))
    def test_submit_globus_batch_file(self, mock_run, mock_get_manifest):
        mock_get_manifest.side_effect = ["Globus_Download_201572_File_Manifest.csv"
                                         ]
        attrs = {
            'stdout': "Message: The transfer has been accepted and a task has been created and queued for execution\n"
                      "Task ID: e5130cf8-ce5d-11ed-a9b9-63ca5f6c6821", 'returncode': 0}
        process_mock = Mock()
        process_mock.configure_mock(**attrs)
        mock_run.side_effect = [process_mock, process_mock]
        grow_analysis_df = pd.read_csv(os.path.join(self.fixtures, 'grow_analysis_projects.csv'))
        grow_analysis_df.columns = ['apGoldId', 'studyId', 'itsApId', 'projects', 'biosample_id', 'seq_id', 'file_name',
                                    'file_status', 'file_size', 'jdp_file_id', 'md5sum', 'analysis_project_id']
        grow_analysis_df = grow_analysis_df[['apGoldId', 'studyId', 'itsApId', 'biosample_id', 'seq_id',
                                             'file_name', 'file_status', 'file_size', 'jdp_file_id', 'md5sum',
                                             'analysis_project_id']]
        grow_analysis_df['file_status'] = 'ready'
        grow_analysis_df['project'] = 'test_project'
        grow_analysis_df['request_id'] = 201572
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

    def test_get_list_staged_files(self):
        staged_files = ['52614.1.394702.GCACTAAC-CCAAGACT.filtered-report.txt',
                        '52614.1.394702.GCACTAAC-CCAAGACT.filter_cmd-METAGENOME.sh',
                        'Ga0499978_imgap.info', 'Ga0499978_proteins.supfam.domtblout',
                        'Ga0499978_ko.tsv', 'Ga0499978_proteins.faa',
                        'pairedMapped_sorted.bam.cov', 'Table_8_-_3300049478.taxonomic_composition.txt',
                        'Ga0499978_annotation_config.yaml']
        project_name = 'test_project'
        analysis_projects_dir = Path(self.fixtures, 'analysis_projects', f"{project_name}_analysis_projects", 'Ga0499978')
        shutil.rmtree(analysis_projects_dir) if Path.exists(analysis_projects_dir) else None
        Path.mkdir(analysis_projects_dir, parents=True)
        [Path.touch(Path(analysis_projects_dir, grow_file)) for grow_file in staged_files]

        grow_analysis_df = pd.read_csv(os.path.join(self.fixtures, 'grow_analysis_projects.csv'))
        grow_analysis_df.columns = ['apGoldId', 'studyId', 'itsApId', 'projects', 'biosample_id', 'seq_id', 'file_name',
                                    'file_status', 'file_size', 'jdp_file_id', 'md5sum', 'analysis_project_id']
        grow_analysis_df = grow_analysis_df[['apGoldId', 'studyId', 'itsApId', 'biosample_id', 'seq_id',
                                             'file_name', 'file_status', 'file_size', 'jdp_file_id', 'md5sum',
                                             'analysis_project_id']]
        grow_analysis_df['file_status'] = 'ready'
        grow_analysis_df['project'] = 'test_project'
        insert_samples_into_mongodb(grow_analysis_df.to_dict('records'))
        output_file = Path(os.path.dirname(__file__), 'merge_db_staged.csv')
        try:
            missing_files = get_list_missing_staged_files(project_name, self.config_file)
            self.assertTrue(os.path.exists(output_file))
            self.assertTrue('rqc-stats.pdf' in [el['file_name'] for el in missing_files if el['file_name'] == 'rqc-stats.pdf'])
        finally:
            os.remove(output_file) if Path.exists(output_file) else None
            shutil.rmtree(analysis_projects_dir) if Path.exists(analysis_projects_dir) else None


if __name__ == '__main__':
    unittest.main()
