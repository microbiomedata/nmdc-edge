import unittest
import uuid
import hashlib
import os
from os.path import join, dirname
from unittest.mock import patch, Mock
from nmdc_automation.import_automation.activity_mapper import GoldMapper
import nmdc_schema.nmdc as nmdc


class TestGoldMapper(unittest.TestCase):

   
    def setUp(self):
        yaml_file = os.path.abspath("../configs/import.yaml")
        test_files = [os.path.abspath("../test_data/test_cog.gff"), os.path.abspath("../test_data/test_2.tar.gz"),os.path.abspath("../test_data/test_72.tar.gz")]
        proj_dir = os.path.abspath("./test_data")
        omics_id = "nmdc:omprc-11-importT"
        self.gold_mapper = GoldMapper(test_files, omics_id, yaml_file, proj_dir)


    def test_unique_object_mapper(self):
        # Call the method
        self.gold_mapper.unique_object_mapper()
        # Add assertions to check if the method works as expected
        self.assertEqual(len(self.gold_mapper.nmdc_db.data_object_set), 1)
        self.assertEqual(len(self.gold_mapper.objects), 1)
        
    def test_multiple_objects_mapper(self):
        # Call the method
        self.gold_mapper.multiple_objects_mapper()
        # Add assertions to check if the method works as expected
        self.assertEqual(len(self.gold_mapper.nmdc_db.data_object_set), 1)
        self.assertEqual(len(self.gold_mapper.objects), 1)


def generate_fake_md5() -> str:
    random_uuid = uuid.uuid4()
    md5_hash = hashlib.md5(str(random_uuid).encode('utf-8')).hexdigest()
    return md5_hash

if __name__ == "__main__":
    unittest.main()
