""" Import Mapper - Map import data to NMDC data objects. """

import json
import logging
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Union, Set, Tuple

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


    def __init__(
            self, nucleotide_sequencing_id: str,
            import_project_dir: str, import_yaml: str, runtime_api
    ):
        self.nucleotide_sequencing_id = nucleotide_sequencing_id
        self.import_project_dir = import_project_dir
        self.import_yaml = import_yaml
        self.runtime_api = runtime_api
        # Derived properties

        self._import_files = [f for f in os.listdir(self.import_project_dir) if
            os.path.isfile(os.path.join(self.import_project_dir, f))]
        self._file_mappings = self._init_file_mappings()
        self.minted_id_file = f"{self.import_project_dir}/{self.nucleotide_sequencing_id}_minted_ids.json"
        self.minted_ids = {
                "data_object_ids": {},
                "workflow_execution_ids": {}
            }
        if os.path.exists(self.minted_id_file):
            logger.info(f"Loading minted IDs from {self.minted_id_file}")
            with open(self.minted_id_file, 'r') as f:
                ids = json.load(f)
                self.minted_ids = ids

    def write_minted_id_file(self):
        with open(self.minted_id_file, 'w') as f:
            logger.info(f"Writing minted IDs to {self.minted_id_file}")
            json.dump(self.minted_ids, f)

    def get_or_create_minted_id(self, object_type: str, data_object_type: str = None) -> str:
        """
        Get an ID by object type and data object type if it exists, otherwise mint a new ID and add it to self.minted_ids.
        """
        if object_type == self.NMDC_DATA_OBJECT_TYPE and not data_object_type:
            raise TypeError("Must specify data_object_type for a Data Object")

        if object_type == self.NMDC_DATA_OBJECT_TYPE:
            ids = self.minted_ids["data_object_ids"]
            if data_object_type in ids:
                return ids[data_object_type]
            else:
                data_obj_id = self.runtime_api.minter(object_type)
                logger.info(f"Minted new ID:  {data_obj_id}")
                self.minted_ids["data_object_ids"][data_object_type] = data_obj_id
                return data_obj_id
        else:
            ids = self.minted_ids["workflow_execution_ids"]
            if object_type in ids:
                return ids[object_type]
            else:
                workflow_obj_id = self.runtime_api.minter(object_type) + ".1"
                logger.info(f"Minted new ID:  {workflow_obj_id}")
                self.minted_ids["workflow_execution_ids"][object_type] = workflow_obj_id
                return workflow_obj_id


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
        return list(self._file_mappings)

    @property
    def file_mappings_by_data_object_type(self) -> Dict:
        """Return the file mappings by data object type."""
        return {fm.data_object_type: fm for fm in self.file_mappings}


    @property
    def file_mappings_by_workflow_type(self) -> Dict[str, list]:
        """Return the file mappings by workflow type."""
        file_mappings = {}
        for fm in self.file_mappings:
            if fm.output_of in file_mappings:
                file_mappings[fm.output_of].append(fm)
            else:
                file_mappings[fm.output_of] = [fm]
        return file_mappings


    @property
    def workflow_execution_ids(self) -> List[str]:
        """ Return the unique workflow execution IDs."""
        workflow_execution_ids = {fm.workflow_execution_id for fm in self.file_mappings}
        return list(workflow_execution_ids)

    @property
    def workflow_execution_types(self) -> List[str]:
        """ Return the unique workflow execution types, bases on output_of."""
        workflow_execution_types = {fm.output_of for fm in self.file_mappings}
        return list(workflow_execution_types)


    def update_file_mappings(self, data_object_type: str,
                             data_object_id: str,
                             workflow_execution_id: str,
                             ) -> None:
        """ Update the file mappings."""
        for fm in self._file_mappings:
            if fm.data_object_type == data_object_type:
                fm.data_object_id = data_object_id
                fm.workflow_execution_id = workflow_execution_id

    def get_nmdc_data_file_name(self, file_mapping: "FileMapping") -> str:
        spec = self.import_specs_by_data_object_type[file_mapping.data_object_type]
        if spec["action"] == "none":
            filename =  os.path.basename(file_mapping.file)
        elif spec["action"] == "rename":
            wfe_file_id = file_mapping.workflow_execution_id.replace(":", "_")
            filename =  wfe_file_id + spec["nmdc_suffix"]
        else:
            raise NotImplementedError
        return filename


    def get_has_input_has_output_for_workflow_type(self, workflow_type: str) -> Tuple[list, list]:
        """
        Retrieve input and output data object IDs for a given workflow type.

        Args:
            workflow_type: The workflow type for which the input and output data
            objects are to be determined.

        Returns:
            A tuple containing two lists:
                - The first list contains IDs of data objects that serve as inputs
                  to the specified workflow type.
                - The second list contains IDs of data objects that serve as outputs
                  of the specified workflow type.
        """
        has_input = []
        has_output = []
        for fm in self.file_mappings:
            if fm.output_of == workflow_type:
                has_output.append(fm.data_object_id)
            else:
                for wf_type in fm.input_to:
                    if wf_type == workflow_type:
                        has_input.append(fm.data_object_id)
        return has_input, has_output



    def _init_file_mappings(self) -> Set:
        """Create the initial list of File Mapping based on the import files."""
        file_mappings = set()
        for file in self._import_files:
            data_object_type = self._get_file_data_object_type(file)
            if not data_object_type:
                logger.error(f"No mapping action found for {file}")
                continue
            import_spec = self.import_specs_by_data_object_type[data_object_type]
            output_of = import_spec["output_of"]
            input_to = import_spec["input_to"]
            is_multiple = import_spec["multiple"]
            file_mappings.add(
                FileMapping(data_object_type, file, output_of, input_to, is_multiple)
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
    - data_object_id: The data object ID.
    - workflow_execution_id: (Optional) The workflow execution ID that the data object is output of.
    """

    def __init__(self, data_object_type: str, import_file: Union[str, Path], output_of: str,
                 input_to: list , is_multiple: bool,  data_object_id: Optional[str] = None, workflow_execution_id: str = None):
        self.data_object_type = data_object_type
        self.file = import_file
        self.output_of = output_of
        self.input_to = input_to
        self.is_multiple = is_multiple
        self.data_object_id = data_object_id
        self.workflow_execution_id = workflow_execution_id

    def __str__(self):
        return (
            f"FileMapping("
            f"data_object_type={self.data_object_type}, "
            f"file={self.file}, "
            f"output_of={self.output_of}, "
            f"input_to={self.input_to}, "
            f"is_multiple={self.is_multiple}, "
            f"data_object_id={self.data_object_id}, "
            f"workflow_execution_id={self.workflow_execution_id} "
            f")"
        )

    def __eq__(self, other):
        if isinstance(other, FileMapping):
            return (
                self.data_object_type == other.data_object_type and
                self.file == other.file and
                self.output_of == other.output_of and
                self.input_to == other.input_to and
                self.is_multiple == other.is_multiple and
                self.data_object_id == other.data_object_id and
                self.workflow_execution_id == other.workflow_execution_id
            )

    def __hash__(self):
        return hash((self.data_object_type, self.file, self.output_of, self.data_object_id, self.workflow_execution_id))
        

@lru_cache
def _load_yaml_file(yaml_file: Union[str, Path]) -> Dict:
    """Utility function to load YAML file."""
    with open(yaml_file, "r") as file:
        return yaml.safe_load(file)
