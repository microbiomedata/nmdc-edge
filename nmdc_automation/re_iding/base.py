# nmdc_automation/nmddc_automation/re_iding/base.py
"""
base.py - Provides classes and functions for re-ID-ing NMDC metagenome workflow
records and data objects.
"""
import logging
from typing import List
from pathlib import Path
import json
from typing import Dict, List

from nmdc_schema.nmdc import Database, DataObject
from nmdc_automation.re_iding.db_utils import (
    OMICS_PROCESSING_SET,
    DATA_OBJECT_SET,
    check_for_single_omics_processing_record,
)


NAPA_TEMPLATE = "../../configs/re_iding_worklfows.yaml"


def get_new_db_and_downstream_inputs(
        db_record: Dict, config_file: str = None) -> (Database,
                                                     List[DataObject]):
    """
    Return a new Database instance with the given new_omics_processing_record
    and the data objects that are has_output of the given old_omics_processing_record
    """
    if config_file is None:
        config_file = NAPA_TEMPLATE
    config_file = Path(config_file)

    new_db = Database()
    downstream_inputs = []

    check_for_single_omics_processing_record(db_record)
    old_omics_processing_record = db_record[OMICS_PROCESSING_SET][0]

    return new_db, downstream_inputs