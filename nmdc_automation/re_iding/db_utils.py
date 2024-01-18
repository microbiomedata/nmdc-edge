# nmdc_automation/nmdc_automation/re_iding/db_utils.py
"""
db_utils.py: Provides utility functions for working with NMDC Database
records and data objects as dicts.
"""
from dataclasses import dataclass
from typing import Dict, List
from nmdc_schema.nmdc import Database, DataObject

# Some constants for set names we care about
OMICS_PROCESSING_SET = "omics_processing_set"
DATA_OBJECT_SET = "data_object_set"
READS_QC_SET = "read_qc_analysis_activity_set"
METAGENOME_ASSEMBLY_SET = "metagenome_assembly_set"
METATRANSCRIPTOME_ACTIVITY_SET = "metatranscriptome_activity_set"




def get_omics_processing_id(db_record: Dict) -> str:
    """
    Get the ID of the OmicsProcessing record in the given Database instance.
    The OmicsProcessing record acts as the root of the workflow graph and
    the data objects.
    """
    check_for_single_omics_processing_record(db_record)
    omics_processing_set = db_record[OMICS_PROCESSING_SET]
    return omics_processing_set[0]["id"]


def check_for_single_omics_processing_record(db_record: Dict) -> bool:
    """
    Check that there is only one OmicsProcessing record in the Database.
    """
    omics_processing_set = db_record.get("omics_processing_set", [])
    if len(omics_processing_set) == 0:
        raise ValueError("No omics_processing_set found in db_record")
    elif len(omics_processing_set) > 1:
        raise ValueError("Multiple omics_processing_set found in db_record")
    return True

def get_data_object_record_by_id(db_record: Dict, id: str)-> Dict:
    """
    Return the data object record with the given ID.
    """
    data_objects = [d for d in db_record[DATA_OBJECT_SET] if d["id"] == id]
    if len(data_objects) == 0:
        raise ValueError(f"No data object found with id: {id}")
    elif len(data_objects) > 1:
        raise ValueError(f"Multiple data objects found with id: {id}")
    return data_objects[0]









