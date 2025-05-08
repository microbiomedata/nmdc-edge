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

from jgi_file_metadata import (
    get_access_token,
    check_access_token,
    get_analysis_projects_from_proposal_id,
    get_sample_files,
    get_sequence_id,
    insert_samples_into_mongodb,
    get_files_and_agg_ids,
    remove_unneeded_files,
    get_samples_data,
    remove_duplicate_analysis_files,
    remove_large_files,
    get_seq_unit_names,
    get_request, get_biosample_ids, create_all_files_list
)
from mongo import get_mongo_db
from models import SequencingProject
from file_restoration import update_sample_in_mongodb


class JgiFileTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.fixtures = os.path.join(os.path.dirname(__file__), "fixtures")
        self.config_file = os.path.join(self.fixtures, "config.ini")
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(self.config_file)
        self.config = config

    @mongomock.patch(servers=(("localhost", 27017),))
    def tearDown(self) -> None:
        mdb = get_mongo_db()
        mdb.samples.drop()
        mdb.globus.drop()

    @staticmethod
    @mongomock.patch(servers=(('localhost', 27017),))
    def insert_sequencing_project():
        insert_dict = {'proposal_id': '507130', 'project_name': 'bioscales',
                       'nmdc_study_id': 'nmdc:sty-11-r2h77870',
                       'analysis_projects_dir': 'nmdc_automation/jgi_file_staging/tests/fixtures/test_project'}
        insert_object = SequencingProject(**insert_dict)
        mdb = get_mongo_db()
        mdb.sequencing_projects.insert_one(insert_object.dict())
        insert_dict = {'proposal_id': '508306', 'project_name': '1000_soils', 'nmdc_study_id': 'nmdc:sty-11-28tm5d36',
                       'analysis_projects_dir': '/global/cfs/cdirs/m3408/aim2/dev'}
        insert_object = SequencingProject(**insert_dict)
        mdb.sequencing_projects.insert_one(insert_object.dict())

    @patch("jgi_file_metadata.requests.get")
    def test_get_request(self, mock_get):
        mock_get.return_value.json.return_value = "[{'itsSpid': 1323348}]"
        mock_get.return_value.status_code = 200
        url = 'https://gold-ws.jgi.doe.gov/api/v1/projects?biosampleGoldId=Gb0291582'
        ACCESS_TOKEN = '33k0krk2k4k56l'
        value = get_request(url, ACCESS_TOKEN)
        self.assertEqual(value, "[{'itsSpid': 1323348}]")

    @patch('jgi_file_metadata.get_request')
    def test_get_biosample_ids(self, mock_get_request):
        mock_get_request.return_value = [{'biosampleGoldId': 'Gb0156560'}, {'biosampleGoldId': 'Gb0156587'},
                                         {'biosampleGoldId': 'Gb0156618'}, {'biosampleGoldId': 'Gb0156656'},
                                         {'biosampleGoldId': 'Gb0156820'}, {'biosampleGoldId': 'Gb0156898'},
                                         {'biosampleGoldId': 'Gb0158490'}, {'biosampleGoldId': 'Gb0158497'},
                                         {'biosampleGoldId': 'Gb0158498'}, {'biosampleGoldId': 'Gb0158504'}]
        samples_df = pd.DataFrame({'Biosample ID': get_biosample_ids(503125, '')})
        self.assertEqual(len(samples_df), 10)
        self.assertEqual(samples_df.loc[0,'Biosample ID'], 'Gb0156560')

    @mongomock.patch(servers=(("localhost", 27017),))
    def test_insert_samples_into_mongodb(self):
        grow_analysis_df = pd.read_csv(
            os.path.join(self.fixtures, "grow_analysis_projects.csv")
        )

        grow_analysis_df["project"] = "test_project"
        # grow_analysis_df['projects'] = grow_analysis_df['projects'].apply(lambda x: eval(x))
        grow_analysis_df['analysis_project_id'] = grow_analysis_df['analysis_project_id'].apply(lambda x: str(x))
        insert_samples_into_mongodb(grow_analysis_df.to_dict("records"))
        mdb = get_mongo_db()
        sample = mdb.samples.find_one({"apGoldId": "Ga0499978"})
        self.assertEqual(sample["studyId"], "Gs0149396")
        sample = mdb.samples.find_one({"jdp_file_id": "61a9d6ee8277d7ede604d0f6"})
        self.assertEqual(sample["file_name"], "Ga0499978_imgap.info")
        self.assertEqual(sample["file_status"], "RESTORED")

    @mongomock.patch(servers=(('localhost', 27017),))
    def test_insert_samples_into_mongodb_fail_valid(self):
        grow_analysis_df = pd.read_csv(
            os.path.join(self.fixtures, "grow_analysis_projects.csv")
        )

        grow_analysis_df["project"] = None
        mdb = get_mongo_db()
        sample = mdb.samples.find_one({"apGoldId": "Ga0499978"})
        insert_samples_into_mongodb(grow_analysis_df.to_dict("records"))
        mdb = get_mongo_db()
        sample = mdb.samples.find_one({"apGoldId": "Ga0499978"})
        self.assertEqual(sample, None)

    @mongomock.patch(servers=(("localhost", 27017),))
    def test_update_samples_in_mongodb(self):
        grow_analysis_df = pd.read_csv(
            os.path.join(self.fixtures, "grow_analysis_projects.csv")
        )
        grow_analysis_df['project'] = "test_project"
        grow_analysis_df['analysis_project_id'] = grow_analysis_df['analysis_project_id'].apply(lambda x: str(x))
        insert_samples_into_mongodb(grow_analysis_df.to_dict("records"))
        mdb = get_mongo_db()
        sample = mdb.samples.find_one({"jdp_file_id": "6190d7d30de2fc3298da6f7a"})
        update_sample_in_mongodb(
            sample, {"file_status": "RESTORE_IN_PROGRESS", "request_id": '217934'}
        )
        updated_sample = mdb.samples.find_one({"jdp_file_id": "6190d7d30de2fc3298da6f7a"})
        self.assertEqual(updated_sample["file_status"], "RESTORE_IN_PROGRESS")
        self.assertEqual(updated_sample["request_id"], '217934')

        sample = mdb.samples.find_one({"jdp_file_id": "6190d7d30de2fc3298da6f7a"})
        sample.pop("file_name")
        success = update_sample_in_mongodb(
            sample, {"file_status": "RESTORE_IN_PROGRESS", "request_id": '217934'}
        )
        self.assertFalse(success)

    @patch("jgi_file_metadata.requests.get")
    def test_get_files_and_agg_ids(self, mock_get):
        with open(os.path.join(self.fixtures, "files_data.json"), "r") as f:
            files_json = json.load(f)
        mock_get.return_value.json.return_value = files_json
        mock_get.return_value.status_code = 200
        files_data_list = get_files_and_agg_ids(1323459, "ed42ef155670")
        self.assertEqual(
            files_data_list[0]['files'][0]["file_name"],
            "Table_8_-_3300049478.taxonomic_composition.txt",
        )
        self.assertEqual(files_data_list[0]['files'][0]["file_type"], "report")
        self.assertEqual(files_data_list[0]['agg_id'], 1323348)

    @patch("jgi_file_metadata.requests.get")
    def test_get_files_and_agg_ids_no_organisms(self, mock_get):
        with open(os.path.join(self.fixtures, "files_data.json"), "r") as f:
            files_json = json.load(f)
        files_json.pop("organisms")
        mock_get.return_value.json.return_value = files_json
        mock_get.return_value.status_code = 200
        files_data_list = get_files_and_agg_ids(1323459, "ed42ef155670")
        self.assertEqual(files_data_list, [])

    def test_create_all_files_list(self):
        with open(os.path.join(self.fixtures, "files_data_list.json"), "r") as f:
            files_json = json.load(f)
        all_files_list = []
        create_all_files_list(files_json, 'Gb0156560', 1323459, all_files_list)
        self.assertEqual(len(all_files_list), 85)
        self.assertEqual(all_files_list[3]['file_name'], 'Ga0499978_ko.tsv')
        self.assertEqual(all_files_list[3]['biosample_id'], 'Gb0156560')
        self.assertEqual(all_files_list[3]['seq_id'], 1323459)
        self.assertEqual(all_files_list[3]['analysis_project_id'], 1323348)
        self.assertEqual(all_files_list[3]['seq_unit_name'], None)
        self.assertEqual(all_files_list[66]['seq_unit_name'], ['52614.1.394702.GCACTAAC-CCAAGACT.fastq.gz'])

    @patch('jgi_file_metadata.get_request')
    @patch("jgi_file_metadata.get_files_and_agg_ids")
    @patch("jgi_file_metadata.get_access_token")
    def test_get_sample_files(self, mock_token,  mock_get_files_list, mock_get_request):
        # with open(os.path.join(self.fixtures, "files_data.json"), "r") as f:
        #     files_json = json.load(f)
        # files_data_list = []
        # agg_id_list = []
        # for org in files_json["organisms"]:
        #     files_data_list.append(org["files"])
        #     agg_id_list.append(org["agg_id"])
        with open(os.path.join(self.fixtures, "files_data_list.json"), "r") as f:
            files_json = json.load(f)
        mock_get_files_list.return_value = files_json
        mock_token.return_value = "ed42ef155670"
        # mock_get.return_value.json.return_value = [{"itsSpid": 1323348}]
        # mock_get.return_value.status_code = 200
        mock_get_request.side_effect = [[{'biosampleGoldId': 'Gb0156560'}], 'lekl%l',
                                        [{"itsApId": 1323348, 'apType': "Metagenome Analysis"}]]
        grow_samples = get_sample_files(
            12345,
            "ed42ef155670",
            eval(self.config["JDP"]["delay"]),
        )
        self.assertEqual(
            grow_samples[0]["file_name"],
            "Table_8_-_3300049478.taxonomic_composition.txt",
        )

    # def test_remove_large_files(self):
    #     with open(os.path.join(self.fixtures, "seq_files_df.json"), "r") as f:
    #         files_data_list = json.load(f)
    #     seq_files_df = pd.DataFrame(files_data_list)
    #     self.assertFalse(
    #         seq_files_df[
    #             seq_files_df.file_name == "Ga0451670_proteins.img_nr.last.blasttab"
    #         ].empty
    #     )
    #     self.assertFalse(
    #         seq_files_df[
    #             seq_files_df.file_name == "Ga0451670_proteins.supfam.domtblout"
    #         ].empty
    #     )
    #     seq_files_df = remove_large_files(
    #         seq_files_df, ["img_nr.last.blasttab", "domtblout"]
    #     )
    #     self.assertEqual(len(seq_files_df), 71)
    #     self.assertTrue(
    #         seq_files_df[
    #             seq_files_df.file_name == "Ga0451670_proteins.img_nr.last.blasttab"
    #         ].empty
    #     )
    #     self.assertTrue(
    #         seq_files_df[
    #             seq_files_df.file_name == "Ga0451670_proteins.supfam.domtblout"
    #         ].empty
    #     )

    def test_get_seq_unit_names(self):
        seq_files_df = pd.read_csv(os.path.join(self.fixtures, "Gb0258377_gold_analysis_files.csv"))
        seq_files_df.loc[pd.notna(seq_files_df.seq_unit_name), 'seq_unit_name'] = seq_files_df.loc[
            pd.notna(seq_files_df.seq_unit_name), 'seq_unit_name'].apply(lambda x: eval(x))
        seq_unit_names = get_seq_unit_names(seq_files_df, "Ga0451670")
        self.assertEqual(seq_unit_names, ["52444.3.336346.GAGCTCAA-GAGCTCAA"])

    def test_remove_duplicate_analysis_files(self):
        seq_files_df = pd.read_csv(os.path.join(self.fixtures, "Gb0258377_gold_analysis_files.csv"))
        seq_files_df.loc[pd.notna(seq_files_df.seq_unit_name), 'seq_unit_name'] = seq_files_df.loc[
            pd.notna(seq_files_df.seq_unit_name), 'seq_unit_name'].apply(lambda x: eval(x))
        seq_files_df = seq_files_df[(seq_files_df.apGoldId == 'Ga0485222')]
        self.assertFalse(
            seq_files_df[(seq_files_df.apGoldId == 'Ga0485222') &
                         (seq_files_df.file_name == "52444.3.336346.GAGCTCAA-GAGCTCAA.fastq.gz")
                         ].empty
        )
        grow_samples_df = remove_duplicate_analysis_files(seq_files_df)
        self.assertTrue(
            seq_files_df[(seq_files_df.apGoldId == 'Ga0485222') &
                         (seq_files_df.file_name == "52444.3.336346.GAGCTCAA-GAGCTCAA.fastq.gz")
                         ].empty
        )

    def test_remove_large_files(self):
        seq_files_df = pd.read_csv(os.path.join(self.fixtures, "Gb0258377_gold_analysis_files.csv"))
        seq_files_df.loc[pd.notna(seq_files_df.seq_unit_name), 'seq_unit_name'] = seq_files_df.loc[
            pd.notna(seq_files_df.seq_unit_name), 'seq_unit_name'].apply(lambda x: eval(x))
        seq_files_df = seq_files_df[(seq_files_df.apGoldId == 'Ga0485222')]
        self.assertFalse(seq_files_df[seq_files_df.file_name == 'Ga0485222_proteins.pfam.domtblout'].empty)
        grow_samples_df = remove_large_files(seq_files_df, ["img_nr.last.blasttab", "domtblout"])
        self.assertEqual(len(grow_samples_df), 74)
        self.assertTrue(grow_samples_df[grow_samples_df.file_name == 'Ga0485222_proteins.pfam.domtblout'].empty)

    @patch("jgi_file_metadata.get_files_and_agg_ids")
    @patch("jgi_file_metadata.requests.get")
    @patch("jgi_file_metadata.get_access_token")
    def test_remove_unneeded_files(self, mock_token, mock_get, mock_get_files_list):
        seq_files_df = pd.read_csv(os.path.join(self.fixtures, "Gb0258377_gold_analysis_files.csv"))
        seq_files_df.loc[pd.notna(seq_files_df.seq_unit_name), 'seq_unit_name'] = seq_files_df.loc[
            pd.notna(seq_files_df.seq_unit_name), 'seq_unit_name'].apply(lambda x: eval(x))

        seq_files_df = seq_files_df[(seq_files_df.apGoldId == 'Ga0485222')]
        self.assertFalse(
            seq_files_df[(seq_files_df.apGoldId == 'Ga0485222') &
                         (seq_files_df.file_name == "52444.3.336346.GAGCTCAA-GAGCTCAA.fastq.gz")
                         ].empty
        )
        self.assertFalse(
            seq_files_df[(seq_files_df.apGoldId == 'Ga0485222') &
                         (seq_files_df.file_name == "Ga0485222_proteins.img_nr.last.blasttab")
                         ].empty
        )
        grow_samples_df = remove_unneeded_files(
            seq_files_df, ["img_nr.last.blasttab", "domtblout"]
        )
        self.assertEqual(len(grow_samples_df), 73)
        self.assertTrue(
            grow_samples_df[
                grow_samples_df.file_name == "52444.3.336346.GAGCTCAA-GAGCTCAA.fastq.gz"
            ].empty
        )
        self.assertTrue(
            grow_samples_df[
                grow_samples_df.file_name == "Ga0485222_proteins.img_nr.last.blasttab"
            ].empty
        )
    @patch("jgi_file_metadata.get_files_and_agg_ids")
    @patch("jgi_file_metadata.get_biosample_ids")
    @patch("jgi_file_metadata.requests.get")
    @patch("jgi_file_metadata.get_sequence_id")
    @patch("jgi_file_metadata.check_access_token")
    @patch("jgi_file_metadata.get_access_token")
    @patch("jgi_file_metadata.get_analysis_projects_from_proposal_id")
    @mongomock.patch(servers=(("localhost", 27017),))
    def test_get_samples_data(
        self,
        mock_analysis_projects,
        mock_token,
        mock_check_token,
        mock_sequence_id,
        mock_get,
        mock_biosample_ids,
        mock_file_ids
    ):
        self.insert_sequencing_project()
        with open(os.path.join(self.fixtures, "gold_analysis_data.txt"), "r") as f:
            files_json = json.load(f)
        mock_analysis_projects.return_value = files_json
        mock_token.return_value = "ed42ef155670"
        mock_check_token.return_value = "ed42ef155670"
        mock_sequence_id.return_value = [1323348]
        with open(os.path.join(self.fixtures, "files_data.json"), "r") as f:
            files_json = json.load(f)
        mock_get.return_value.json.return_value = files_json
        mock_get.return_value.status_code = 200
        mock_biosample_ids.return_value = ['Gb0258377']
        with open(os.path.join(self.fixtures, "files_data_list.json"), "r") as f:
            files_json_list = json.load(f)
        mock_file_ids.return_value = files_json_list
        get_samples_data('bioscales', self.config_file)
        mdb = get_mongo_db()
        sample = mdb.samples.find_one({"apGoldId": "Ga0499978"})
        self.assertEqual(sample["studyId"], "Gs0149396")


if __name__ == "__main__":
    unittest.main()
