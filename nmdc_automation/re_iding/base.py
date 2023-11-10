# nmdc_automation/nmddc_automation/re_iding/base.py
"""
base.py - Provides classes and functions for re-ID-ing NMDC metagenome workflow
records and data objects.
"""
import logging
from typing import Dict
import yaml

from nmdc_schema.nmdc import DataObject as NmdcDataObject, \
    Database as NmdcDatabase, OmicsProcessing

from nmdc_automation.api import NmdcRuntimeApi
from nmdc_automation.re_iding.db_utils import (OMICS_PROCESSING_SET,
                                               READS_QC_SET,
                                               check_for_single_omics_processing_record,
                                               get_data_object_record_by_id, )

NAPA_TEMPLATE = "../../../configs/re_iding_worklfows.yaml"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

class ReIdTool:
    def __init__(self, api_client: NmdcRuntimeApi, template_file: str = None):
        self.api_client = api_client
        if template_file is None:
            template_file = NAPA_TEMPLATE
        with open(template_file, "r") as f:
            self.template = yaml.safe_load(f)

    def update_omics_processing_has_output(
            self, db_record: Dict,
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
        has_output = omics_record.pop("has_output", [])
        omics_record.pop("_id", None)
        # make a new omics processing record
        new_omics = OmicsProcessing(**omics_record)

        # make new data objects with updated IDs
        for old_do_id in has_output:
            old_do_rec = get_data_object_record_by_id(db_record, old_do_id)
            old_do_id = old_do_rec.pop("id")
            new_do_id = self.api_client.minter("nmdc:DataObject")
            logger.info(f"nmdcDataObject\t{old_do_id}\t{new_do_id}")

            # Add new do ID to new OmicsProcessing has_output
            new_omics.has_output.append(new_do_id)
            # Make a new data object record with the new ID
            new_db.data_object_set.append(
                NmdcDataObject(**old_do_rec, id=new_do_id)
            )
        new_db.omics_processing_set.append(new_omics)
        return new_db






def update_reads_qc_analysis_activity_set(db_record: Dict, new_db: NmdcDatabase,
                                          api_client: NmdcRuntimeApi) -> (NmdcDatabase):
    """
    Return a new Database instance with the reads_qc_analysis_activity_set
    and its data objects updated to new IDs.
    """
    for reads_qc_rec in db_record[READS_QC_SET]:
        pass

