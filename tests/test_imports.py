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
def gold_mapper(nmdc_api, base_test_dir, test_data_dir):
    yaml_file = base_test_dir / "import_test.yaml"
    test_files = [test_data_dir / "test_pfam.gff",
                  test_data_dir / "test_cog.gff",
                  test_data_dir / "test_2.tar.gz",
                  test_data_dir / "test_72.tar.gz"]
    # proj_dir = os.path.abspath("./test_data")
    site_conf = base_test_dir / "site_configuration_test.toml"
    omics_id = "nmdc:omprc-11-importT"
    root_dir = f"/tmp/{omics_id}"
    if os.path.exists(root_dir):
        shutil.rmtree(root_dir)
    gm = GoldMapper("1", test_files, omics_id, yaml_file, test_data_dir, site_conf)
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
