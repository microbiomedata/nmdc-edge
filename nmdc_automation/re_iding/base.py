# nmdc_automation/nmddc_automation/re_iding/base.py
"""
base.py - Provides classes and functions for re-ID-ing NMDC metagenome workflow
records and data objects.
"""
import copy
import csv
import logging
from copy import deepcopy
from dataclasses import asdict
from typing import Dict, List
import os
import re
import yaml
from pathlib import Path

from nmdc_schema.nmdc import DataObject as NmdcDataObject, \
    Database as NmdcDatabase, OmicsProcessing, WorkflowExecutionActivity
import nmdc_schema.nmdc as nmdc

from nmdc_automation.api import NmdcRuntimeApi
from nmdc_automation.re_iding.db_utils import (
    BIOSAMPLE_SET,
    OMICS_PROCESSING_SET,
    READS_QC_SET,
    MAGS_ACTIVITY_SET,
    METAGENOME_ASSEMBLY_SET,
    METAGENOME_ANNOTATION_ACTIVITY_SET,
    METATRANSCRIPTOME_ACTIVITY_SET,
    READ_BASED_TAXONOMY_ANALYSIS_ACTIVITY_SET,
    DATA_OBJECT_SET,
    METABOLOMICS_ANALYSIS_ACTIVITY_SET,
    NOM_ANALYSIS_ACTIVITY_SET,
    check_for_single_omics_processing_record,
    get_data_object_record_by_id,
    get_omics_processing_id
)
from nmdc_automation.re_iding.file_utils import (
    find_data_object_type,
    compute_new_data_file_path,
    link_data_file_paths,
    assembly_file_operations,
    get_workflow_id_from_scaffold_file,
)

DATA_DIR = Path(__file__).parent.absolute().joinpath("scripts/data")
NAPA_TEMPLATE = "../../../configs/re_iding_worklfows.yaml"
DATA_BASE_URL = "https://data.microbiomedata.org/data"
# BASE_DIR = "/global/cfs/cdirs/m3408/results"

# More constants for class types and set names
# data object types
BIOSAMPLE_TYPE = "nmdc:Biosample"
DATA_OBJECT_TYPE = "nmdc:DataObject"
MAGS_ANALYSIS_ACTIVITY_TYPE = "nmdc:MAGsAnalysisActivity"
METABOLOMICS_ANALYSIS_ACTIVITY_TYPE = "nmdc:MetabolomicsAnalysisActivity"
METAGENOME_ANNOTATION_ACTIVITY_TYPE = "nmdc:MetagenomeAnnotationActivity"
METAGENOME_ASSEMBLY_TYPE = "nmdc:MetagenomeAssembly"
METATRANSCRIPTOME_ACTIVITY_TYPE = "nmdc:MetatranscriptomeActivity"
NOM_ANALYSIS_ACTIVITY_TYPE = "nmdc:NomAnalysisActivity"
OMICS_PROCESSING_TYPE = "nmdc:OmicsProcessing"
READ_BASED_TAXONOMY_ANALYSIS_ACTIVITY_TYPE = "nmdc:ReadBasedTaxonomyAnalysisActivity"
READ_QC_ANALYSIS_ACTIVITY_TYPE = "nmdc:ReadQcAnalysisActivity"


# map data object types set names
DATA_OBJECT_TYPE_SET_MAP = {
    BIOSAMPLE_TYPE: BIOSAMPLE_SET,
    DATA_OBJECT_TYPE: DATA_OBJECT_SET,
    MAGS_ANALYSIS_ACTIVITY_TYPE: MAGS_ACTIVITY_SET,
    METABOLOMICS_ANALYSIS_ACTIVITY_TYPE: METABOLOMICS_ANALYSIS_ACTIVITY_SET,
    METAGENOME_ANNOTATION_ACTIVITY_TYPE: METAGENOME_ANNOTATION_ACTIVITY_SET,
    METAGENOME_ASSEMBLY_TYPE: METAGENOME_ASSEMBLY_SET,
    METATRANSCRIPTOME_ACTIVITY_TYPE: METATRANSCRIPTOME_ACTIVITY_SET,
    NOM_ANALYSIS_ACTIVITY_TYPE: NOM_ANALYSIS_ACTIVITY_SET,
    OMICS_PROCESSING_TYPE: OMICS_PROCESSING_SET,
    READ_BASED_TAXONOMY_ANALYSIS_ACTIVITY_TYPE: READ_BASED_TAXONOMY_ANALYSIS_ACTIVITY_SET,
    READ_QC_ANALYSIS_ACTIVITY_TYPE: READS_QC_SET
}



logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)


class ReIdTool:
    def __init__(self, api_client: NmdcRuntimeApi, data_dir: str,
                 template_file: str = None, identifiers_map: dict = None):
        self.api_client = api_client
        self.data_dir = data_dir
        if template_file is None:
            template_file = NAPA_TEMPLATE
        with open(template_file, "r") as f:
            self.workflow_template = yaml.safe_load(f)["Workflows"]
        # collector to track ID changes as (type, old_id, new_id)
        self.updated_record_identifiers = set()
        self.identifiers_map = identifiers_map


    def _workflow_template_for_type(self, workflow_type: str) -> Dict:
        """
        Return the workflow template for the given workflow name.
        """
        templates = []
        # There are some inconsistencies in the workflow names between
        # template and object records
        workflow_type = workflow_type.replace("QC", "Qc")
        if workflow_type == "nmdc:ReadbasedAnalysis":
            workflow_type = "nmdc:ReadBasedTaxonomyAnalysisActivity"
        if workflow_type == "nmdc:MetaT":
            workflow_type = "nmdc:MetatranscriptomeActivity"

        for t in self.workflow_template:
            type = t["Type"]
            if type == workflow_type:
                templates.append(t)

        if len(templates) == 0:
            raise ValueError(f"No workflow template found for {workflow_type}")
        elif len(templates) > 1:
            raise ValueError(
                f"Multiple workflow templates found for "
                f"{workflow_type}"
                )
        return templates[0]

    def data_object_template(self, workflow_type: str,
                             data_object_type: str) -> Dict:
        """
        Return the data object template for the given workflow name and data
        object type.
        """
        template = self._workflow_template_for_type(workflow_type)
        data_object_templates = [t for t in template["Outputs"] if
                                 t["data_object_type"] == data_object_type]
        if len(data_object_templates) == 0:
            raise ValueError(
                f"No data object template found for "
                f"{workflow_type} and {data_object_type}"
                )
        elif len(data_object_templates) > 1:
            raise ValueError(
                f"Multiple data object templates found for "
                f"{workflow_type} and {data_object_type}"
                )
        return data_object_templates[0]

    def update_omics_processing_has_output(self, db_record: Dict,
            new_db: NmdcDatabase) -> (NmdcDatabase):
        """
        Return a new Database instance with the omics processing record has_output
        data object IDs updated to new IDs.

        Note: This function assumes that there is only one omics processing record,
        and that id and name have already been updated.
        """
        check_for_single_omics_processing_record(db_record)
        omics_record = db_record[OMICS_PROCESSING_SET][0]
        # Strip out and keep has_output and strip out _id
        params = copy.deepcopy(omics_record)
        params.pop("has_output", [])
        params.pop("_id", None)
        # make a new omics processing record
        new_omics = OmicsProcessing(**params)

        # make new data objects with updated IDs
        old_do_ids = omics_record.get("has_output", [])
        if not old_do_ids:
            logger.warning(f"No data objects found for {omics_record['id']}")
            new_db.omics_processing_set.append(new_omics)
            return new_db
        for old_do_id in old_do_ids:
            old_do_rec = get_data_object_record_by_id(db_record, old_do_id)
            old_do_rec["data_object_type"] = "Metagenome Raw Reads"
            old_do_rec["type"] = "nmdc:DataObject"
            old_do_id = old_do_rec.get("id")
            params = copy.deepcopy(old_do_rec)
            params.pop("id", None)
            new_do_id = get_new_nmdc_id(NmdcDataObject(**old_do_rec), self.api_client, self.identifiers_map)
            self.updated_record_identifiers.add((DATA_OBJECT_SET, old_do_id, new_do_id))
            logger.info(f"nmdcDataObject\t{old_do_id}\t{new_do_id}")

            # Add new do ID to new OmicsProcessing has_output
            new_omics.has_output.append(new_do_id)
            # Make a new data object record with the new ID
            new_db.data_object_set.append(
                NmdcDataObject(**params, id=new_do_id)
            )
        new_db.omics_processing_set.append(new_omics)
        return new_db

    def update_reads_qc_analysis_activity_set(self, db_record: Dict,
            new_db: NmdcDatabase, update_links: bool = False) -> NmdcDatabase:
        """
        Return a new Database instance with the reads_qc_analysis_activity_set
        and its data objects updated to new IDs.
        """
        logger.info(
            f"Updating reads_qc_analysis_activity_set for "
            f"{db_record[OMICS_PROCESSING_SET][0]['id']}"
            )
        new_omics_processing = new_db.omics_processing_set[0]
        for reads_qc_rec in db_record.get(READS_QC_SET, []):
            # old records have non-conforming type
            activity_type = "nmdc:ReadQcAnalysisActivity"
            reads_qc_rec["type"] = activity_type
            omics_processing_id = new_omics_processing.id
            has_input = new_omics_processing.has_output
            
            activity_obj = nmdc.ReadQcAnalysisActivity(**reads_qc_rec)
            new_activity_id = get_new_nmdc_id(activity_obj, self.api_client, self.identifiers_map)

            self.updated_record_identifiers.add((READS_QC_SET, reads_qc_rec["id"], new_activity_id))
            logging.info(f"New activity id created for {omics_processing_id} activity type {activity_type}: {new_activity_id}")
            
            new_readsqc_base_dir = os.path.join(self.data_dir, omics_processing_id,
                                                new_activity_id)

            if update_links:
                logging.info(f"Making directory {new_readsqc_base_dir}")
                os.makedirs(new_readsqc_base_dir, exist_ok=True)
            else:
                logging.info(f"Skipping directory creation for {new_readsqc_base_dir}")

            updated_has_output = []
            # Get ReadQC data objects and update IDs
            for old_do_id in reads_qc_rec["has_output"]:
                logger.info(f"old_do_id: {old_do_id}")
                old_do_rec = get_data_object_record_by_id(db_record, old_do_id)
                data_object_type = find_data_object_type(old_do_rec)

                # Compute new file path and optionally update links
                new_file_path = compute_new_data_file_path(
                old_do_rec["url"], new_readsqc_base_dir, new_activity_id)
                logging.info(f"New file path computed for {data_object_type}: {new_file_path}")
                if update_links:
                    logging.info(f"Updating links for {old_do_rec['url']} to {new_file_path}")
                    link_data_file_paths(old_do_rec["url"], self.data_dir, new_file_path)

                new_do = self.make_new_data_object(
                    omics_processing_id, activity_type, new_activity_id, old_do_rec,
                    data_object_type,
                )
                self.updated_record_identifiers.add((DATA_OBJECT_SET, old_do_id, new_do.id))
                # add new data object to new database and update has_output
                new_db.data_object_set.append(new_do)
                updated_has_output.append(new_do.id)

            # Get new ReadQC activity set
            new_reads_qc = self._make_new_activity_set_object(
                omics_processing_id, new_activity_id, reads_qc_rec, has_input, updated_has_output
            )
            # update activity-specific properties
            unset_properties = [
                p for p in new_reads_qc.__dict__ if not new_reads_qc.__dict__[p]
            ]
            # check for that value in old record
            for p in unset_properties:
                if p in reads_qc_rec:
                    setattr(new_reads_qc, p, reads_qc_rec[p])

            new_db.read_qc_analysis_activity_set.append(new_reads_qc)
        return new_db

    def update_metagenome_assembly_set(self, db_record: Dict,
                                       new_db: NmdcDatabase, update_links: bool = False) -> (NmdcDatabase):
        """
        Return a new Database instance with the metagenome_assembly_set
        and its data objects updated to new IDs.
        """
        logger.info(f"Updating metagenome_assembly_set for "
                    f"{db_record[OMICS_PROCESSING_SET][0]['id']}")
        new_omics_processing = new_db.omics_processing_set[0]

        for assembly_rec in db_record.get(METAGENOME_ASSEMBLY_SET, []):
            activity_type = "nmdc:MetagenomeAssembly"
            omics_processing_id = new_omics_processing.id
            has_input = [self._get_input_do_id(new_db, "Filtered Sequencing Reads")]
            
            updated_has_output = []
            activity_obj = nmdc.MetagenomeAssembly(**assembly_rec)
            activity_obj.type = activity_type
            new_activity_id = get_new_nmdc_id(activity_obj, self.api_client, self.identifiers_map)

            self.updated_record_identifiers.add((METAGENOME_ASSEMBLY_TYPE, assembly_rec["id"], new_activity_id))
            logging.info(f"New activity id created for {omics_processing_id} activity type {activity_type}: {new_activity_id}")
            
            new_assembly_base_dir = os.path.join(self.data_dir, omics_processing_id,
                                                 new_activity_id)

            # make new directory is update_links is True
            if update_links:
                os.makedirs(new_assembly_base_dir, exist_ok=True)
                logging.info(f"Making directory {new_assembly_base_dir}")
            else:
                logging.info(f"Skipping directory creation for {new_assembly_base_dir}")

            # get the old workflow ID from the scaffolds file.
            # This is used to update the assembly file name

            for old_do_id in assembly_rec["has_output"]:
                logger.info(f"old_do_id: {old_do_id}")
                old_do_rec = get_data_object_record_by_id(db_record, old_do_id)
                data_object_type = find_data_object_type(old_do_rec)
                if not data_object_type:
                    logger.warning(f"Data object type not found for {old_do_id} - {old_do_rec['description']}")
                    continue
                old_url = old_do_rec.get("url")
                if not old_url:
                    logger.warning(f"Data object url not found for {old_do_id} - {old_do_rec['description']}")
                    old_url = f"{DATA_BASE_URL}/{omics_processing_id}/assembly/{old_do_rec['name']}"
                    logger.warning(f"Using inferred url: {old_url}")
                new_file_path = compute_new_data_file_path(old_url, new_assembly_base_dir, new_activity_id)

                if update_links:
                    updated_md5, updated_file_size = assembly_file_operations(
                    old_url, data_object_type, new_file_path, new_activity_id,
                        self.data_dir)
                    logging.info(f"Updated md5: {updated_md5}, updated file size: {updated_file_size}")
                else:
                    updated_md5 = old_do_rec.get("md5_checksum")
                    updated_file_size = old_do_rec.get("file_size_bytes")

                logging.info(f"New file path computed for {data_object_type}: {new_file_path}")

                #update md5 and file byte size in place to use _make_new_data_object function without functions
                old_do_rec["file_size_bytes"] = updated_file_size
                old_do_rec["md5_checksum"] = updated_md5
                new_do = self.make_new_data_object(
                    omics_processing_id, activity_type, new_activity_id, old_do_rec, data_object_type
                )
                self.updated_record_identifiers.add((DATA_OBJECT_SET, old_do_id, new_do.id))
                # add new data object to new database and update has_output
                new_db.data_object_set.append(new_do)
                updated_has_output.append(new_do.id)

            # Skip creating a new assembly if no typed data objects were found
            if not updated_has_output:
                logger.warning(f"No typed data objects found for {activity_type}")
                return new_db

            # Get new Metagenome Assembly activity set
            new_assembly = self._make_new_activity_set_object(
                omics_processing_id, new_activity_id, assembly_rec, has_input,
                updated_has_output
            )
            # update activity-specific properties
            # get new_assembly properties with no set value
            unset_properties = [
                p for p in new_assembly.__dict__ if not new_assembly.__dict__[p]
            ]
            # check for that value in old record
            for p in unset_properties:
                if p in assembly_rec:
                    setattr(new_assembly, p, assembly_rec[p])

            new_db.metagenome_assembly_set.append(new_assembly)
        return new_db

    def update_read_based_taxonomy_analysis_activity_set(self, db_record: Dict,
            new_db: NmdcDatabase, update_links: bool=False) -> (NmdcDatabase):
        """
        Return a new Database instance with the read_based_taxonomy_analysis_activity_set
        and its data objects updated to new IDs.
        """
        logger.info(f"Updating read_based_taxonomy_analysis_activity_set for "
                    f"{db_record[OMICS_PROCESSING_SET][0]['id']}")
        new_omics_processing = new_db.omics_processing_set[0]

        for read_based_rec in db_record.get(READ_BASED_TAXONOMY_ANALYSIS_ACTIVITY_SET, []):
            activity_type = "nmdc:ReadBasedTaxonomyAnalysisActivity"
            omics_processing_id = new_omics_processing.id
            has_input = [self._get_input_do_id(new_db, "Filtered Sequencing Reads")]
            activity_obj = nmdc.ReadBasedTaxonomyAnalysisActivity(**read_based_rec)
            activity_obj.type = activity_type
            new_activity_id = get_new_nmdc_id(activity_obj, self.api_client, self.identifiers_map)

            self.updated_record_identifiers.add((READ_BASED_TAXONOMY_ANALYSIS_ACTIVITY_SET, read_based_rec["id"],
                                               new_activity_id))
            logging.info(f"New activity id created for {omics_processing_id} activity type {activity_type}: {new_activity_id}")
            
            new_readbased_base_dir = os.path.join(self.data_dir, omics_processing_id,
                                                  new_activity_id)

            # make new directory is update_links is True
            if update_links:
                os.makedirs(new_readbased_base_dir, exist_ok=True)
                logging.info(f"Making directory {new_readbased_base_dir}")
            else:
                logging.info(f"Skipping directory creation for {new_readbased_base_dir}")
            
            updated_has_output = []
            for old_do_id in read_based_rec["has_output"]:
                logger.info(f"old_do_id: {old_do_id}")
                old_do_rec = get_data_object_record_by_id(db_record, old_do_id)
                data_object_type = find_data_object_type(old_do_rec)
                if not data_object_type:
                    logger.warning(f"Data object type not found for {old_do_id} - {old_do_rec['description']}")
                    continue

                # Compute new file path and optionally update links
                new_file_path = compute_new_data_file_path(
                old_do_rec["url"], new_readbased_base_dir, new_activity_id)
                logging.info(f"New file path computed for {data_object_type}: {new_file_path}")
                if update_links:
                    logging.info(f"Updating links for {old_do_rec['url']} to {new_file_path}")
                    link_data_file_paths(old_do_rec["url"], self.data_dir, new_file_path)
                
                new_do = self.make_new_data_object(
                    omics_processing_id, activity_type, new_activity_id, old_do_rec, data_object_type
                )
                self.updated_record_identifiers.add((DATA_OBJECT_SET, old_do_id, new_do.id))
                # add new data object to new database and update has_output
                new_db.data_object_set.append(new_do)
                updated_has_output.append(new_do.id)

            # Skip creating a new assembly if no typed data objects were found
            if not updated_has_output:
                logger.warning(f"No typed data objects found for {activity_type}")
                return new_db

            # Get new ReadBasedTaxonomyAnalysisActivity activity set
            new_read_based = self._make_new_activity_set_object(
                omics_processing_id, new_activity_id,read_based_rec, has_input,
                updated_has_output
            )
            # update activity-specific properties
            # get new_read_based properties with no set value
            unset_properties = [
                p for p in new_read_based.__dict__ if not new_read_based.__dict__[p]
            ]
            # check for that value in old record
            for p in unset_properties:
                if p in read_based_rec:
                    setattr(new_read_based, p, read_based_rec[p])

            new_db.read_based_taxonomy_analysis_activity_set.append(new_read_based)

        return new_db

    def update_metatranscriptome_activity_set(self, db_record: Dict,
                                              new_db: NmdcDatabase, update_links: bool = False) -> (NmdcDatabase):
        """
        Return a new Database instance with the metatranscriptome_activity_set
        and its data objects updated to new IDs.
        """
        metatranscriptome_records = db_record.get(METATRANSCRIPTOME_ACTIVITY_SET, [])
        if not metatranscriptome_records:
            logger.info(f"No metatranscriptome_activity_set found for {db_record[OMICS_PROCESSING_SET][0]['id']}")
            return new_db
        logger.info(f"Updating metatranscriptome_activity_set for "
                    f"{db_record[OMICS_PROCESSING_SET][0]['id']}")
        new_omics_processing = new_db.omics_processing_set[0]

        for metatranscriptome_rec in metatranscriptome_records:
            # old records have non-conforming type e.g. nmdc:MetaT,
            # nmdc:metaT etc. - fix it
            activity_type = "nmdc:MetatranscriptomeActivity"
            metatranscriptome_rec["type"] = activity_type
            omics_processing_id = new_omics_processing.id
            has_input = [self._get_input_do_id(new_db, "Filtered Sequencing Reads")]

            activity_obj = nmdc.MetatranscriptomeActivity(**metatranscriptome_rec)
            activity_obj.type = activity_type
            new_activity_id = get_new_nmdc_id(activity_obj, self.api_client, self.identifiers_map)

            self.updated_record_identifiers.add((METATRANSCRIPTOME_ACTIVITY_SET, metatranscriptome_rec["id"],
                                               new_activity_id))
            logging.info(f"New activity id created for {omics_processing_id} activity type {activity_type}: {new_activity_id}")
            new_metatranscriptome_base_dir = os.path.join(self.data_dir, omics_processing_id,
                                                          new_activity_id)

            # make new directory is update_links is True
            if update_links:
                os.makedirs(new_metatranscriptome_base_dir, exist_ok=True)
                logging.info(f"Making directory {new_metatranscriptome_base_dir}")
            else:
                logging.info(f"Skipping directory creation for {new_metatranscriptome_base_dir}")

            updated_has_output = []
            # Get Metatranscriptome data objects and update IDs
            for old_do_id in metatranscriptome_rec["has_output"]:
                logger.info(f"old_do_id: {old_do_id}")
                old_do_rec = get_data_object_record_by_id(db_record, old_do_id)
                # there are some data objects that are not in the database
                if not old_do_rec:
                    logger.warning(f"Data object record not found for {old_do_id}")
                    continue

                data_object_type = find_data_object_type(old_do_rec)
                logging.info(f"data_object_type: {data_object_type}")
                # TODO: how do we handle data objects w/o type?
                if not data_object_type:
                    logger.warning(f"Data object type not found for {old_do_id} - {old_do_rec['description']}")
                    continue
                # link data object to new location
                new_file_path = compute_new_data_file_path(
                    old_do_rec["url"], new_metatranscriptome_base_dir, new_activity_id)
                logging.info(f"New file path computed for {data_object_type}: {new_file_path}")
                if update_links:
                    logging.info(f"Updating links for {old_do_rec['url']} to {new_file_path}")
                    link_data_file_paths(old_do_rec["url"], self.data_dir, new_file_path)


                new_do = self.make_new_data_object(
                    omics_processing_id, activity_type, new_activity_id, old_do_rec, data_object_type
                )
                self.updated_record_identifiers.add((DATA_OBJECT_SET, old_do_id, new_do.id))
                # add new data object to new database and update has_output
                new_db.data_object_set.append(new_do)
                updated_has_output.append(new_do.id)


            # Skip creating a new assembly if no typed data objects were found
            if not updated_has_output:
                logger.warning(f"No typed data objects found for {activity_type}")
                return new_db
            # Get new Metatranscriptome activity set
            new_metatranscriptome = self._make_new_activity_set_object(
                omics_processing_id, new_activity_id, metatranscriptome_rec, has_input,
                updated_has_output
            )
            # update activity-specific properties
            # get new_metatranscriptome properties with no set value
            unset_properties = [
                p for p in new_metatranscriptome.__dict__ if not new_metatranscriptome.__dict__[p]
            ]
            # check for that value in old record
            for p in unset_properties:
                if p in metatranscriptome_rec:
                    setattr(new_metatranscriptome, p, metatranscriptome_rec[p])

            new_db.metatranscriptome_activity_set.append(new_metatranscriptome)
        return new_db


    def _get_input_do_id(self, new_db, data_object_type: str):
        """Returns the string representation of a data object id given data object type"""
        
        for rec in new_db.data_object_set:
            if str(rec.data_object_type) == data_object_type:
                return str(rec.id)        

    def _make_new_activity_set_object(self, omics_processing_id: str, new_activity_id: str,
            activity_set_rec: Dict, has_input: List,
            has_output: List) -> WorkflowExecutionActivity:
        """
        Return a new activity set object with updated IDs and common properties:
        - id, name, git_url, version, part_of, execution_resource,
        started_at_time, ended_at_time, was_informed_by, type, has_input,
        has_output
        """
        activity_type = activity_set_rec["type"].replace("QC", "Qc")
        if activity_type == "nmdc:ReadbasedAnalysis":
            activity_type = "nmdc:ReadBasedTaxonomyAnalysisActivity"
        if activity_type == "nmdc:ReadBasedAnalysisActivity":
            activity_type = "nmdc:ReadBasedTaxonomyAnalysisActivity"
        if activity_type == "nmdc:MetaT":
            activity_type = "nmdc:MetatranscriptomeActivity"
        template = self._workflow_template_for_type(activity_type)
        activity_class = getattr(nmdc, template["ActivityRange"])
        
        logger.info(
            f"{activity_type}\t{activity_set_rec['id']}\t{new_activity_id}"
            )
        activity = activity_class(
            id=new_activity_id,
            name=template["Activity"]["name"].replace("{id}", omics_processing_id),
            git_url=template["Git_repo"], version=template["Version"],
            part_of=[omics_processing_id],
            execution_resource="NERSC-Cori",
            started_at_time=activity_set_rec["started_at_time"],
            has_input=has_input,
            has_output=has_output,
            ended_at_time=activity_set_rec["ended_at_time"],
            was_informed_by=omics_processing_id,
            type=template["Type"],
        )
        return activity

    def make_new_data_object(self, omics_processing_id: str,
                             activity_type: str,
                             new_activity_id: str,
                             data_object_record: Dict,
                             data_object_type: str) -> NmdcDataObject:
        """
        Return a new data object with updated IDs.
        """
        template = self.data_object_template(
            activity_type, data_object_type
            )
        data_obj = NmdcDataObject(**data_object_record)
        data_obj.type = "nmdc:DataObject"
        new_data_object_id = get_new_nmdc_id(data_obj, self.api_client, self.identifiers_map)
        self.updated_record_identifiers.add((DATA_OBJECT_SET, data_object_record["id"], new_data_object_id))
        logger.info(f"nmdcDataObject\t{data_object_record['id']}\t{new_data_object_id}")
        new_description = re.sub(
            "[^ ]+$", f"{omics_processing_id}", data_object_record["description"]
        )
        logger.info(f"new_description: {new_description}")
        new_filename = self._make_new_filename(new_activity_id, data_object_record)
        logger.info(f"new_filename: {new_filename}")
        new_url = (f"{DATA_BASE_URL}/{omics_processing_id}/{new_activity_id}"
                   f"/{new_filename}")

        data_object = NmdcDataObject(
            id=new_data_object_id,
            name=new_filename,
            description=new_description,
            type="nmdc:DataObject",
            file_size_bytes=data_object_record["file_size_bytes"],
            md5_checksum=data_object_record.get("md5_checksum"),
            url=new_url,
            data_object_type=data_object_type,
            )
        return data_object

    def _make_new_filename(self, new_activity_id: str,
            data_object_record: Dict) -> str:
        """
        Return the updated filename.
        """
        filename = data_object_record["url"].split("/")[-1]
        file_extenstion = filename.lstrip("nmdc_").split("_", maxsplit=1)[-1]
        new_filename = f"{new_activity_id}_{file_extenstion}".replace(":",
                                                                         "_")
        return new_filename


def compare_models(model, updated_model)-> dict:
    """
    Compare two nmdc dataclass models and return a dictionary of differences
    """
    model_dict = asdict(model)
    updated_model_dict = asdict(updated_model)
    diff = {}
    for key in model_dict.keys():
        if model_dict[key] != updated_model_dict[key]:
            diff[key] = updated_model_dict[key]
    return diff


def get_new_nmdc_id(nmdc_object, api_client, identifiers_map: dict = None) -> str:
    """
    Get a nmdc ID from the identifiers_map or mint a new one
    """
    try:
        object_type_code = nmdc_object.type
    except AttributeError:
        raise ValueError(f"Object does not have a type attribute: {nmdc_object}")

    # Fix typo "ndmc:" to "nmdc:"
    if object_type_code.startswith("ndmc:"):
        object_type_code = object_type_code.replace("ndmc:", "nmdc:")
    logging.info(f"Getting new ID for {object_type_code} {nmdc_object.id}")
    if identifiers_map and not DATA_OBJECT_TYPE_SET_MAP.get(object_type_code):
        raise ValueError(f"Set name not found for {object_type_code}")

    if identifiers_map and (DATA_OBJECT_TYPE_SET_MAP[object_type_code], nmdc_object.id) in identifiers_map:
        new_id = identifiers_map[(DATA_OBJECT_TYPE_SET_MAP[object_type_code], nmdc_object.id)]
        logging.info(f"Found new ID in identifiers_map: {new_id}")
    else:
        new_id = api_client.minter(object_type_code)
        # For new workflow IDs, we assume that the .version is 1
        if new_id.startswith("nmdc:wf") and not new_id.endswith(".1"):
            new_id = new_id + ".1"
        logging.info(f"Minted new ID: {new_id}")
    return new_id

def update_biosample(biosample: nmdc.Biosample, nmdc_study_id: str, api_client, identifiers_map: dict = None) -> nmdc.Biosample:
    updated_biosample= deepcopy(biosample)
    # Ensure that type is set to nmdc:Biosample
    updated_biosample.type = "nmdc:Biosample"
    # Check if we need to update the biosample ID and add the legacy ID to the alternate identifiers
    if not updated_biosample.id.startswith("nmdc:bsm-"):
        updated_biosample = _update_biosample_alternate_identifiers(updated_biosample, updated_biosample.id)
        new_biosample_id = get_new_nmdc_id(updated_biosample, api_client, identifiers_map)
        updated_biosample.id = new_biosample_id

    # Handle the part_of array
    part_of = updated_biosample.part_of
    # Remove anything that is not a NMDC study ID
    part_of = [id for id in part_of if id.startswith("nmdc:sty-")]
    # Add the new study ID to the part_of array
    if nmdc_study_id not in part_of:
        part_of.append(nmdc_study_id)
        updated_biosample.part_of = part_of

    return updated_biosample

def _get_biosample_legacy_id(biosample: nmdc.Biosample) -> str:
    if not biosample.id.startswith("nmdc:bsm-"):
        return biosample.id
    elif biosample.gold_biosample_identifiers:
        return biosample.gold_biosample_identifiers[0]
    elif biosample.emsl_biosample_identifiers:
        return biosample.emsl_biosample_identifiers[0]
    elif biosample.igsn_biosample_identifiers:
        return biosample.igsn_biosample_identifiers[0]
    else:
        return biosample.id


def update_omics_processing(omics_processing: nmdc.OmicsProcessing, nmdc_study_id: str, nmdc_biosample_id: str,
                            api_client: NmdcRuntimeApi, identifiers_map: dict=None) -> nmdc.OmicsProcessing:
    """
    Update the omics processing record with the new ID
    """
    updated_omics_processing = deepcopy(omics_processing)
    # Ensure that type is set to nmdc:OmicsProcessing
    updated_omics_processing.type = "nmdc:OmicsProcessing"
    # Check if we need to update the omics processing ID and add the legacy ID to the alternate identifiers
    if not updated_omics_processing.id.startswith("nmdc:omprc-"):
        updated_omics_processing = _update_omics_processing_alternative_identifiers(updated_omics_processing, updated_omics_processing.id)
        new_omics_processing_id = get_new_nmdc_id(updated_omics_processing, api_client, identifiers_map)
        updated_omics_processing.id = new_omics_processing_id

    # Update the has_input array
    has_input = updated_omics_processing.has_input
    # Only Biosamples (nmdc;bsm-*) or ProcessedSamples (nmdc:prcsm-*) should be in the has_input array
    has_input = [id for id in has_input if id.startswith("nmdc:bsm-") or id.startswith("nmdc:prcsm-")]
    if nmdc_biosample_id not in has_input:
        has_input.append(nmdc_biosample_id)
        updated_omics_processing.has_input = has_input
        logging.info(f"Added new biosample ID to has_input: {nmdc_biosample_id}")

    # Update the part_of array with the new study ID
    part_of = updated_omics_processing.part_of
    # Remove gold: IDs from part_of array
    part_of = [id for id in part_of if not id.startswith("gold:")]
    if nmdc_study_id not in part_of:
        part_of.append(nmdc_study_id)
        updated_omics_processing.part_of = part_of
        logging.info(f"Added new study ID to part_of: {nmdc_study_id}")

    return updated_omics_processing


def _get_omics_processing_legacy_id(omics_processing: nmdc.OmicsProcessing) -> str:
    if not omics_processing.id.startswith("nmdc:omprc-"):
        return omics_processing.id
    elif omics_processing.gold_sequencing_project_identifiers:
        return omics_processing.gold_sequencing_project_identifiers[0]
    elif omics_processing.alternative_identifiers:
        return omics_processing.alternative_identifiers[0]
    else:
        return omics_processing.id


def _update_biosample_alternate_identifiers(biosample: nmdc.Biosample, legacy_biosample_id: str) -> nmdc.Biosample:
    """
    Update the appropriate alt identifiers slot depending on the Biosample legacy ID:
    - gold_biosample_identifiers for legacy IDs starting with 'gold:'
    - igsn_biosample_identifiers for legacy IDs starting with 'igsn:'
    - emsl_biosample_identifiers for legacy IDs starting with 'emsl:'
    """
    if legacy_biosample_id.startswith("gold:"):
        if legacy_biosample_id not in biosample.gold_biosample_identifiers:
            biosample.gold_biosample_identifiers.append(legacy_biosample_id)
            logging.info(f"Added legacy biosample ID to gold_biosample_identifiers: {legacy_biosample_id}")
    elif legacy_biosample_id.startswith("igsn:"):
        if legacy_biosample_id not in biosample.igsn_biosample_identifiers:
            biosample.igsn_biosample_identifiers.append(legacy_biosample_id)
            logging.info(f"Added legacy biosample ID to igsn_biosample_identifiers: {legacy_biosample_id}")
    elif legacy_biosample_id.startswith("emsl:"):
        if legacy_biosample_id not in biosample.emsl_biosample_identifiers:
            biosample.emsl_biosample_identifiers.append(legacy_biosample_id)
            logging.info(f"Added legacy biosample ID to emsl_biosample_identifiers: {legacy_biosample_id}")
    else:
        logging.warning(f"Unknown legacy ID format: {legacy_biosample_id}")
    return biosample


def _update_omics_processing_alternative_identifiers(omics_processing: nmdc.OmicsProcessing,
                                                     legacy_omics_processing_id: str) -> nmdc.OmicsProcessing:
    """
    Update the appropriate alt identifiers slot depending on the OmicsProcessing legacy ID:
    - gold_sequencing_project_identifiers for legacy IDs starting with 'gold:'
    - alternative_identifiers for legacy IDs starting with 'emsl:'
    """
    if legacy_omics_processing_id.startswith("gold:"):
        if legacy_omics_processing_id not in omics_processing.gold_sequencing_project_identifiers:
            omics_processing.gold_sequencing_project_identifiers.append(legacy_omics_processing_id)
            logging.info(f"Added legacy omics processing ID to gold_sequencing_project_identifiers: {legacy_omics_processing_id}")
    elif legacy_omics_processing_id.startswith("emsl:"):
        if legacy_omics_processing_id not in omics_processing.alternative_identifiers:
            omics_processing.alternative_identifiers.append(legacy_omics_processing_id)
            logging.info(f"Added legacy omics processing ID to alternative_identifiers: {legacy_omics_processing_id}")
    else:
        logging.warning(f"Unknown legacy ID format: {legacy_omics_processing_id}")
    return omics_processing

def update_omics_output_data_object(
        data_object: nmdc.DataObject, updated_omics_processing: nmdc.OmicsProcessing,
        api_client: NmdcRuntimeApi, identifiers_map: dict=None) -> nmdc.DataObject:
    """
    Update the data object record with the new ID, and add the legacy ID to the alternate identifiers
    """
    updated_data_object = deepcopy(data_object)
    # Check if we need to update the data object ID and set the alternative identifiers to the legacy ID
    if not updated_data_object.id.startswith("nmdc:dobj-"):
        # Only update alternative_identifiers and was_generated_by for Metabolomics and NOM
        if updated_omics_processing.omics_type.has_raw_value in (
            "Metabolomics", "Organic Matter Characterization"
        ):
            updated_data_object.alternative_identifiers = [data_object.id]
        new_data_object_id = get_new_nmdc_id(updated_data_object, api_client, identifiers_map)
        updated_data_object.id = new_data_object_id
    # Set the was_generated_by to the updated omics processing ID if it exists
    if data_object.was_generated_by:
        updated_data_object.was_generated_by = updated_omics_processing.id
    return updated_data_object


def update_metabolomics_or_nom_data_object(data_object: nmdc.DataObject, api_client: NmdcRuntimeApi,
                                           identifiers_map: dict = None, was_generated_by=None) -> nmdc.DataObject:
    """
    Update for data object from Metabolomics or NOM Analysis Activity
    Special case data objects get was_generated_by set to the metabolomics or NOM analysis activity ID
    """
    logging.info(f"Updating data object: {data_object.id}")
    logging.info(f"was_generated_by: {was_generated_by}")
    updated_data_object = deepcopy(data_object)
    # Ensure that type is set to nmdc:DataObject
    updated_data_object.type = "nmdc:DataObject"

    # Check if we need to update the data object ID
    if not updated_data_object.id.startswith("nmdc:dobj-"):
        new_data_object_id = get_new_nmdc_id(updated_data_object, api_client, identifiers_map)
        updated_data_object.id = new_data_object_id
    if was_generated_by:
        updated_data_object.was_generated_by = was_generated_by

    return updated_data_object


def _update_metabolomics_analysis_activity(activity_id: str, metabolomics_analysis_activity:
nmdc.MetabolomicsAnalysisActivity, nmdc_omics_processing_id: str, nmdc_input_data_object_id: str,
                                           nmdc_output_data_object_ids: List[str], nmdc_calibration_data_object_id: str,
                                           identifiers_map: dict = None) -> nmdc.MetabolomicsAnalysisActivity:
    """
    Update the metabolomics activity.
    A valid nmdc activity_id starts with 'nmdc:wfmb-' and must be provided.
    """
    if not activity_id.startswith("nmdc:wfmb-"):
        raise ValueError(f"Invalid metabolomics analysis activity ID: {activity_id}")
    updated_metabolomics_analysis_activity = deepcopy(metabolomics_analysis_activity)
    # Ensure that type is set to nmdc:MetabolomicsAnalysisActivity
    updated_metabolomics_analysis_activity.type = "nmdc:MetabolomicsAnalysisActivity"
    updated_metabolomics_analysis_activity.id = activity_id
    updated_metabolomics_analysis_activity.was_informed_by = nmdc_omics_processing_id
    updated_metabolomics_analysis_activity.has_input = [nmdc_input_data_object_id]
    updated_metabolomics_analysis_activity.has_output = nmdc_output_data_object_ids
    updated_metabolomics_analysis_activity.has_calibration = nmdc_calibration_data_object_id

    return updated_metabolomics_analysis_activity


def _update_nom_analysis_activity(
        activity_id: str,
        nom_analysis_activity: nmdc.NomAnalysisActivity,
        nmdc_omics_processing_id: str, nmdc_input_data_object_id: str,
        nmdc_output_data_object_ids: List[str],
        identifiers_map: dict = None) -> nmdc.NomAnalysisActivity:
    """
    Update the NOM analysis activity record with the new ID
    """
    if not activity_id.startswith("nmdc:wfnom-"):
        raise ValueError(f"Invalid NOM analysis activity ID: {activity_id}")
    updated_nom_analysis_activity = deepcopy(nom_analysis_activity)
    # Ensure that type is set to nmdc:NomAnalysisActivity
    updated_nom_analysis_activity.type = "nmdc:NomAnalysisActivity"

    updated_nom_analysis_activity.id = activity_id
    updated_nom_analysis_activity.was_informed_by = nmdc_omics_processing_id
    updated_nom_analysis_activity.has_input = [nmdc_input_data_object_id]
    updated_nom_analysis_activity.has_output = nmdc_output_data_object_ids

    return updated_nom_analysis_activity


def get_updates_for_metabolomics_or_nom(omics_processing, updated_omics_processing, api_client, db_client,
                                        identifiers_map, updated_record_identifiers, updates):
    """
    Update Metabolomics or NOM Analysis Activity records and their associated data objects.
    Returns updated_omics_processing, updated_record_identifiers, and updates dictionaries.
    """
    # If either the omics_processing or updated_omics_processing is not Metabolomics or NOM, raise an error
    if omics_processing.omics_type.has_raw_value not in ("Metabolomics", "Organic Matter Characterization"):
        raise ValueError(f"Omics Processing omics_type is not Metabolomics or NOM: {omics_processing.omics_type.has_raw_value}")
    if updated_omics_processing.omics_type.has_raw_value not in ("Metabolomics", "Organic Matter Characterization"):
        raise ValueError(f"Updated Omics Processing omics_type is not Metabolomics or NOM: {updated_omics_processing.omics_type.has_raw_value}")


    # OmicsProcessing has_output goes to the Activity's has_input
    # We assume there is only one data object in has_output
    omics_processing_output_id = omics_processing.has_output[0]
    omics_processing_output_record = db_client["data_object_set"].find_one(
        {"id": omics_processing_output_id}
    )
    omics_processing_output__id = omics_processing_output_record.pop("_id")
    omics_processing_output_data_object = nmdc.DataObject(**omics_processing_output_record)
    updated_omics_processing_output_data_object = update_omics_output_data_object(
        omics_processing_output_data_object, updated_omics_processing, api_client, identifiers_map
    )
    # Update the parent OmicsProcessing record with the new has_output data object
    updated_omics_processing.has_output = [updated_omics_processing_output_data_object.id]

    if omics_processing_output_data_object.id != updated_omics_processing_output_data_object.id:
        updated_record_identifiers.add(
            ("data_object_set", omics_processing_output_data_object.id,
             updated_omics_processing_output_data_object.id)
        )
    omics_processing_output_update = compare_models(
        omics_processing_output_data_object,
        updated_omics_processing_output_data_object
    )
    if omics_processing_output_update:
        updates["data_object_set"][omics_processing_output__id] = (omics_processing_output_data_object,
                                                                   omics_processing_output_update)

    # ====== Metabolomics Analysis Activity Update ======
    # Find all Metabolomics Analysis Activity records was_informed_by either OmicsProcessing
    # and has_input either data object
    omics_processing_ids = [omics_processing.id, updated_omics_processing.id]
    data_object_ids = [omics_processing_output_data_object.id, updated_omics_processing_output_data_object.id]
    activity_query = {
        "$and": [
            {"was_informed_by": {"$in": omics_processing_ids}},
            {"has_input": {"$in": data_object_ids}}
        ]
    }
    if updated_omics_processing.omics_type.has_raw_value == "Metabolomics":
        set_name = "metabolomics_analysis_activity_set"
    else:
        set_name = "nom_analysis_activity_set"
    activity_records = db_client[set_name].find(activity_query)
    logging.info(f"Found {len(list(activity_records.clone()))} Records for {set_name}")

    for activity_record in activity_records:
        activity__id = activity_record.pop("_id")

        if updated_omics_processing.omics_type.has_raw_value == "Metabolomics":
            activity = nmdc.MetabolomicsAnalysisActivity(**activity_record)
        else:
            activity = nmdc.NomAnalysisActivity(**activity_record)

        updated_activity_id = get_new_nmdc_id(activity, api_client, identifiers_map)

        # has_output data objects
        activity_has_output_ids = activity.has_output
        updated_activity_has_output_ids = []
        for activity_has_output_id in activity_has_output_ids:
            activity_output_record = db_client["data_object_set"].find_one({"id": activity_has_output_id})
            activity_output__id = activity_output_record.pop("_id")
            activity_output_data_object = nmdc.DataObject(**activity_output_record)
            # Update the data object record
            updated_activity_output_data_object = update_metabolomics_or_nom_data_object(
                activity_output_data_object, api_client, identifiers_map, was_generated_by=updated_activity_id
                )
            updated_activity_has_output_ids.append(updated_activity_output_data_object.id)
            if activity_output_data_object.id != updated_activity_output_data_object.id:
                updated_record_identifiers.add(
                    ("data_object_set", activity_output_data_object.id,
                     updated_activity_output_data_object.id)
                )
            activity_output_data_object_update = compare_models(
                activity_output_data_object, updated_activity_output_data_object
            )
            if activity_output_data_object_update:
                updates["data_object_set"][activity_output__id] = (
                    activity_output_data_object, activity_output_data_object_update)

        # has_calibration_data data object for some activities
        if updated_omics_processing.omics_type.has_raw_value == "Metabolomics":
            calibration_data_object_id = activity.has_calibration
            calibration_data_object_record = db_client["data_object_set"].find_one(
                {"id": calibration_data_object_id}
            )
            calibration_data_object__id = calibration_data_object_record.pop("_id")
            calibration_data_object = nmdc.DataObject(**calibration_data_object_record)
            updated_calibration_data_object = update_metabolomics_or_nom_data_object(
                calibration_data_object, api_client, identifiers_map
                )
            if calibration_data_object.id != updated_calibration_data_object.id:
                updated_record_identifiers.add(
                    ("data_object_set", calibration_data_object.id, updated_calibration_data_object.id)
                )
            calibration_data_object_update = compare_models(
                calibration_data_object, updated_calibration_data_object
            )
            if calibration_data_object_update:
                updates["data_object_set"][calibration_data_object__id] = (
                    calibration_data_object, calibration_data_object_update)

            # Update the Metabolomics Analysis Activity record
            updated_metabolomics_analysis_activity = _update_metabolomics_analysis_activity(
                activity_id=updated_activity_id, metabolomics_analysis_activity=activity,
                nmdc_omics_processing_id=updated_omics_processing.id,
                nmdc_input_data_object_id=updated_omics_processing_output_data_object.id,
                nmdc_output_data_object_ids=updated_activity_has_output_ids,
                nmdc_calibration_data_object_id=updated_calibration_data_object.id, identifiers_map=identifiers_map
                )
            if activity.id != updated_metabolomics_analysis_activity.id:
                updated_record_identifiers.add(
                    ("metabolomics_analysis_activity_set", activity.id, updated_metabolomics_analysis_activity.id)
                )
            metabolomics_analysis_activity_update = compare_models(activity, updated_metabolomics_analysis_activity)
            if metabolomics_analysis_activity_update:
                updates["metabolomics_analysis_activity_set"][activity__id] = (
                    activity, metabolomics_analysis_activity_update
                )

        else:
            # Update the NOM Analysis Activity record
            updated_nom_analysis_activity = _update_nom_analysis_activity(
                activity_id=updated_activity_id,
                nom_analysis_activity=activity,
                nmdc_omics_processing_id=updated_omics_processing.id,
                nmdc_input_data_object_id=updated_omics_processing_output_data_object.id,
                nmdc_output_data_object_ids=updated_activity_has_output_ids,
                identifiers_map=identifiers_map
            )
            if activity.id != updated_nom_analysis_activity.id:
                updated_record_identifiers.add(
                    ("nom_analysis_activity_set", activity.id, updated_nom_analysis_activity.id)
                )
            nom_analysis_activity_update = compare_models(activity, updated_nom_analysis_activity)
            if nom_analysis_activity_update:
                updates["nom_analysis_activity_set"][activity__id] = (
                    activity, nom_analysis_activity_update
                )

    return updated_omics_processing, updated_record_identifiers, updates


def write_updated_record_identifiers(updated_record_identifiers, nmdc_study_id):
    # Create a directory for the study if it doesn't exist
    study_dir = DATA_DIR.joinpath(nmdc_study_id)
    # Write the updated record identifiers to a tsv file using csv writer
    updated_record_identifiers_file = study_dir.joinpath(f"{nmdc_study_id}_updated_record_identifiers.tsv")
    # Check if the file already exists - if so, append to it
    if updated_record_identifiers_file.exists():
        logging.info(f"Appending to existing file: {updated_record_identifiers_file}")
        mode = "a"
    else:
        logging.info(f"Creating new file: {updated_record_identifiers_file}")
        mode = "w"

    logging.info(
        f"Writing {len(updated_record_identifiers)} updated record identifiers to {updated_record_identifiers_file}"
        )
    with open(updated_record_identifiers_file, mode) as f:
        writer = csv.writer(f, delimiter="\t")
        if mode == "w":
            writer.writerow(["collection_name", "legacy_id", "new_id"])
        for record in updated_record_identifiers:
            writer.writerow(record)
