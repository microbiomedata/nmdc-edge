""" Import Mapper - Map import data to NMDC data objects. """

import json
import logging
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Union, Set, Tuple

from nmdc_schema.nmdc import DataCategoryEnum 

import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImportMapper:
    """
    Class to manage the mapping of import data to NMDC data objects.:
    Required:
    - nucleotide_sequencing_id: The NMDC ID for the Data Generation record that will serve as the root node in the DB.
    - import_project_dir: The import project directory path.
    - import_yaml: The file path of the yaml file containing import specifications.

    Attributes:
    - data_object_mappings: A set of DataObjectMapping objects.
    - minted_id_file: The file path of the minted IDs.
    - minted_ids: A dictionary of minted IDs.

    Properties:
    - import_specifications: Return the import specifications.
    - root_directory: Return the root directory path based on nucleotide sequencing ID.
    - data_source_url: Return the data source URL specified in the import.yaml file.
    - import_specs_by_workflow_type: Return the import specifications by workflow type.
    - import_specs_by_data_object_type: Return the import specifications by data object type (unique and multiple).
    - mappings: Return the file mappings as a list.
    - mappings_by_data_object_type: Return the file mappings by data object type.
    - mappings_by_workflow_type: Return the file mappings by workflow type.
    """
    METAGENOME_RAW_READS = "Metagenome Raw Reads"
    NMDC_DATA_OBJECT = "nmdc:DataObject"


    def __init__(
            self, nucleotide_sequencing_id: str,
            import_project_dir: str, import_yaml: str, runtime_api
    ):
        self.data_generation_id = nucleotide_sequencing_id # sequencing is a type of data_generation
        self.import_project_dir = import_project_dir
        self.import_yaml = import_yaml
        self.runtime_api = runtime_api

        self.data_object_mappings = set()

        self._import_files = [f for f in os.listdir(self.import_project_dir) if
            os.path.isfile(os.path.join(self.import_project_dir, f))]

        self.minted_id_file = f"{self.import_project_dir}/{self.data_generation_id}_minted_ids.json"
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
        """Write the minted IDs to a file."""
        with open(self.minted_id_file, 'w') as f:
            logger.info(f"Writing minted IDs to {self.minted_id_file}")
            json.dump(self.minted_ids, f)

    def get_or_create_minted_id(self, object_type: str, data_object_type: str = None) -> str:
        """
        Get an ID by object type and data object type.
        If the ID exists in the minted_ids, return it.
        Otherwise, mint a new ID, add it to minted_ids, and return it.
        """
        if object_type == self.NMDC_DATA_OBJECT and not data_object_type:
            raise TypeError("Must specify data_object_type for a Data Object")

        if object_type == self.NMDC_DATA_OBJECT:
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
            self.import_specifications["Workflow Metadata"]["Root Directory"], self.data_generation_id
        )

    @property
    def data_source_url(self) -> str:
        """Return the data source URL specified in the import.yaml file."""
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
    def mappings(self) -> List:
        """Return the file mappings."""
        return list(self.data_object_mappings)

    @property
    def mappings_by_data_object_type(self) -> Dict:
        """Return the file mappings by data object type."""
        return {fm.data_object_type: fm for fm in self.mappings}


    @property
    def mappings_by_workflow_type(self) -> Dict[str, list]:
        """Return the file mappings by workflow type."""
        file_mappings = {}
        for fm in self.mappings:
            if fm.output_of in file_mappings:
                file_mappings[fm.output_of].append(fm)
            else:
                file_mappings[fm.output_of] = [fm]
        return file_mappings


    @property
    def workflow_execution_ids(self) -> List[str]:
        """ Return the unique workflow execution IDs."""
        workflow_execution_ids = {fm.nmdc_process_id for fm in self.mappings}
        return list(workflow_execution_ids)

    @property
    def workflow_execution_types(self) -> List[str]:
        """ Return the unique workflow execution types, bases on output_of."""
        workflow_execution_types = {fm.output_of for fm in self.mappings}
        return list(workflow_execution_types)


    def update_mappings(self, data_object_type: str,
                        data_object_id: str,
                        workflow_execution_id: str,
                        ) -> None:
        """ Update the data object mappings."""
        for fm in self.data_object_mappings:
            if fm.data_object_type == data_object_type:
                fm.data_object_id = data_object_id
                fm.nmdc_process_id = workflow_execution_id

    def get_nmdc_data_file_name(self, file_mapping: "DataObjectMapping") -> str:
        """
        Return the NMDC data file name based on the file mapping and import specification.
        """
        spec = self.import_specs_by_data_object_type[file_mapping.data_object_type]
        if spec["action"] == "none":
            filename =  os.path.basename(file_mapping.import_file)
        elif spec["action"] == "rename":
            wfe_file_id = file_mapping.nmdc_process_id.replace(":", "_")
            filename =  wfe_file_id + spec["nmdc_suffix"]
        elif spec["action"] == "zip":
            wfe_file_id = file_mapping.nmdc_process_id.replace(":", "_")
            filename = wfe_file_id + spec["nmdc_suffix"]
        else:
            raise ValueError(f"Unknown action: {spec['action']}")
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
        has_input = set()
        has_output = set()
        for fm in self.mappings:
            if fm.output_of == workflow_type:
                has_output.add(fm.data_object_id)
            else:
                for wf_type in fm.input_to:
                    if wf_type == workflow_type:
                        has_input.add(fm.data_object_id)
        return list(has_input), list(has_output)


    def add_do_mappings_from_data_generation(self) -> None:
        """
        Create the initial list of Data Object Mapping based on the data generation
        record in the DB.

        If the DG has_output is empty we create a mapping for Metagenome Raw Reads with
        the data generation ID as the process_id, but no data object.
        """
        # Find the data generation and it's output data object
        id_filter = {'id': self.data_generation_id}
        data_generation_recs = self.runtime_api.find_planned_processes(id_filter)
        if len(data_generation_recs) != 1:
            raise ValueError(f"Found {len(data_generation_recs)} data generation records but expected 1")
        data_generation = data_generation_recs[0]

        if 'has_output' in data_generation and len(data_generation['has_output']) > 0:
            data_object_id = data_generation['has_output'][0]
            data_object = self.runtime_api.find_data_objects(data_object_id)
        else:
            data_object = None

        if data_object:
            import_spec = self.import_specs_by_data_object_type[data_object["data_object_type"]]
            self.data_object_mappings.add(
                DataObjectMapping(
                    data_object_type=data_object["data_object_type"],
                    output_of=import_spec['output_of'],
                    input_to=import_spec['input_to'],
                    is_multiple=import_spec['multiple'],
                    data_object_id=data_object['id'],
                    nmdc_process_id=data_generation['id'],
                    data_object_in_db=True,
                    process_id_in_db=True,
                    data_category=DataCategoryEnum.processed_data 
                )
            )
        else:
            data_object_type = "Metagenome Raw Reads"
            import_spec = self.import_specs_by_data_object_type[data_object_type]
            self.data_object_mappings.add(
                DataObjectMapping(
                    data_object_type=data_object_type,
                    output_of=import_spec['output_of'],
                    input_to=import_spec['input_to'],
                    is_multiple=import_spec['multiple'],
                    nmdc_process_id=self.data_generation_id,
                    data_object_in_db=False,
                    process_id_in_db=True,
                    data_category=DataCategoryEnum.instrument_data
                )
            )


    def add_do_mappings_from_workflow_executions(self) -> None:
        """
        Create the initial list of Data Object Mapping based on workflow executions
        in the DB.
        """

        filter = {
            'was_informed_by': self.data_generation_id,
            'type': {"$ne": "nmdc:MetagenomeSequencing"}
        }
        workflow_execution_recs = self.runtime_api.find_planned_processes(filter)
        for workflow_execution in workflow_execution_recs:
            data_object_ids = workflow_execution['has_output']
            for data_object_id in data_object_ids:
                data_object = self.runtime_api.find_data_objects(data_object_id)
                import_spec = self.import_specs_by_data_object_type.get(data_object["data_object_type"])
                if not import_spec:
                    logger.warning(f"Cannot find an import specification for data object {data_object_id} / {data_object['data_object_type']}")
                    continue
                self.data_object_mappings.add(
                    DataObjectMapping(
                        data_object_type=data_object["data_object_type"],
                        output_of=import_spec['output_of'],
                        input_to=import_spec['input_to'],
                        is_multiple=import_spec['multiple'],
                        data_object_id=data_object_id,
                        nmdc_process_id=workflow_execution['id'],
                        data_object_in_db=True,
                        process_id_in_db=True,
                        data_category=DataCategoryEnum.processed_data
                    )
                )


    def update_do_mappings_from_import_files(self) -> None:
        """
        Update the Data Object Mappings based on the import files.
        """
        for file in self._import_files:
            data_object_type = self._get_file_data_object_type(file)
            if not data_object_type:
                logger.error(f"No mapping action found for {file}")
                continue
            import_spec = self.import_specs_by_data_object_type[data_object_type]

            # look for an existing single-data mapping and add the import file
            existing_mapping = next((m for m in self.data_object_mappings if m.data_object_type == data_object_type), None)
            if existing_mapping and not import_spec['multiple']:
                existing_mapping.import_file = file
            else:
                self.data_object_mappings.add(
                    DataObjectMapping(
                        data_object_type=data_object_type,
                        output_of=import_spec['output_of'],
                        input_to=import_spec['input_to'],
                        is_multiple=import_spec['multiple'],
                        import_file=file,
                    )
                )


    def _get_file_data_object_type(self, file: str) -> Optional[str]:
        """Return the data object type based on the file name suffix."""
        for _, import_spec in self.import_specs_by_data_object_type.items():
            import_suffix = re.compile(import_spec["import_suffix"])
            if import_suffix.search(file):
                return import_spec["data_object_type"]
        return None


class DataObjectMapping:
    """
    Class to represent a Data Object mapping with:
    Required:
    - data_object_type: The type of data object.
    - output_of: The workflow execution type that this data object is an output of.
    - input_to: The workflow execution type(s) that this data object is an input to.
    - is_multiple: Whether this data object is based on a multipart data file such as binning results.
    Optional - these get updated as the data object is processed:
    - data_object_id: The data object ID.
    - nmdc_process_id: The workflow execution or data generation ID that produced this data object.
    - data_object_in_db: Whether this data object exists in the database or not.
    - nmdc_process_in_db: Whether this process (workflow execution or data generation) exists in the database or not.
    - data_category: The category of data (instrument_data, processed_data, or workflow_parameter_data) as defined in DataCategoryEnum.
    """

    def __init__(self, data_object_type: str, output_of: str, input_to: list, is_multiple: bool,
                 data_object_id: Optional[str] = None, import_file: Union[str, Path] = None,
                 nmdc_process_id: str = None, data_object_in_db: bool = False, process_id_in_db: bool = False, 
                 data_category: Optional[DataCategoryEnum] = None) -> None:
        self.data_object_type = data_object_type
        self.import_file = import_file
        self.output_of = output_of
        self.input_to = input_to
        self.is_multiple = is_multiple
        self.data_object_id = data_object_id
        self.nmdc_process_id = nmdc_process_id
        self.data_object_in_db = data_object_in_db
        self.process_id_in_db = process_id_in_db
        self.data_category = data_category

    def __str__(self):
        return (
            f"FileMapping("
            f"data_object_type={self.data_object_type}, "
            f"import_file={self.import_file}, "
            f"output_of={self.output_of}, "
            f"input_to={self.input_to}, "
            f"is_multiple={self.is_multiple}, "
            f"data_object_id={self.data_object_id}, "
            f"nmdc_process_id={self.nmdc_process_id}, "
            f"data_object_in_db={self.data_object_in_db}, "
            f"process_id_in_db={self.process_id_in_db}, "
            f"data_category={self.data_category} "
            f")"
        )

    def __eq__(self, other):
        if isinstance(other, DataObjectMapping):
            return (
                    self.data_object_type == other.data_object_type and
                    self.import_file == other.import_file and
                    self.output_of == other.output_of and
                    self.input_to == other.input_to and
                    self.is_multiple == other.is_multiple and
                    self.data_object_id == other.data_object_id and
                    self.nmdc_process_id == other.nmdc_process_id and
                    self.data_object_in_db == other.data_object_in_db and
                    self.process_id_in_db == other.process_id_in_db and
                    self.data_category == other.data_category
            )

    def __hash__(self):
        return hash((self.data_object_type, self.import_file, self.output_of, self.data_object_id, self.nmdc_process_id, self.data_category))
        

@lru_cache
def _load_yaml_file(yaml_file: Union[str, Path]) -> Dict:
    """Utility function to load YAML file."""
    with open(yaml_file, "r") as file:
        return yaml.safe_load(file)
