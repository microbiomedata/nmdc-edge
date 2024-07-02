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

WORKFLOW_ID_CODE_MAP = {
    "nmdc:wfmag": MAGS_ACTIVITY_SET,
    "nmdc:wfmb": METABOLOMICS_ANALYSIS_ACTIVITY_SET,
    "nmdc:wfmgan": METAGENOME_ANNOTATION_ACTIVITY_SET,
    "nmdc:wfmgas": METAGENOME_ASSEMBLY_SET,
    "nmdc:wfrbt": READ_BASED_TAXONOMY_ANALYSIS_ACTIVITY_SET,
    "nmdc:wfrqc": READS_QC_SET,
}


def get_collection_name_from_workflow_id(workflow_id: str) -> str:
    """
    Get the collection name for the given workflow ID based on the
    embedded code.
     e.g. nmdc:wfrqc-11-zbyqeq59.1 -> nmdc:wfrqc -> READS_QC_SET
    """
    code = workflow_id.split("-")[0]
    return WORKFLOW_ID_CODE_MAP.get(code, "unknown")


def fix_malformed_workflow_id_version(workflow_id: str) -> str:
    """
    Fix a malformed workflow id version examples
        - extra .1(s) at the end of the version e.g. nmdc:wfrqc-11-zbyqeq59.1.1
        - missing version e.g nmdc:wfrqc-11-zbyqeq59
    Corrected version will be nmdc:wfrqc-11-zbyqeq59.1
    """
    parts = workflow_id.split(".")
    if len(parts) >2:
        return ".".join(parts[:2])
    elif len(parts) == 1:
        return f"{workflow_id}.1"
    return workflow_id

def fix_malformed_data_object_name(name: str) -> str:
    """
    Fix a malformed data object name - example
    - "nmdc_wfrqc-11-pbxpdr12.1.1_filtered.fastq.gz" -> "nmdc_wfrqc-11-pbxpdr12.1_filtered.fastq.gz"
    - "nmdc_wfrqc-11-pbxpdr12_filtered.fastq.gz" -> "nmdc_wfrqc-11-pbxpdr12.1_filtered.fastq.gz"
    """
    # Split along the `_` to get nmdc, the workflow id and the rest of the name
    logging.info(f"Fixing malformed data object name: {name}")
    parts = name.split("_")
    nmdc = parts[0]
    workflow_id = parts[1]
    rest = "_".join(parts[2:])
    fixed_workflow_id = fix_malformed_workflow_id_version(workflow_id)
    return f"{nmdc}_{fixed_workflow_id}_{rest}"


def fix_malformed_data_object_url(url: str) -> str:
    """
    Fix a malformed data object URL - example
    - "https://data.microbiomedata.org/data/nmdc:omprc-11-wmzpa354/nmdc:wfrqc-11-pbxpdr12.1.1/nmdc_wfrqc-11-pbxpdr12.1.1_filtered.fastq.gz"
    -> "https://data.microbiomedata.org/data/nmdc:omprc-11-wmzpa354/nmdc:wfrqc-11-pbxpdr12.1/nmdc_wfrqc-11-pbxpdr12.1_filtered.fastq.gz"
    """
    parts = url.split("/")
    name = parts[-1]
    # if the name does not look like an NMDC workflow data file name, do not try to fix it
    if not name.startswith("nmdc_wf"):
        return url
    dirname = parts[-2]
    fixed_name = fix_malformed_data_object_name(name)
    fixed_dirname = fix_malformed_workflow_id_version(dirname)
    parts[-1] = fixed_name
    parts[-2] = fixed_dirname
    return "/".join(parts)


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
        raise ValueError(f"Multiple data objects found with id: {id}")
    return data_objects[0]

def check_if_data_object_record_has_malformed_version(data_object: Dict, workflow_id: str) -> bool:
    """
    Check if the data object record has a malformed version
    """
    # Name can be a filename e.g. nmdc_wfrbt-13-3m1n3g49.1_gottcha2_report.tsv
    # but can be almosdt anything e.g. GOTTCHA2 classification report file
    data_object_name = data_object.get("name", "")
    workflow_name = workflow_id.replace("nmdc:", "nmdc_")
    is_malformed_name = False
    if workflow_name in data_object_name:
        fixed_data_object_name = fix_malformed_data_object_name(data_object_name)
        if fixed_data_object_name != data_object_name:
            is_malformed_name = True
            logging.warning(f"Data object name is malformed: {data_object_name}")

    data_object_url = data_object.get("url", "")
    is_malformed_url = False
    if data_object_url:
        fixed_data_object_url = fix_malformed_data_object_url(data_object_url)
        if fixed_data_object_url != data_object_url:
            is_malformed_url = True
            logging.warning(f"Data object URL is malformed: {data_object_url}")

    return is_malformed_name or is_malformed_url