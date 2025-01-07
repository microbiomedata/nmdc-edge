""" Import Mapper - Map import data to NMDC data objects. """

import json
import logging
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Union

import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImportMapper:
    """
    Class to represent a data import mapping with:
    - nucleotide_sequencing_id: The identifier for the omics data.
    - import_project_dir: The project directory path.
    - import_yaml: The file path of the yaml file containing import specifications.
    """
    METAGENOME_RAW_READS = "Metagenome Raw Reads"
    NMDC_DATA_OBJECT_TYPE = "nmdc:DataObject"


    def __init__(self, nucleotide_sequencing_id: str, import_project_dir: str, import_yaml: str):
        self.nucleotide_sequencing_id = nucleotide_sequencing_id
        self.import_project_dir = import_project_dir
        self.import_yaml = import_yaml
        self._file_mappings = []
        self._import_files = [f for f in os.listdir(self.import_project_dir) if
            os.path.isfile(os.path.join(self.import_project_dir, f))]

        self.minted_id_file = f"{self.nucleotide_sequencing_id}_minted_ids.json"
        self.minted_ids = {}
        if os.path.exists(self.minted_id_file):
            with open(self.minted_id_file, 'r') as f:
                ids = json.load(f)
                self.minted_ids = ids

    def write_minted_id_file(self):
        with open(self.minted_id_file, 'w') as f:
            json.dump(self.minted_ids, f)




    @property
    def import_specifications(self) -> Dict:
        """Return the import specifications."""
        return _load_yaml_file(self.import_yaml)

    @property
    def root_directory(self) -> str:
        """Return the root directory path based on nucleotide sequencing ID."""
        return os.path.join(
            self.import_specifications["Workflow Metadata"]["Root Directory"], self.nucleotide_sequencing_id
        )

    @property
    def data_source_url(self) -> str:
        """Return the data source URL."""
        return self.import_specifications["Workflow Metadata"]["Source URL"]

    @property
    def import_specs_by_workflow_type(self) -> Dict:
        """Return the import specifications by workflow type."""
        return {wf["Type"]: wf for wf in self.import_specifications["Workflows"]}

    @property
    def import_specs_by_data_object_type(self) -> Dict:
        """Return the import specifications by data object type (unique and multiple)."""
        import_specs = {do['data_object_type']: do for do in self.import_specifications["Data Objects"]["Unique"]}
        import_specs.update(
            {do['data_object_type']: do for do in self.import_specifications["Data Objects"]["Multiples"]}
            )
        return import_specs

    @property
    def file_mappings(self) -> List:
        """Return the file mappings."""
        if not self._file_mappings:
            self._file_mappings = self._init_file_mappings()
        return self._file_mappings

    @property
    def file_mappings_by_data_object_type(self) -> Dict:
        """Return the file mappings by data object type."""
        file_mappings = {fm.data_object_type: fm for fm in self._file_mappings}
        return file_mappings

    def update_file_mappings(self, data_object_type: str,
                             data_object_id: str,
                             workflow_execution_id: str,
                             ) -> None:
        for do_type, fm in self.file_mappings_by_data_object_type.items():
            if do_type.upper() == data_object_type.upper():
                fm.data_object_id = data_object_id
                fm.workflow_execution_id = workflow_execution_id

    def _init_file_mappings(self) -> List:
        """Create the initial list of File Mapping based on the import files."""
        file_mappings = []
        for file in self._import_files:
            data_object_type = self._get_file_data_object_type(file)
            if not data_object_type:
                logger.error(f"No mapping action found for {file}")
                continue
            import_spec = self.import_specs_by_data_object_type[data_object_type]
            output_of = import_spec["output_of"]
            input_to = import_spec["input_to"]
            file_mappings.append(
                FileMapping(data_object_type, file, output_of, input_to)
            )
        return file_mappings

    def _get_file_data_object_type(self, file: str) -> Optional[str]:
        """Return the data object type based on the file name suffix."""
        for _, import_spec in self.import_specs_by_data_object_type.items():
            import_suffix = re.compile(import_spec["import_suffix"])
            if import_suffix.search(file):
                return import_spec["data_object_type"]
        return None


class FileMapping:
    """
    Class to represent a data file mapping with:
    - data_object_type: The type of data object.
    - import_file: The import file name.
    - output_of: The workflow execution type that this data object is an output of.
    - input_to: The workflow execution type(s) that this data object is an input to.
    - workflow_execution_id: (Optional) The workflow execution ID that the data object is output of.
    """

    def __init__(self, data_object_type: str, import_file: Union[str, Path], output_of: str, input_to: List[str],
                 data_object_id: Optional[str] = None, workflow_execution_id: str = None):
        self.data_object_type = data_object_type
        self.file = import_file
        self.output_of = output_of
        self.input_to = input_to
        self.data_object_id = data_object_id
        self.workflow_execution_id = workflow_execution_id

        
        
    def __str__(self):
        return (
            f"FileMapping("
            f"data_object_type={self.data_object_type}, "
            f"file={self.file}, "
            f"output_of={self.output_of}, "
            f"input_to={self.input_to}, "
            f"data_object_id={self.data_object_id}, "
            f"workflow_execution_id={self.workflow_execution_id} "
            f")"
        )
        




@lru_cache
def _load_yaml_file(yaml_file: Union[str, Path]) -> Dict:
    """Utility function to load YAML file."""
    with open(yaml_file, "r") as file:
        return yaml.safe_load(file)
