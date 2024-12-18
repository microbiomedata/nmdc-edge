import os
from pathlib import Path
import re
import logging
import datetime
import pytz
import yaml

from typing import List, Dict, Union, Tuple
from nmdc_schema import nmdc

from nmdc_automation.api import NmdcRuntimeApi
from nmdc_automation.models.nmdc import DataObject, workflow_process_factory
from .utils import object_action, file_link, get_md5, filter_import_by_type

logger = logging.getLogger(__name__)


class GoldMapper:

    METAGENOME_RAW_READS = "Metagenome Raw Reads"
    def __init__(
        self,
        iteration,
        file_list: List[Union[str, Path]],
        nucelotide_sequencing_id: str,
        yaml_file: Union[str, Path],
        project_directory: Union[str, Path],
        runtime: NmdcRuntimeApi,
    ):
        """
        Initialize the GoldMapper object.

        Args:
            file_list: List of file paths to be processed.
            nucelotide_sequencing_id: Identifier for the omics data.
            yaml_file: File path of the yaml file containing import data.
            root_directory: Root directory path.
            project_directory: Project directory path.
        """

        self.import_specifications = self.load_yaml_file(yaml_file)
        self.nmdc_db = nmdc.Database()
        self.iteration = iteration
        self.file_list = file_list
        self.nucelotide_sequencing_id = nucelotide_sequencing_id
        self.root_dir = os.path.join(
            self.import_specifications["Workflow Metadata"]["Root Directory"], nucelotide_sequencing_id
        )
        self.project_dir = project_directory
        self.url = self.import_specifications["Workflow Metadata"]["Source URL"]
        self.data_object_type = "nmdc:DataObject"
        self.data_object_map = {}
        self.workflow_execution_ids = {}
        self.workflows_by_type = self.build_workflows_by_type()
        self.runtime = runtime


    def load_yaml_file(self, yaml_file: Union[str, Path]) -> Dict:
        """Utility function to load YAML file."""
        with open(yaml_file, "r") as file:
            return yaml.safe_load(file)

    def build_workflows_by_type(self) -> Dict:
        """Builds a dictionary of workflows by their type."""
        return {wf["Type"]: wf for wf in self.import_specifications["Workflows"]}


    def link_sequencing_data_file(self) -> Dict[str, dict]:
        """
        Create a link to the sequencing file if it does not exist.
        Return a dictionary with the sequencing data object record by md5 checksum.

        Currently only supports a unique sequencing data object of type "Metagenome Raw Reads".
        """
        sequencing_import_specifications = [
            d for d in self.import_specifications["Data Objects"]["Unique"] if d["data_object_type"] == self.METAGENOME_RAW_READS
        ]
        # We can only have one sequencing data object import specification
        if len(sequencing_import_specifications) > 1:
            raise ValueError("More than one sequencing import specification found")
        import_spec = sequencing_import_specifications[0]


        # make the root directory if it does not exist
        try:
            os.makedirs(self.root_dir)
        except FileExistsError:
            logger.info(f"{self.root_dir} already exists")

        # Get the import file that matches the nmdc_suffix given in the data object spec - we can only have one
        import_files = [str(f) for f in self.file_list if re.search(import_spec["import_suffix"], str(f))]
        if len(import_files) > 1:
            raise ValueError("More than one sequencing data object found")
        if not import_files:
            raise ValueError("No sequencing data object found")
        import_file = import_files[0]

        file_destination_name = object_action(
            import_file,
            import_spec["action"],
            self.nucelotide_sequencing_id,
            import_spec["nmdc_suffix"],
        )
        export_file = os.path.join(self.root_dir, file_destination_name)
        try:
            os.link(import_file, export_file)
            logger.info(f"Linked {import_file} to {export_file}")
        except FileExistsError:
            logger.info(f"{export_file} already exists")
        md5 = get_md5(export_file)
        sequencing_data_by_md5 = {
            md5: {
                "name": file_destination_name,
                "file_size_bytes": os.stat(export_file).st_size,
                "md5_checksum": md5,
                "data_object_type": import_spec["data_object_type"],
                "description": import_spec["description"].replace(
                    "{id}", self.nucelotide_sequencing_id
                )
            }
        }
        return sequencing_data_by_md5



    def map_sequencing_data(self) -> Tuple[nmdc.Database, Dict]:
        """
        Map sequencing data to an NMDC data object and create an update to be applied to the has_output
        list of the sequencing data generation.
        """
        # Define the sequencing types to look for -
        sequencing_types = ["Metagenome Raw Reads",]
        db = nmdc.Database()

        # get the Metagenome Raw Reads import data
        sequencing_import_data = [
            d for d in self.import_specifications["Data Objects"]["Unique"] if d["data_object_type"] in sequencing_types
        ]
        has_output = []
        for data_object_dict in sequencing_import_data:
            # get the file(s) that match the import suffix
            for import_file in self.file_list:
                import_file = str(import_file)
                if re.search(data_object_dict["import_suffix"], import_file):
                    logging.debug(f"Processing {data_object_dict['data_object_type']}")
                    file_destination_name = object_action(
                        import_file,
                        data_object_dict["action"],
                        self.nucelotide_sequencing_id,
                        data_object_dict["nmdc_suffix"],
                    )
                    # sequencing_dir = os.path.join(self.root_dir, self.nucelotide_sequencing_id)
                    try:
                        os.makedirs(self.root_dir)
                    except FileExistsError:
                        logger.debug(f"{self.root_dir} already exists")

                    export_file = os.path.join(self.root_dir, file_destination_name)

                    try:
                        os.link(import_file, export_file)
                    except FileExistsError:
                        logger.debug(f"{export_file} already exists")

                    filemeta = os.stat(export_file)
                    md5 = get_md5(export_file)
                    data_object_id = self.runtime.minter(self.data_object_type)
                    # Imported nucleotide sequencing data object does not have a URL
                    do_record = {
                        "id": data_object_id,
                        "type": self.data_object_type,
                        "name": file_destination_name,
                        "file_size_bytes": filemeta.st_size,
                        "md5_checksum": md5,
                        "data_object_type": data_object_dict["data_object_type"],
                        "description": data_object_dict["description"].replace(
                            "{id}", self.nucelotide_sequencing_id
                        )
                    }
                    db.data_object_set.append(DataObject(**do_record))
                    has_output.append(data_object_id)
        update = {
            "update": "data_generation_set",
            "updates": [
                {"q": {"id": self.nucelotide_sequencing_id}, "u": {"$addToSet": {"has_output": has_output[0]}}}
            ]
        }
        # update self.data_object_map
        if len(has_output) > 1:
            raise ValueError("More than one sequencing data object found")
        self.data_object_map["Metagenome Raw Reads"] = (
            ["nmdc:ReadQcAnalysis"], ["nmdc:NucleotideSequencing"], has_output[0]
        )
        return db, update


    def map_data(self,db: nmdc.Database, unique: bool = True) -> Tuple[nmdc.Database, Dict]:
        """
        Map data objects to the NMDC database.
        """

        def process_files(files: Union[str, List[str]], data_object_dict: Dict, workflow_execution_id: str,
                          multiple: bool = False) -> DataObject:
            """
            Process import file(s) and return a DataObject instance. Map data object ids to input_to and
            output_of workflow execution types.
            """
            file_destination_name = object_action(
                files,
                data_object_dict["action"],
                workflow_execution_id,
                data_object_dict["nmdc_suffix"],
                workflow_execution_dir=os.path.join(self.root_dir, workflow_execution_id),
                multiple=multiple,
            )
            updated_file = file_link(
                self.project_dir,
                files,
                os.path.join(self.root_dir, workflow_execution_id),
                file_destination_name,
            )
            filemeta = os.stat(updated_file)
            md5 = get_md5(updated_file)
            data_object_id = self.runtime.minter(self.data_object_type)
            do_record = {
                "id": data_object_id,
                "type": self.data_object_type,
                "name": file_destination_name,
                "url": f"{self.url}/{self.nucelotide_sequencing_id}/{workflow_execution_id}/{file_destination_name}",
                "file_size_bytes": filemeta.st_size,
                "md5_checksum": md5,
                "data_object_type": data_object_dict["data_object_type"],
                "description": data_object_dict["description"].replace(
                    "{id}", self.nucelotide_sequencing_id
                )
            }
            # update self.objects mapping
            self.data_object_map[data_object_dict["data_object_type"]] = (
                data_object_dict["input_to"],
                [data_object_dict["output_of"]],
                data_object_id,
            )
            return DataObject(**do_record)

        # Select the correct data source (unique or multiple)
        data_objects_key = "Unique" if unique else "Multiples"
        data_object_specs = self.import_specifications["Data Objects"][data_objects_key]
        for data_object_spec in data_object_specs:
            if not filter_import_by_type(self.import_specifications["Workflows"], data_object_spec["output_of"]):
                continue
            if not "import_suffix" in data_object_spec:
                logging.warning("Missing suffix")
                continue

            # Process unique data objects
            if unique:
                for file in map(str, self.file_list):
                    if re.search(data_object_spec["import_suffix"], file):
                        workflow_execution_id = self.get_workflow_execution_id(data_object_spec["output_of"])
                        db.data_object_set.append(process_files(file, data_object_spec, workflow_execution_id))

            # Process multiple data data files into a single data object
            else:
                multiple_files = []
                for file in map(str, self.file_list):
                    if re.search(data_object_spec["import_suffix"], file):
                        multiple_files.append(file)
                if multiple_files:
                    workflow_execution_id = self.get_workflow_execution_id(data_object_spec["output_of"])
                    db.data_object_set.append(process_files(multiple_files, data_object_spec, workflow_execution_id, multiple=True))

        return db, self.data_object_map


    def map_workflow_executions(self, db) -> nmdc.Database:
        """
        Maps workflow executions from the import data to the NMDC database.
        The function creates a database workflow execution set for each workflow type in the import data,
        attaching the relevant input and output objects. It also provides other metadata for each workflow execution.

        This method assumes that the import data includes a 'Workflows' section with each workflow having
        a 'Type', 'Git_repo', and 'Version'. It also assumes that the import data includes a 'Workflow Metadata'
        section with an 'Execution Resource'.
        """

        for workflow in self.import_specifications["Workflows"]:
            if not workflow.get("Import"):
                continue
            logging.info(f"Processing {workflow['Name']}")

            # Get the input / output lists for the workflow execution type
            has_inputs_list, has_output_list = self.attach_objects_to_workflow_execution(
                workflow["Type"]
            )
            # We can't make a valid workflow execution without inputs and outputs
            if not has_inputs_list or not has_output_list:
                logging.error(
                    f"Skipping {workflow['Name']} due to missing inputs or outputs"
                )
                continue
            # Mint an ID if needed
            wf_id = self.workflow_execution_ids.get(workflow["Type"], None)
            if wf_id is None:
                # mint an ID
                wf_id = self.runtime.minter(workflow["Type"]) + "." + self.iteration
                # store the ID
                self.workflow_execution_ids[workflow["Type"]] = wf_id


            # Create the workflow execution object
            record = {
                "id": wf_id,
                "name": workflow["Workflow_Execution"]["name"].replace("{id}", wf_id),
                "type": workflow["Type"],
                "has_input": has_inputs_list,
                "has_output": has_output_list,
                "git_url": workflow["Git_repo"],
                "version": workflow["Version"],
                "execution_resource": self.import_specifications["Workflow Metadata"]["Execution Resource"],
                "started_at_time": datetime.datetime.now(pytz.utc).isoformat(),
                "ended_at_time": datetime.datetime.now(pytz.utc).isoformat(),
                "was_informed_by": self.nucelotide_sequencing_id
            }
            wfe = workflow_process_factory(record)
            db.workflow_execution_set.append(wfe)

        return db


    def get_workflow_execution_id(self, output_of: str) -> str:
        """Lookup and returns minted workflow execution id

        Args:
            output_of (str): The workflow execution type the data object is an output of.

        Returns:
            str: The workflow execution id for this workflow type.
        """
        if output_of not in self.workflow_execution_ids:
            wf = self.workflows_by_type[output_of]
            id = self.runtime.minter(wf["Type"]) + "." + self.iteration
            self.workflow_execution_ids[output_of] = id
            return id
        return self.workflow_execution_ids[output_of]

    def attach_objects_to_workflow_execution(
        self, workflow_execution_type: str
    ) -> Tuple[List[str], List[str]]:
        """
        Get data objects that inform workflow execution inputs and outputs.

        This function iterates through the stored objects, checking if the provided workflow_execution_type
        is in the 'input_to' or 'output_of' fields. If it is, the corresponding object is appended
        to the respective list (inputs or outputs).

        Args:
            workflow_execution_type (str): The type of nmdc workflow execution to relate object to.

        Returns:
            Tuple[List[str], List[str]]: Two lists containing the data object
            ids of the data objects that are inputs to and outputs of the specified
            workflow execution type.
        """

        has_input = []
        has_output = []

        for _, data_object_items in self.data_object_map.items():
            input_types, ouput_types, data_object_id = data_object_items
            if workflow_execution_type in input_types:
                has_input.append(data_object_id)
            if workflow_execution_type in ouput_types:
                has_output.append(data_object_id)

        return has_input, has_output
