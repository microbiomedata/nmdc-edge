# nmdc_automation/nmdc_automation/re_iding/db_utils.py
"""
db_utils.py: Provides utility functions for working with NMDC Database
records and data objects as dicts.
"""
import logging
from dataclasses import dataclass
from typing import Dict, Optional
from nmdc_schema.nmdc import Database, DataObject

# Some constants for set names we care about
BIOSAMPLE_SET = "biosample_set"
OMICS_PROCESSING_SET = "omics_processing_set"
DATA_OBJECT_SET = "data_object_set"
READS_QC_SET = "read_qc_analysis_activity_set"
READ_BASED_TAXONOMY_ANALYSIS_ACTIVITY_SET = "read_based_taxonomy_analysis_activity_set"
METAGENOME_ASSEMBLY_SET = "metagenome_assembly_set"
METAGENOME_ANNOTATION_ACTIVITY_SET = "metagenome_annotation_activity_set"
METAGENOME_SEQUENCING_ACTIVITY_SET = "metagenome_sequencing_activity_set"
MAGS_ACTIVITY_SET = "mags_activity_set"
METATRANSCRIPTOME_ACTIVITY_SET = "metatranscriptome_activity_set"
METAPROTEOMICS_ANALYSIS_ACTIVITY_SET = "metaproteomics_analysis_activity_set"
METABOLOMICS_ANALYSIS_ACTIVITY_SET = "metabolomics_analysis_activity_set"
NOM_ANALYSIS_ACTIVITY_SET= "nom_analysis_activity_set"

ANALYSIS_ACTIVITIES = [
    READS_QC_SET,
    READ_BASED_TAXONOMY_ANALYSIS_ACTIVITY_SET,
    METAGENOME_ANNOTATION_ACTIVITY_SET,
    METAGENOME_SEQUENCING_ACTIVITY_SET,
    METAGENOME_ASSEMBLY_SET,
    MAGS_ACTIVITY_SET,
    METATRANSCRIPTOME_ACTIVITY_SET,
    METAPROTEOMICS_ANALYSIS_ACTIVITY_SET,
    METABOLOMICS_ANALYSIS_ACTIVITY_SET,
    NOM_ANALYSIS_ACTIVITY_SET
]



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

def get_data_object_record_by_id(db_record: Dict, id: str)-> Optional[Dict]:
    """
    Return the data object record with the given ID.
    """
    data_objects = [d for d in db_record[DATA_OBJECT_SET] if d["id"] == id]
    if len(data_objects) == 0:
        logging.warning(f"No data object found with id: {id}")
        return None
    elif len(data_objects) > 1:
        logging.warning(f"Multiple data objects found with id: {id}")
    return data_objects[0]
