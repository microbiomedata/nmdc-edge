import os
import shutil
from nmdc_automation.import_automation.activity_mapper import GoldMapper
from pytest import fixture
from time import time


@fixture
def nmdc_api(requests_mock):
    requests_mock.real_http = True
    data = {"expires": {"minutes": time()+60},
            "access_token": "abcd"
            }
    requests_mock.post("http://localhost/token", json=data)
    requests_mock.post("http://localhost/pids/mint", json=["nmdc:abcd"])
    requests_mock.post("http://localhost/workflows/activities",
                       json=["nmdc:abcd"])


@fixture
def gold_mapper(nmdc_api):
    yaml_file = os.path.abspath("./tests/import_test.yaml")
    test_files = [os.path.abspath("./test_data/test_pfam.gff"),
                  os.path.abspath("./test_data/test_cog.gff"),
                  os.path.abspath("./test_data/test_2.tar.gz"),
                  os.path.abspath("./test_data/test_72.tar.gz")]
    proj_dir = os.path.abspath("./test_data")
    site_conf = os.path.abspath("./tests/site_configuration_test.toml")
    omics_id = "nmdc:omprc-11-importT"
    root_dir = f"/tmp/{omics_id}"
    if os.path.exists(root_dir):
        shutil.rmtree(root_dir)
    gm = GoldMapper("1", test_files, omics_id, yaml_file, proj_dir, site_conf)
    gm.root_dir = root_dir
    return gm


def test_activity_mapper(gold_mapper):
    gold_mapper.unique_object_mapper()
    gold_mapper.multiple_objects_mapper()
    gold_mapper.activity_mapper()
    gold_mapper.post_nmdc_database_object()
    db = gold_mapper.get_database_object_dump()
    assert len(db.metagenome_annotation_activity_set) == 1
    assert len(db.mags_activity_set) == 1
    assert len(db.data_object_set) == 3


def test_unique_object_mapper(gold_mapper):
    gold_mapper.unique_object_mapper()
    assert len(gold_mapper.nmdc_db.data_object_set) == 2
    assert len(gold_mapper.objects) == 2


def test_multiple_object_mapper(gold_mapper):
    gold_mapper.multiple_objects_mapper()
    # Add assertions to check if the method works as expected
    assert len(gold_mapper.nmdc_db.data_object_set) == 1
    assert len(gold_mapper.objects) == 1
