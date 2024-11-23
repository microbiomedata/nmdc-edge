""" This module contains functions to load workflow process nodes from the database. """
import logging
from functools import lru_cache
from typing import List, Dict

from semver.version import Version

from nmdc_automation.models.nmdc import DataObject
from nmdc_automation.models.workflow import WorkflowConfig, WorkflowProcessNode

warned_objects = set()


def get_required_data_objects_map(db, workflows: List[WorkflowConfig]) -> Dict[str, DataObject]:
    """
     Search for all the data objects that are required data object types for the workflows,
        and return a dictionary of data objects by ID.

    TODO: In the future this will probably need to be redone
    since the number of data objects could get very large.
    """

    # Build up a filter of what types are used
    required_types = set()
    for wf in workflows:
        required_types.update(set(wf.data_object_types))

    required_data_object_map = dict()
    for rec in db.data_object_set.find({"data_object_type": {"$ne": None}}):
        data_object = DataObject(**rec)
        if data_object.data_object_type.code.text not in required_types:
            continue
        required_data_object_map[data_object.id] = data_object
    return required_data_object_map


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
            do_types.add(data_objs[doid].data_object_type.code.text)
    return match_set.issubset(do_types)


def _is_missing_required_input_output(wf: WorkflowConfig, rec: dict, data_objects_by_id: Dict[str, DataObject]) -> bool:
    """
    Some workflows require specific inputs or outputs.  This
    implements the filtering for those.
    """
    match_in = _check(
        wf.filter_input_objects, rec.get("has_input"), data_objects_by_id
    )
    match_out = _check(
        wf.filter_output_objects, rec.get("has_output"), data_objects_by_id
    )
    return not (match_in and match_out)


def get_current_workflow_process_nodes(
        db, workflows: List[WorkflowConfig],
        data_objects_by_id: Dict[str, DataObject], allowlist: List[str] = None) -> List[WorkflowProcessNode]:
    """
    Fetch the relevant workflow process nodes for the given workflows.
        1. Get the Data Generation (formerly Omics Processing) records for the workflows by analyte category.
        2. Get the remaining Workflow Execution records that was_informed_by the Data Generation objects.
        3. Filter Workflow Execution records by:
            - version (within range) if specified in the workflow
            - input and output data objects required by the workflow
    Returns a list of WorkflowProcessNode objects.
    """
    workflow_process_nodes = set()
    analyte_category = _determine_analyte_category(workflows)

    data_generation_ids = set()
    data_generation_workflows = [wf for wf in workflows if wf.collection == "data_generation_set"]

    workflow_execution_workflows = [wf for wf in workflows if wf.collection == "workflow_execution_set"]

    # default query for data_generation_set records filtered by analyte category
    q = {"analyte_category": analyte_category}
    # override query with allowlist
    if allowlist:
        q["id"] = {"$in": list(allowlist)}
    dg_execution_records = db["data_generation_set"].find(q)
    dg_execution_records = list(dg_execution_records)

    for wf in data_generation_workflows:
        # Sequencing workflows don't have a git repo
        for rec in dg_execution_records:
            if _is_missing_required_input_output(wf, rec, data_objects_by_id):
                continue
            data_generation_ids.add(rec["id"])
            wfp_node = WorkflowProcessNode(rec, wf)
            workflow_process_nodes.add(wfp_node)

    for wf in workflow_execution_workflows:
        q = {}
        if wf.git_repo:
            q = {"git_url": wf.git_repo}
        # override query with allowlist
        if allowlist:
            q = {"was_informed_by": {"$in": list(allowlist)}}

        records = db[wf.collection].find(q)
        for rec in records:
            # legacy JGI sequencing records
            if rec.get("type") == "nmdc:MetagenomeSequencing" or rec["name"].startswith("Metagenome Sequencing"):
                continue
            if wf.version and not _within_range(rec["version"], wf.version):
                continue
            if _is_missing_required_input_output(wf, rec, data_objects_by_id):
                continue
            if rec["was_informed_by"] in data_generation_ids:
                wfp_node = WorkflowProcessNode(rec, wf)
                workflow_process_nodes.add(wfp_node)

    return list(workflow_process_nodes)


def _determine_analyte_category(workflows: List[WorkflowConfig]) -> str:
    analyte_categories = set([wf.analyte_category for wf in workflows])
    if len(analyte_categories) > 1:
        raise ValueError("Multiple analyte categories not supported")
    elif len(analyte_categories) == 0:
        raise ValueError("No analyte category found")
    analyte_category = analyte_categories.pop()
    return analyte_category.lower()


# TODO: Make public, give a better name, add type hints and unit tests.
def _resolve_relationships(current_nodes: List[WorkflowProcessNode], node_data_object_map: Dict[str, WorkflowProcessNode]) -> List[WorkflowProcessNode]:
    """
    Find the parents and children relationships
    between the activities
    """
    # We now have a list of all the activites and
    # a map of all of the data objects they generated.
    # Let's use this to find the parent activity
    # for each child activity
    for node in current_nodes:
        logging.debug(f"Processing {node.id} {node.name} {node.workflow.name}")
        node_predecessors = node.workflow.parents
        if not node_predecessors:
            logging.debug("- No Predecessors")
            continue
        # Go through its inputs
        for data_object_id in node.has_input:
            if data_object_id not in node_data_object_map:
                # This really shouldn't happen
                if data_object_id not in warned_objects:
                    logging.warning(f"Missing data object {data_object_id}")
                    warned_objects.add(data_object_id)
                continue
            parent_node = node_data_object_map[data_object_id]
            # This is to cover the case where it was a duplicate.
            # This shouldn't happen in the future.
            if not parent_node:
                logging.warning("Parent node is none")
                continue
            # Let's make sure these came from the same source
            # This is just a safeguard
            if node.was_informed_by != parent_node.was_informed_by:
                logging.warning(
                    "Mismatched informed by for "
                    f"{data_object_id} in {node.id} "
                    f"{node.was_informed_by} != "
                    f"{parent_node.was_informed_by}"
                )
                continue
            # We only want to use it as a parent if it is the right
            # parent workflow. Some inputs may come from ancestors
            # further up
            if parent_node.workflow in node_predecessors:
                # This is the one
                node.parent = parent_node
                parent_node.children.append(node)
                logging.debug(
                    f"Found parent: {parent_node.id}"
                    f" {parent_node.name}"
                )
                break
        if len(node.workflow.parents) > 0 and not node.parent:
            if node.id not in warned_objects:
                logging.info(f"Skipping obsolete WorkflowExecution: {node.id}, {node.type} {node.version}")
                warned_objects.add(node.id)
    # Now all the activities have their parent
    return current_nodes


def _map_nodes_to_data_objects(current_nodes: List[WorkflowProcessNode], required_data_object_map):
    """
    Associate the data objects with workflow process nodes
    """
    node_data_object_map = dict()
    for node in current_nodes:
        for data_object_id in node.has_output:
            if data_object_id in required_data_object_map:
                do = required_data_object_map[data_object_id]
                node.add_data_object(do)

            if data_object_id in node_data_object_map:
                if data_object_id not in warned_objects:
                    logging.warning(f"Duplicate output object {data_object_id}")
                    warned_objects.add(data_object_id)
                node_data_object_map[data_object_id] = None
            else:
                node_data_object_map[data_object_id] = node
    return node_data_object_map, current_nodes


def load_workflow_process_nodes(db, workflows: list[WorkflowConfig], allowlist: list[str] = None) -> List[WorkflowProcessNode]:
    """
    This reads the activities from Mongo.  It also
    finds the parent and child relationships between
    the activities using the has_output and has_input
    to connect things.

    Finally, it creates a map of data objects by type
    for each activity.

    Inputs:
    db: mongo database
    workflow: workflow
    """

    # This is map from the data object ID to the activity
    # that created it.
    data_object_map = get_required_data_objects_map(db, workflows)

    # Build up a set of relevant activities and a map from
    # the output objects to the activity that generated them.
    current_nodes = get_current_workflow_process_nodes(db, workflows, data_object_map, allowlist)

    node_data_object_map, current_nodes = _map_nodes_to_data_objects(current_nodes, data_object_map)

    # Now populate the parent and children values for the
    resolved_nodes = _resolve_relationships(current_nodes, node_data_object_map)
    return resolved_nodes

