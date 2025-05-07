import unittest
from pathlib import Path
import shutil
import pandas as pd
import os
import configparser

from nmdc_automation.db.nmdc_mongo import get_test_db
from nmdc_automation.jgi_file_staging.jgi_file_metadata import sample_records_to_sample_objects
from nmdc_automation.jgi_file_staging.staged_files import get_list_missing_staged_files, get_list_staged_files

class StagedFilesTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.fixtures = os.path.join(os.path.dirname(__file__), "fixtures")
        self.config_file = os.path.join(self.fixtures, "config.ini")
        self.config = configparser.ConfigParser()
        self.config.read(self.config_file)
        self.project_name = "test_project"
        self.analysis_projects_dir = Path(
            self.fixtures,
            "analysis_projects",
            f"{self.project_name}_analysis_projects",
            "Ga0499978",
        )
    def tearDown(self):
        shutil.rmtree(self.analysis_projects_dir) if Path.exists(
            self.analysis_projects_dir
        ) else None

    def create_test_files(self):
        staged_files = [
            "52614.1.394702.GCACTAAC-CCAAGACT.filtered-report.txt",
            "52614.1.394702.GCACTAAC-CCAAGACT.filter_cmd-METAGENOME.sh",
            "Ga0499978_imgap.info",
            "Ga0499978_proteins.supfam.domtblout",
            "Ga0499978_ko.tsv",
            "Ga0499978_proteins.faa",
            "pairedMapped_sorted.bam.cov",
            "Table_8_-_3300049478.taxonomic_composition.txt",
            "Ga0499978_annotation_config.yaml",
        ]

        shutil.rmtree(self.analysis_projects_dir) if Path.exists(
            self.analysis_projects_dir
        ) else None
        Path.mkdir(self.analysis_projects_dir, parents=True)
        [
            Path.touch(Path(self.analysis_projects_dir, grow_file))
            for grow_file in staged_files
        ]

    def test_get_list_staged_files(self):
        self.create_test_files()
        staged_df = get_list_staged_files('test_project', self.config, self.config)
        self.assertEqual(staged_df.shape, (len(staged_df), 2))
        self.assertEqual(staged_df.loc[0,"analysis_project"], 'Ga0499978')

    def test_get_list_missing_staged_files(self):
        self.create_test_files()

        grow_analysis_df = pd.read_csv(
            os.path.join(self.fixtures, "grow_analysis_projects.csv")
        )
        grow_analysis_df["file_status"] = "ready"

        sample_objects = sample_records_to_sample_objects(grow_analysis_df.to_dict("records"))
        mdb = get_test_db()
        output_file = Path(os.path.dirname(__file__), "merge_db_staged.csv")
        try:
            missing_files = get_list_missing_staged_files(
                self.project_name, self.config_file, mdb
            )
            self.assertTrue(os.path.exists(output_file))
            self.assertTrue(
                "rqc-stats.pdf"
                in [
                    el["file_name"]
                    for el in missing_files
                    if el["file_name"] == "rqc-stats.pdf"
                ]
            )
        finally:
            os.remove(output_file) if Path.exists(output_file) else None


if __name__ == '__main__':
    unittest.main()
