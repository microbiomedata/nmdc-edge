# nmdc_automation/nmddc_automation/re_iding/base.py
"""
base.py - Provides classes and functions for re-ID-ing NMDC metagenome workflow
records and data objects.
"""
import copy
import logging
from typing import Dict, List
import os
import re
import yaml

from nmdc_schema.nmdc import DataObject as NmdcDataObject, \
    Database as NmdcDatabase, OmicsProcessing, WorkflowExecutionActivity
import nmdc_schema.nmdc as nmdc

from nmdc_automation.api import NmdcRuntimeApi
from nmdc_automation.re_iding.db_utils import (OMICS_PROCESSING_SET,
                                               READS_QC_SET,
                                               METAGENOME_ASSEMBLY_SET,
                                                METATRANSCRIPTOME_ACTIVITY_SET,
                                               check_for_single_omics_processing_record,
                                               get_data_object_record_by_id,
                                               get_omics_processing_id)
from nmdc_automation.re_iding.file_utils import (find_data_object_type,
                                                compute_new_paths,
                                                get_new_paths,
                                                assembly_file_operations)

NAPA_TEMPLATE = "../../../configs/re_iding_worklfows.yaml"
DATA_BASE_URL = "https://data.microbiomedata.org/data"
# BASE_DIR = "/global/cfs/cdirs/m3408/results"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)


class ReIdTool:
    def __init__(self, api_client: NmdcRuntimeApi, data_dir: str,
                 template_file: str = None, iteration: str = "1"):
        self.api_client = api_client
        self.data_dir = data_dir
        self.workflow_iteration = iteration
        if template_file is None:
            template_file = NAPA_TEMPLATE
        with open(template_file, "r") as f:
            self.workflow_template = yaml.safe_load(f)["Workflows"]

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
        for old_do_id in omics_record["has_output"]:
            old_do_rec = get_data_object_record_by_id(db_record, old_do_id)
            old_do_rec["data_object_type"] = "Metagenome Raw Reads"
            old_do_id = old_do_rec.get("id")
            params = copy.deepcopy(old_do_rec)
            params.pop("id", None)
            new_do_id = self.api_client.minter("nmdc:DataObject")
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
            new_db: NmdcDatabase) -> (NmdcDatabase):
        """
        Return a new Database instance with the reads_qc_analysis_activity_set
        and its data objects updated to new IDs.
        """
        logger.info(
            f"Updating reads_qc_analysis_activity_set for "
            f"{db_record[OMICS_PROCESSING_SET][0]['id']}"
            )
        new_omics_processing = new_db.omics_processing_set[0]
        for reads_qc_rec in db_record[READS_QC_SET]:
            # old records have non-conforming type
            activity_type = "nmdc:ReadQcAnalysisActivity"
            omics_processing_id = new_omics_processing.id
            has_input = new_omics_processing.has_output
            
            new_activity_id = self.api_client.minter(activity_type) + "." + self.workflow_iteration
            logging.info(f"New activity id created for {omics_processing_id} activity type {activity_type}: {new_activity_id}")
            
            new_readsqc_base_dir = os.path.join(self.data_dir, omics_processing_id,
                                                new_activity_id)
            os.makedirs(new_readsqc_base_dir, exist_ok=True)

            updated_has_output = []
            # Get ReadQC data objects and update IDs
            for old_do_id in reads_qc_rec["has_output"]:
                logger.info(f"old_do_id: {old_do_id}")
                old_do_rec = get_data_object_record_by_id(db_record, old_do_id)
                data_object_type = find_data_object_type(old_do_rec)
                new_file_path = compute_new_paths(
                old_do_rec["url"], new_readsqc_base_dir, new_activity_id, self.data_dir
                )
                logging.info(f"New file path computed for {data_object_type}: {new_file_path}")
                new_do = self.make_new_data_object(
                    omics_processing_id, activity_type, new_activity_id, old_do_rec,
                    data_object_type,
                )
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
            new_db: NmdcDatabase) -> (NmdcDatabase):
        """
        Return a new Database instance with the metagenome_assembly_set
        and its data objects updated to new IDs.
        """
        logger.info(f"Updating metagenome_assembly_set for "
                    f"{db_record[OMICS_PROCESSING_SET][0]['id']}")
        new_omics_processing = new_db.omics_processing_set[0]

        for assembly_rec in db_record[METAGENOME_ASSEMBLY_SET]:
            activity_type = "nmdc:MetagenomeAssembly"
            omics_processing_id = new_omics_processing.id
            has_input = [self._get_input_do_id(new_db, "Filtered Sequencing Reads")]
            
            updated_has_output = []
            
            new_activity_id = self.api_client.minter(activity_type) + "." + self.workflow_iteration
            logging.info(f"New activity id created for {omics_processing_id} activity type {activity_type}: {new_activity_id}")
            
            new_assembly_base_dir = os.path.join(self.data_dir, omics_processing_id,
                                                 new_activity_id)
            os.makedirs(new_assembly_base_dir, exist_ok=True)
            
            for old_do_id in assembly_rec["has_output"]:
                logger.info(f"old_do_id: {old_do_id}")
                old_do_rec = get_data_object_record_by_id(db_record, old_do_id)
                data_object_type = find_data_object_type(old_do_rec)
                if not data_object_type:
                    continue
                new_file_path = get_new_paths(old_do_rec["url"],new_assembly_base_dir, new_activity_id)
                updated_md5, updated_file_size = assembly_file_operations(
                old_do_rec, data_object_type, new_file_path, new_activity_id,
                    self.data_dir)
                logging.info(f"New file path computed for {data_object_type}: {new_file_path}")
                #update md5 and file byte size in place to use _make_new_data_object function without functions
                old_do_rec["file_size_bytes"] = updated_file_size
                old_do_rec["md5_checksum"] = updated_md5
                new_do = self.make_new_data_object(
                    omics_processing_id, activity_type, new_activity_id, old_do_rec, data_object_type
                )
                # add new data object to new database and update has_output
                new_db.data_object_set.append(new_do)
                updated_has_output.append(new_do.id)

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
            new_db: NmdcDatabase) -> (NmdcDatabase):
        """
        Return a new Database instance with the read_based_taxonomy_analysis_activity_set
        and its data objects updated to new IDs.
        """
        logger.info(f"Updating read_based_taxonomy_analysis_activity_set for "
                    f"{db_record[OMICS_PROCESSING_SET][0]['id']}")
        new_omics_processing = new_db.omics_processing_set[0]

        for read_based_rec in db_record[
            "read_based_taxonomy_analysis_activity_set"]:
            activity_type = "nmdc:ReadBasedTaxonomyAnalysisActivity"
            omics_processing_id = new_omics_processing.id
            has_input = [self._get_input_do_id(new_db, "Filtered Sequencing Reads")]
            
            new_activity_id = self.api_client.minter(activity_type) + "." + self.workflow_iteration
            logging.info(f"New activity id created for {omics_processing_id} activity type {activity_type}: {new_activity_id}")
            
            new_readbased_base_dir = os.path.join(self.data_dir, omics_processing_id,
                                                  new_activity_id)
            os.makedirs(new_readbased_base_dir, exist_ok=True)
            
            updated_has_output = []
            for old_do_id in read_based_rec["has_output"]:
                logger.info(f"old_do_id: {old_do_id}")
                old_do_rec = get_data_object_record_by_id(db_record, old_do_id)
                data_object_type = find_data_object_type(old_do_rec)
                if not data_object_type:
                    continue
                new_file_path = compute_new_paths(
                old_do_rec["url"], new_readbased_base_dir, new_activity_id, self.data_dir
                )
                logging.info(f"New file path computed for {data_object_type}: {new_file_path}")
                
                new_do = self.make_new_data_object(
                    omics_processing_id, activity_type, new_activity_id, old_do_rec, data_object_type
                )
                # add new data object to new database and update has_output
                new_db.data_object_set.append(new_do)
                updated_has_output.append(new_do.id)

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
                                              new_db: NmdcDatabase) -> (NmdcDatabase):
        """
        Return a new Database instance with the metatranscriptome_activity_set
        and its data objects updated to new IDs.
        """
        logger.info(f"Updating metatranscriptome_activity_set for "
                    f"{db_record[OMICS_PROCESSING_SET][0]['id']}")
        new_omics_processing = new_db.omics_processing_set[0]

        for metatranscriptome_rec in db_record[METATRANSCRIPTOME_ACTIVITY_SET]:
            activity_type = "nmdc:MetaT"
            omics_processing_id = new_omics_processing.id
            has_input = [self._get_input_do_id(new_db, "Filtered Sequencing Reads")]

            updated_has_output = []

            new_activity_id = self.api_client.minter(activity_type) + "." + self.workflow_iteration
            logging.info(f"New activity id created for {omics_processing_id} activity type {activity_type}: {new_activity_id}")

            new_metatranscriptome_base_dir = os.path.join(self.data_dir, omics_processing_id,
                                                          new_activity_id)
            os.makedirs(new_metatranscriptome_base_dir, exist_ok=True)

            for old_do_id in metatranscriptome_rec["has_output"]:
                logger.info(f"old_do_id: {old_do_id}")
                old_do_rec = get_data_object_record_by_id(db_record, old_do_id)
                if not old_do_rec:
                    logger.warning(f"Data object record not found for {old_do_id}")
                    continue
                data_object_type = find_data_object_type(old_do_rec)
                if not data_object_type:
                    logger.warning(f"Data object type not found for {old_do_id}")
                    continue
                new_file_path = get_new_paths(old_do_rec["url"],new_metatranscriptome_base_dir, new_activity_id)
                updated_md5, updated_file_size = assembly_file_operations(
                old_do_rec, data_object_type, new_file_path, new_activity_id,
                    self.data_dir)
                logging.info(f"New file path computed for {data_object_type}: {new_file_path}")
                new_do = self.make_new_data_object(
                    omics_processing_id, activity_type, new_activity_id, old_do_rec, data_object_type
                )
                # add new data object to new database and update has_output
                new_db.data_object_set.append(new_do)
                updated_has_output.append(new_do.id)

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
        new_data_object_id = self.api_client.minter("nmdc:DataObject")
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
            md5_checksum=data_object_record["md5_checksum"],
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

