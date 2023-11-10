# nmdc_automation/re_iding/tests/test_re_iding_base.py
import pytest_mock

from nmdc_automation.api import NmdcRuntimeApi
from nmdc_schema.nmdc import Database as NmdcDatabase
from nmdc_automation.re_iding.base import ReIdTool




def test_update_omics_processing_has_output(db_record, mocker):
    """
    Test that we can get a new Database with updated omics processing has_output
    and re-IDed data objects.
    """
    exp_do_id = "nmdc:dobj-1234-abcd12345"
    mock_api = mocker.Mock(spec=NmdcRuntimeApi)
    mock_api.minter.return_value = exp_do_id
    reid_tool = ReIdTool(mock_api)
    new_db = NmdcDatabase()
    new_db = reid_tool.update_omics_processing_has_output(db_record, new_db)
    assert isinstance(new_db, NmdcDatabase)
    assert new_db.omics_processing_set

    assert new_db.omics_processing_set[0].has_output[0] == exp_do_id


