""" This module reads the workflows yaml file and returns a list of WorkflowConfig objects"""
from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from nmdc_automation.models.workflow import WorkflowConfig


def load_workflow_configs(yaml_file) -> list[WorkflowConfig]:
    """
    Read the workflows yaml file and return a list of WorkflowConfig objects
    """
    workflow_configs = []
    data = load(open(yaml_file), Loader)
    for wf in data["Workflows"]:
        # normalize the keys from Key Name to key_name
        wf = {k.replace(" ", "_").lower(): v for k, v in wf.items()}
        workflow_configs.append(WorkflowConfig(**wf))
    # Populate workflow dependencies
    for wf in workflow_configs:
        for wf2 in workflow_configs:
            if not wf2.predecessors:
                continue
            if wf.name in wf2.predecessors:
                wf.add_child(wf2)
                wf2.add_parent(wf)
    return workflow_configs
