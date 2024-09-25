import logging
from functools import lru_cache
from typing import List, Optional

from semver.version import Version

from nmdc_automation.workflow_automation.workflows import Workflow
from nmdc_schema.nmdc import WorkflowExecution

# TODO: Berkley refactoring:
#   The load_activities method will need to be modified to handle DataGeneration objects
#   instead of OmicsProcessing objects, with the difference being the DataGeneration objects can be part_of other
#   DataGeneration objects. This will require a change in the way the parent/child relationships are resolved.
#   Need to add logic to find the correct parent DataGeneration to use for constructing the Activity graph and
#   correctly setting the was_informed_by field.
#   Add unit tests to cover the new behavior, mocking the MongoDB database and the Berkley style DataGeneration objects.
#   DataGeneration is an abstract class, include specific tests for subclasses NucleotideSequencing or MassSpectrometry

warned_objects = set()


def get_required_data_objects_map(db, workflows: List[Workflow]) -> dict:
    """
     Search for all the data objects that are required data object types for the workflows,
        and return a dictionary of data objects by ID.

    TODO: In the future this will probably need to be redone
    since the number of data objects could get very large.
    """

    # Build up a filter of what types are used
    required_types = set()
    for wf in workflows:
        required_types.update(set(wf.do_types))

    required_data_objs_by_id = dict()
    for rec in db.data_object_set.find():
        do = DataObject(rec)
        if do.data_object_type not in required_types:
            continue
        required_data_objs_by_id[do.id] = do
    return required_data_objs_by_id


@lru_cache
def _within_range(ver1: str, ver2: str) -> bool:
    """
    Determine if two workflows are within a major and minor
    version of each other.
    """

    def get_version(version):
        v_string = version.lstrip("b").lstrip("v").rstrip("-beta")
        return Version.parse(v_string)

    v1 = get_version(ver1)
    v2 = get_version(ver2)
    if v1.major == v2.major and v1.minor == v2.minor:
        return True
    return False


def _check(match_types, data_object_ids, data_objs):
    """
    This iterates through a list of data objects and
    checks the type against the match types.
    """
    if not data_object_ids:
        return False
    if not match_types or len(match_types) == 0:
        return True
    match_set = set(match_types)
    do_types = set()
    for doid in data_object_ids:
        if doid in data_objs:
            do_types.add(data_objs[doid].data_object_type)
    return match_set.issubset(do_types)


def _is_missing_required_input_output(wf, rec, data_objs):
    """
    Some workflows require specific inputs or outputs.  This
    implements the filtering for those.
    """
    match_in = _check(
        wf.filter_input_objects, rec.get("has_input"), data_objs
    )
    match_out = _check(
        wf.filter_output_objects, rec.get("has_output"), data_objs
    )
    return not (match_in and match_out)


def get_workflow_executions(db, workflows: List[Workflow], data_objects: dict, allowlist: Optional[set] = None):
    """
    Fetch the relevant workflow executions from the database for the given workflows.
        1. Get the Data Generation (formerly Omics Processing) objects for the workflows by analyte category.
        2. Get the remaining Workflow Execution objects that was_informed_by the Data Generation objects.
        3. Filter Workflow Execution objects by:
            - version (within range) if specified in the workflow
            - input and output data objects required by the workflow
    Return the list of Workflow Execution objects.
    """
    workflow_executions = set()
    analyte_category = _determine_analyte_category(workflows)

    # We handle the data generation and data processing workflows separately. Data generation workflow executions have an
    # analyte category field, while data processing workflow executions do not, so we filter by the was_informed_by field.
    data_generation_ids = set()
    dg_workflows = [wf for wf in workflows if wf.collection in ["omics_processing_set", "data_generation_set"]]
    dp_workflows = [wf for wf in workflows if not wf.collection in ["omics_processing_set", "data_generation_set"]]

    # default query
    q = {"analyte_category": analyte_category}
    # override query with allowlist
    if allowlist:
        q["id"] = {"$in": list(allowlist)}
    dg_execution_records = db["data_generation_set"].find(q)
    # change from cursor to list
    dg_execution_records = list(dg_execution_records)

    for wf in dg_workflows:
        # Sequencing workflows don't have a git repo
        default_git_url = "https://github.com/microbiomedata"
        for rec in dg_execution_records:
            if _is_missing_required_input_output(wf, rec, data_objects):
                continue
            data_generation_ids.add(rec["id"])
            act = WorkflowExecutionNode(rec, wf)
            act.was_informed_by = rec["id"]
            workflow_executions.add(act)

    for wf in dp_workflows:
        q = {}
        if wf.git_repo:
            q = {"git_url": wf.git_repo}
        # override query with allowlist
        if allowlist:
            q = {"was_informed_by": {"$in": list(allowlist)}}

        records = db[wf.collection].find(q)
        for rec in records:
            if wf.version and not _within_range(rec["version"], wf.version):
                continue
            if _is_missing_required_input_output(wf, rec, data_objects):
                continue
            if rec["was_informed_by"] in data_generation_ids:
                act = WorkflowExecutionNode(rec, wf)
                workflow_executions.add(act)

    return list(workflow_executions)


def _determine_analyte_category(workflows: List[Workflow]) -> str:
    analyte_categories = set([wf.analyte_category for wf in workflows])
    if len(analyte_categories) > 1:
        raise ValueError("Multiple analyte categories not supported")
    elif len(analyte_categories) == 0:
        raise ValueError("No analyte category found")
    analyte_category = analyte_categories.pop()
    return analyte_category.lower()


# TODO: Make public, give a better name, add type hints and unit tests.
def _resolve_relationships(activities, data_obj_act):
    """
    Find the parents and children relationships
    between the activities
    """
    # We now have a list of all the activites and
    # a map of all of the data objects they generated.
    # Let's use this to find the parent activity
    # for each child activity
    for act in activities:
        logging.debug(f"Processing {act.id} {act.name} {act.workflow.name}")
        act_pred_wfs = act.workflow.parents
        if not act_pred_wfs:
            logging.debug("- No Predecessors")
            continue
        # Go through its inputs
        for do_id in act.has_input:
            if do_id not in data_obj_act:
                # This really shouldn't happen
                if do_id not in warned_objects:
                    logging.warning(f"Missing data object {do_id}")
                    warned_objects.add(do_id)
                continue
            parent_act = data_obj_act[do_id]
            # This is to cover the case where it was a duplicate.
            # This shouldn't happen in the future.
            if not parent_act:
                logging.warning("Parent act is none")
                continue
            # Let's make sure these came from the same source
            # This is just a safeguard
            if act.was_informed_by != parent_act.was_informed_by:
                logging.warning(
                    "Mismatched informed by for "
                    f"{do_id} in {act.id} "
                    f"{act.was_informed_by} != "
                    f"{parent_act.was_informed_by}"
                )
                continue
            # We only want to use it as a parent if it is the right
            # parent workflow. Some inputs may come from ancestors
            # further up
            if parent_act.workflow in act_pred_wfs:
                # This is the one
                act.parent = parent_act
                parent_act.children.append(act)
                logging.debug(
                    f"Found parent: {parent_act.id}"
                    f" {parent_act.name}"
                )
                break
        if len(act.workflow.parents) > 0 and not act.parent:
            if act.id not in warned_objects:
                logging.warning(f"Didn't find a parent for {act.id}")
                warned_objects.add(act.id)
    # Now all the activities have their parent
    return activities


def _find_data_object_activities(activities, data_objs_by_id):
    """
    Find the activity that generated each data object to
    use in the relationship method.
    """
    data_obj_act = dict()
    for act in activities:
        for do_id in act.has_output:
            if do_id in data_objs_by_id:
                do = data_objs_by_id[do_id]
                act.add_data_object(do)
            # If its a dupe, set it to none
            # so we can ignore it later.
            # Once we re-id the data objects this
            # shouldn't happen
            if do_id in data_obj_act:
                if do_id not in warned_objects:
                    logging.warning(f"Duplicate output object {do_id}")
                    warned_objects.add(do_id)
                data_obj_act[do_id] = None
            else:
                data_obj_act[do_id] = act
    return data_obj_act


# TODO: Give a better name, add unit tests.
#   This function builds up the graph of related parent / child Execution objects and is
#   key to the behavior of workflow automation.
def load_activities(db, workflows: list[Workflow], allowlist: set = set()):
    """
    This reads the activities from Mongo.  It also
    finds the parent and child relationships between
    the activities using the has_output and has_input
    to connect things.

    Finally it creates a map of data objects by type
    for each activity.

    Inputs:
    db: mongo database
    workflow: workflow
    """

    # This is map from the data object ID to the activity
    # that created it.
    data_objs_by_id = get_required_data_objects_map(db, workflows)

    # Build up a set of relevant activities and a map from
    # the output objects to the activity that generated them.
    workflow_executions = get_workflow_executions(db, workflows, data_objs_by_id, allowlist)

    data_obj_act = _find_data_object_activities(workflow_executions, data_objs_by_id)

    # Now populate the parent and children values for the
    # activities
    _resolve_relationships(workflow_executions, data_obj_act)
    return workflow_executions


# TODO: Why are we not importing and using the existing nmdc_schema.DataObject class?
#   nmdc_schema.DataObject is stricter and using it currently causes tests / fixtures to fail.
#   We should fix the tests and fixtures to use the stricter class and remove this class.
class DataObject(object):
    """
    Data Object Class
    """

    _FIELDS = ["id", "name", "description", "url", "md5_checksum", "file_size_bytes", "data_object_type", ]

    def __init__(self, rec: dict):
        for f in self._FIELDS:
            setattr(self, f, rec.get(f))


# TODO: Give a better 'Execution' based name, expand docstring, and make sure it is covered by unit tests.
#   This class represents a network of related WorkflowExecution objects and their associated DataObject objects.
class Activity(object):
    """
    Activity Object Class
    """

    _FIELDS = ["id", "name", "git_url", "version", "has_input", "has_output", "was_informed_by", "type", ]

    def __init__(self, activity_rec: dict, wf: Workflow):
        self.parent = None
        self.children = []
        self.data_objects_by_type = dict()
        self.workflow = wf
        for f in self._FIELDS:
            setattr(self, f, activity_rec.get(f))
        if self.type == "nmdc:NucleotideSequencing":
            self.was_informed_by = self.id

    def add_data_object(self, do: DataObject):
        self.data_objects_by_type[do.data_object_type] = do


class WorkflowExecutionNode(WorkflowExecution):
    """
    Data class that extends the NMDC WorkflowExecution class.
    The WorkflowExecutionNode class is used to represent a network of related workflow execution and
    data generation events and their associated DataObject objects.
    """

    def __init__(self, record: dict, wf: Workflow):
        """
        Initialize the WorkflowExecutionNode object with the given record and workflow.
        The record may be for a DataGeneration or WorkflowExecution object.
        In the case of a DataGeneration object, the was_informed_by field is set to the id of the DataGeneration object,
        and the record is massaged to look like a WorkflowExecution object.
        """
        record.pop("_id", None)
        if not record.get("git_url"):
            record["git_url"] = "http://github.com/microbiomedata"
        if not record.get("started_at_time"):
            record["started_at_time"] = record.get("add_date", "2024-01-01T00:00:00Z")
        analyte_category = None
        if record["type"] == "nmdc:NucleotideSequencing":
            record["was_informed_by"] = record["id"]
            analyte_category = record.pop("analyte_category")
            record.pop("associated_studies")
            record.pop("principal_investigator")

        super().__init__(**record)
        self.parent = None
        self.children = []
        self.data_objects_by_type = dict()
        self.workflow = wf
        self.analyte_category = analyte_category


    def add_data_object(self, do: DataObject):
        self.data_objects_by_type[do.data_object_type] = do