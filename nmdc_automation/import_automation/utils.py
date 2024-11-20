from zipfile import ZipFile
from typing import Union, List
import logging
import hashlib
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def object_action(
    file_s: Union[str, List[str]],
    action: str,
    workflow_execution_id: str,
    nmdc_suffix: str,
    workflow_execution_dir: Union[str, Path] = None,
    multiple: bool = False,
) -> str:
    """
    Perform an action (non, rename, zip) on an object based on the provided parameters.

    Args:
        file_s (Union[str, List[str]]): The object or list of objects to perform the action on.
        action (str): The action to perform. Possible values are 'none', 'rename', or 'zip'.
        workflow_execution_id (str): The workflow execution subclass ID associated with the object.
        nmdc_suffix (str): The NMDC suffix.
        workflow_execution_dir (str or Path, optional): The directory where the workflow execution subclass is located. Defaults to None.
        multiple (bool, optional): Indicates if multiple files are involved. Defaults to False.

    Returns:
        str: Expected file name for import

    """

    if action == "none":
        return get_basename(file_s)
    elif action == "rename":
        return rename(workflow_execution_id, nmdc_suffix)
    elif action == "zip":
        if multiple:
            zip_names = []
            for file in file_s:
                zip_name = zip_file(workflow_execution_id, nmdc_suffix, file, workflow_execution_dir)
                zip_names.append(zip_name)
            return zip_names[0]
        else:
            return zip_file(file_s)
    else:
        logger.error(f"No mapping action found for {file_s}")


def get_basename(file: str) -> str:
    """
    Get file basename

    Args:
        file: import file

    Returns:
        str: file basename
    """

    return os.path.basename(file)


def rename(workflow_execution_id: str, nmdc_suffix: str) -> str:
    """
    Renames file to target nmdc target workflow execution name

    Args:
        workflow_execution_id (str): workflow execution id for corresponding data object
        nmdc_suffix (str): expected target suffix

    Returns:
        str: nmdc file name
    """

    workflow_execution_file_id = workflow_execution_id.replace(":", "_")

    nmdc_file_name = workflow_execution_file_id + nmdc_suffix

    return nmdc_file_name


def zip_file(workflow_execution_id: str, nmdc_suffix: str, file: str, project_dir: str):
    """Add files of type Multiples to a zip file and represent as one data object

    Args:
        workflow_execution_id (str): The activity ID associated with the object.
        nmdc_suffix (str): The NMDC suffix.
        file (str): The file associated with objects of type Multiples.
        project_dir (str, optional): The directory where the activity is located.

    Returns:
        str: Expected file name for import of Multiples as one data object.

    """

    zip_file_name = rename(workflow_execution_id, nmdc_suffix)

    if not os.path.exists(os.path.join(project_dir, zip_file_name)):
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)
        with ZipFile(os.path.join(project_dir, zip_file_name), mode="w") as zipped_file:
            zipped_file.write(file)
    else:
        with ZipFile(os.path.join(project_dir, zip_file_name), mode="a") as zipped_file:
            zipped_file.write(file)

    return zip_file_name


def file_link(
    import_project_dir: str,
    import_file: Union[str, List[str]],
    destination_dir: str,
    updated_file: str,
):
    """
    Link original file to nmdc file on system path

    Args:
        import_project_dir (str): Directory of project being imported
        import_file (Union[str, List[str]]): Filed be imported
        destination_dir (str): Destination directory of nmdc compliant file
        updated_file (str): nmdcc compliant file

    Returns:
        str: os linked path of updated file
    """

    if type(import_file) == list:
        logging.info(
            "Object has already been linked in objection specific import action"
        )
        return os.path.join(destination_dir, updated_file)

    elif type(import_file) == str:
        try:
            os.makedirs(destination_dir)
        except FileExistsError:
            logger.debug(f"{destination_dir} already exists")

        original_path = os.path.join(import_project_dir, import_file)
        linked_path = os.path.join(destination_dir, updated_file)

        try:
            os.link(import_file, linked_path)
        except FileExistsError:
            logger.info(f"{linked_path} already exists")

        return linked_path


def get_md5(fn: str) -> str:
    """
    Generate md5 for file

    Args:
        fn (str): file name

    Returns:
        md5:  md5 hash of file
    """

    md5f = fn + ".md5"
    if os.path.exists(md5f):
        with open(md5f) as f:
            md5 = f.read().rstrip()
    else:
        md5 = hashlib.md5(open(fn, "rb").read()).hexdigest()
        with open(md5f, "w") as f:
            f.write(md5)
            f.write("\n")
    return md5


def filter_import_by_type(workflow_data: dict, nmdc_type: str) -> dict:
    """
    Filter workflows and check if they should be imported

    Args:
        workflow_data (dict): Workflows
        nmdc_type (str): nmdc:xxxxxWorkflowExecution

    Returns:
        dict: Filtered workflows
    """

    for workflow in workflow_data:
        if workflow["Type"] == nmdc_type:
            return workflow["Import"]
