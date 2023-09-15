import os
import re
import logging
import datetime
import pytz
import json
import yaml
from typing import List, Dict, Callable, Tuple
import nmdc_schema.nmdc as nmdc
from linkml_runtime.dumpers import json_dumper
from nmdc_automation.api import NmdcRuntimeApi
from .utils import (object_action, 
                    file_link, 
                    get_md5,
                    filter_import_by_type)

logger = logging.getLogger(__name__)

class GoldMapper:
    def __init__(
        self,
        iteration,
        file_list: List[str],
        omics_id: str,
        yaml_file: str,
        project_directory: str,
        site_config_file: str
    ):
        """
        Initialize the GoldMapper object.

        Args:
            file_list: List of file paths to be processed.
            omics_id: Identifier for the omics data.
            yaml_file: File path of the yaml file containing import data.
            root_directory: Root directory path.
            project_directory: Project directory path.
        """

        with open(yaml_file, "r") as file:
            self.import_data = yaml.safe_load(file)

        self.nmdc_db = nmdc.Database()
        self.iteration = iteration
        self.file_list = file_list
        self.omics_id = omics_id
        self.root_dir = os.path.join(
            self.import_data["Workflow Metadata"]["Root Directory"], omics_id
        )
        self.project_dir = project_directory
        self.url = self.import_data["Workflow Metadata"]["Source URL"]
        self.data_object_type = "nmdc:DataObject"
        self.objects = {}
        self.activity_ids = {}
        self.workflows_by_type = {}
        
        self.runtime = NmdcRuntimeApi(site_config_file)
        
        for wf in self.import_data["Workflows"]:
            self.workflows_by_type[wf["Type"]] = wf

    def unique_object_mapper(self) -> None:
        """
        Map unique data objects from the file list based on unique matching import suffix.
        The method relates each object to an activity ID and updates the file with object action.
        It updates the nmdc database with the DataObject and stores the information in the objects dictionary.
        """

        for data_object_dict in self.import_data["Data Objects"]["Unique"]:
            if not filter_import_by_type(self.import_data["Workflows"], data_object_dict["output_of"]):
                continue
            for file in self.file_list:
                if data_object_dict is None:
                    continue
                elif "import_suffix" not in data_object_dict:
                    logging.warning("Missing suffix")
                    continue

                elif re.search(data_object_dict["import_suffix"], file):
                    activity_id = self.get_activity_id(data_object_dict["output_of"])

                    file_destination_name = object_action(file, data_object_dict["action"], activity_id, data_object_dict["nmdc_suffix"])


                    activity_dir = os.path.join(self.root_dir, activity_id)

                    updated_file = file_link(
                        self.project_dir, file, activity_dir, file_destination_name
                    )

                    filemeta = os.stat(updated_file)

                    md5 = get_md5(updated_file)

                    dobj = self.runtime.minter(self.data_object_type)

                    self.nmdc_db.data_object_set.append(
                        nmdc.DataObject(
                            file_size_bytes=filemeta.st_size,
                            name=file_destination_name,
                            url=f"{self.url}/{self.omics_id}/{activity_id}/{file_destination_name}",
                            data_object_type=data_object_dict["data_object_type"],
                            type=self.data_object_type,
                            id=dobj,
                            md5_checksum=md5,

                            description=data_object_dict["description"].replace("{id}", self.omics_id)
                            ))
                    self.objects[data_object_dict["data_object_type"]] = (data_object_dict["input_to"], [data_object_dict["output_of"]], dobj)


    def multiple_objects_mapper(self) -> None:
        """
        Maps multiple data objects from the file list based on matching import suffix into one nmdc data object.
        The method relates each object to an activity ID and updates the file with object action.
        It updates the nmdc database with the DataObject and stores the information in the objects dictionary.
        """

        multiple_objects_list = []

        for data_object_dict in self.import_data["Data Objects"]["Multiples"]:
            for file in self.file_list:
                if re.search(data_object_dict["import_suffix"], file):
                    multiple_objects_list.append(file)


            activity_id = self.get_activity_id(data_object_dict["output_of"])


            activity_dir = os.path.join(self.root_dir, activity_id)

            file_destination_name = object_action(
                multiple_objects_list,
                data_object_dict["action"],
                activity_id,
                data_object_dict["nmdc_suffix"],
                activity_dir=activity_dir,
                multiple=True,
            )

            updated_file = file_link(
                self.project_dir,
                multiple_objects_list,
                activity_dir,
                file_destination_name,
            )

            filemeta = os.stat(updated_file)

            md5 = get_md5(updated_file)

            dobj = self.runtime.minter(self.data_object_type)

            self.nmdc_db.data_object_set.append(
                nmdc.DataObject(
                    file_size_bytes=filemeta.st_size,
                    name=data_object_dict["name"],
                    url=f"{self.url}/{self.omics_id}/{activity_dir}/{file_destination_name}",
                    data_object_type=data_object_dict["data_object_type"],
                    type=self.data_object_type,
                    id=dobj,
                    md5_checksum=md5,
                    description=data_object_dict["description"].replace(
                        "{id}", self.omics_id
                    ),
                )
            )

            self.objects[data_object_dict["data_object_type"]] = (
                data_object_dict["input_to"],
                [data_object_dict["output_of"]],
                dobj,
            )

    def activity_mapper(self) -> None:
        """
        Maps activities from the import data to the NMDC database.
        The function creates a database activity set for each workflow type in the import data,
        attaching the relevant input and output objects. It also provides other metadata for each activity.

        This method assumes that the import data includes a 'Workflows' section with each workflow having
        a 'Type', 'Git_repo', and 'Version'. It also assumes that the import data includes a 'Workflow Metadata'
        section with an 'Execution Resource'.
        """


        for workflow in self.import_data["Workflows"]:
            if not workflow.get("Import"):
                continue
            logging.info(f"Processing {workflow['Name']}")
            has_inputs_list, has_output_list = self.attach_objects_to_activity(workflow["Type"])
            # quick fix because nmdc-schema does not support [], even though raw product has none
            if len(has_output_list) == 0:
                logging.warning("No outputs.  That seems odd.")
                has_output_list = ["None"]
            #input may be none for metagenome sequencing
            if len(has_inputs_list) == 0:
                    has_inputs_list = ["None"]
            # Lookup the nmdc database class
            database_activity_set = getattr(self.nmdc_db, workflow["Collection"])
            # Lookup the nmdc schema range class
            database_activity_range = getattr(nmdc, workflow["ActivityRange"])
            # Mint an ID
            activity_id = self.get_activity_id(workflow["Type"])
            database_activity_set.append(
                database_activity_range(
                    id=activity_id,
                    name=workflow['Activity']['name'].replace("{id}", activity_id),
                    git_url=workflow['Git_repo'],
                    version=workflow['Version'],
                    part_of=[self.omics_id],
                    execution_resource=self.import_data['Workflow Metadata']['Execution Resource'],
                    started_at_time=datetime.datetime.now(pytz.utc).isoformat(),
                    has_input=has_inputs_list,
                    has_output=has_output_list,
                    type=workflow['Type'],
                    ended_at_time=datetime.datetime.now(pytz.utc).isoformat(),
                    was_informed_by=self.omics_id,
                ))

    def get_activity_id(self, output_of: str) -> str:
        '''Lookup and returns minted activity id

        Args:
            output_of (str): The activity type the data object is an output of.

        Returns:
            str: The activity id for this workflow type.
        '''
        if output_of not in self.activity_ids:
            wf = self.workflows_by_type[output_of]
            id = self.runtime.minter(wf["Type"]) + "." + self.iteration
            self.activity_ids[output_of] = id
            return id
        return self.activity_ids[output_of]


    def attach_objects_to_activity(
        self, activity_type: str
    ) -> Tuple[List[str], List[str]]:
        """
        Get data objects that inform activity inputs and outputs.

        This function iterates through the stored objects, checking if the provided activity_type
        is in the 'input_to' or 'output_of' fields. If it is, the corresponding object is appended
        to the respective list (inputs or outputs).

        Args:
            activity_type (str): The type of nmdc activity to relate object to.

        Returns:
            Tuple[List[str], List[str]]: Two lists containing the data object
            ids of the data objects that are inputs to and outputs of the specified
            activity type.
        """

        data_object_outputs_of_list = []

        data_object_inputs_to_list = []

        for _, data_object_items in self.objects.items():
            if activity_type in data_object_items[1]:
                data_object_outputs_of_list.append(data_object_items[2])
            elif activity_type in data_object_items[0]:
                data_object_inputs_to_list.append(data_object_items[2])

        return data_object_inputs_to_list, data_object_outputs_of_list

    def post_nmdc_database_object(self) -> Dict:
        """
        Post the nmdc database object.

        This function dumps the NMDC database object into JSON format, then posts
        it using the runtime API.

        Returns:
            Dict: The response from the runtime API after posting the object.
        """

        nmdc_database_object = json.loads(json_dumper.dumps(self.nmdc_db, inject_type=False))
        res = self.runtime.post_objects(nmdc_database_object)
        return res

    def get_database_object_dump(self) -> nmdc.Database:
        """
        Get the NMDC database object.

        Returns:
            nmdc.Database: NMDC database object.
        """
        return self.nmdc_db
