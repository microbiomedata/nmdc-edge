# nmdc_automation/re_iding/tests/test_re_iding_base.py

from nmdc_schema.nmdc import Database
from nmdc_automation.re_iding.base import get_new_db_and_downstream_inputs



def test_get_new_db_and_downstream_inputs(db_record):
    """
    Test that we can get a new Database instance and downstream inputs from an
    existing Database instance.
    """
    new_db, downstream_inputs = get_new_db_and_downstream_inputs(db_record)
    assert isinstance(new_db, Database)
    assert isinstance(downstream_inputs, list)