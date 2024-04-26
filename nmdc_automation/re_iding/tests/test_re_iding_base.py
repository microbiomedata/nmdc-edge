# nmdc_automation/re_iding/tests/test_re_iding_base.py
from pathlib import Path
import pytest_mock

from nmdc_automation.api import NmdcRuntimeApi
from nmdc_schema.nmdc import Database as NmdcDatabase
from nmdc_schema.nmdc import DataObject as NmdcDataObject
from nmdc_schema.nmdc import Biosample
from nmdc_automation.re_iding.base import (
    ReIdTool,
    update_biosample,
    compare_models,
)


TEST_DATAFILE_DIR = "./test_data/results"

def test_update_omics_processing_has_output(db_record, mocker):
    """
    Test that we can get a new Database with updated omics processing has_output
    and re-IDed data objects.
    """
    exp_do_id = "nmdc:dobj-1234-abcd12345"
    mock_api = mocker.Mock(spec=NmdcRuntimeApi)
    mock_api.minter.return_value = exp_do_id
    reid_tool = ReIdTool(mock_api, TEST_DATAFILE_DIR)
    new_db = NmdcDatabase()
    new_db = reid_tool.update_omics_processing_has_output(db_record, new_db)
    assert isinstance(new_db, NmdcDatabase)
    assert new_db.omics_processing_set

    assert new_db.omics_processing_set[0].has_output[0] == exp_do_id


def test_make_new_data_object(data_object_record, mocker):
    """
    Test that we can make a new DataObject with a new ID and correct
    URL and Path attributes.
    """
    exp_do_id = "nmdc:dobj-1234-abcd12345"
    exp_url = 'https://data.microbiomedata.org/data/nmdc:omics_processing-1234-abcd12345/nmdc:activity-1234-abcd12345/nmdc_activity-1234-abcd12345_filtered.fastq.gz'
    mock_api = mocker.Mock(spec=NmdcRuntimeApi)
    mock_api.minter.return_value = exp_do_id
    reid_tool = ReIdTool(mock_api, TEST_DATAFILE_DIR)
    new_do = reid_tool.make_new_data_object(
        omics_processing_id="nmdc:omics_processing-1234-abcd12345",
        activity_type="nmdc:ReadQcAnalysisActivity",
        new_activity_id="nmdc:activity-1234-abcd12345",
        data_object_record=data_object_record,
        data_object_type="Filtered Sequencing Reads",
    )
    assert isinstance(new_do, NmdcDataObject)
    assert new_do.id == exp_do_id
    assert new_do.url == exp_url

def test_update_biosample_igsn_biosample_record_id_set_correctly_no_id_map(igsn_biosample_record, mocker):
    """
    Test that we can update a Biosample with an IGSN Biosample record with no identifiers_map provided.
    """
    exp_biosample_id = "nmdc:bsm-1234-abcd12345"
    mock_api = mocker.Mock(spec=NmdcRuntimeApi)
    mock_api.minter.return_value = exp_biosample_id
    exp_study_id = "nmdc:sty-1234-abcd12345"

    orig_biosample_id = igsn_biosample_record["id"]

    biosample = Biosample(**igsn_biosample_record)
    updated_biosample = update_biosample(biosample, exp_study_id, mock_api)

    assert isinstance(updated_biosample, Biosample)
    assert updated_biosample.id == exp_biosample_id
    assert updated_biosample.part_of == [exp_study_id]
    assert updated_biosample.igsn_biosample_identifiers == [orig_biosample_id]

def test_compare_models_igsn_biosample_updates(igsn_biosample_record, mocker):
    """
    Test that we can compare a Biosample with an IGSN Biosample record and update it.
    """
    exp_biosample_id = "nmdc:bsm-1234-abcd12345"
    mock_api = mocker.Mock(spec=NmdcRuntimeApi)
    mock_api.minter.return_value = exp_biosample_id
    exp_study_id = "nmdc:sty-1234-abcd12345"

    orig_biosample_id = igsn_biosample_record["id"]
    orig_study_id = igsn_biosample_record["part_of"][0]

    biosample = Biosample(**igsn_biosample_record)
    updated_biosample = update_biosample(biosample, exp_study_id, mock_api)

    changes = compare_models(biosample, updated_biosample)
    assert changes["id"] == exp_biosample_id
    assert changes["part_of"] == [exp_study_id]
    assert changes["igsn_biosample_identifiers"] == [orig_biosample_id]