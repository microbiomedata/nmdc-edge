""" Model classes for the workflow automation app. """
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from nmdc_automation.workflow_automation.workflows import Workflow
from nmdc_schema.nmdc import (
    DataGeneration,
    WorkflowExecution,
    NucleotideSequencing,
    MagsAnalysis,
    MetagenomeAssembly,
    MetagenomeAnnotation,
    MetatranscriptomeAssembly,
    MetatranscriptomeAnnotation,
    MetatranscriptomeExpressionAnalysis,
    PlannedProcess,
    ReadBasedTaxonomyAnalysis,
    ReadQcAnalysis,
)
process_types = {
    "nmdc:MagsAnalysis": MagsAnalysis,
    "nmdc:MetagenomeAnnotation": MetagenomeAnnotation,
    "nmdc:MetagenomeAssembly": MetagenomeAssembly,
    "nmdc:MetatranscriptomeAnnotation": MetatranscriptomeAnnotation,
    "nmdc:MetatranscriptomeAssembly": MetatranscriptomeAssembly,
    "nmdc:MetatranscriptomeExpressionAnalysis": MetatranscriptomeExpressionAnalysis,
    "nmdc:NucleotideSequencing": NucleotideSequencing,
    "nmdc:ReadBasedTaxonomyAnalysis": ReadBasedTaxonomyAnalysis,
    "nmdc:ReadQcAnalysis": ReadQcAnalysis,
}
def workflow_process_factory(record: Dict[str, Any]) -> PlannedProcess:
    """
    Factory function to create a PlannedProcess subclass object from a record.
    Subclasses are determined by the "type" field in the record, and can be
    either a WorkflowExecution or DataGeneration object.
    """
    record.pop("_id", None)
    try:
        cls = process_types[record["type"]]
    except KeyError:
        raise ValueError(f"Invalid workflow execution type: {record['type']}")
    return cls(**record)


class WorkflowProcessNode(object):
    """
    Class to represent a workflow execution node. This is a node in a tree
    structure that represents the execution hierarchy of data generation and
    workflow execution objects with their associated data objects.
    """
    def __init__(self, record: Dict[str, Any], workflow: Workflow):
        self.parent = None
        self.children = []
        self.data_objects_by_type = {}
        self.workflow = workflow
        process = workflow_process_factory(record)
        self.process = process

    def __hash__(self):
        return hash((self.id, self.type))

    def __eq__(self, other):
        return self.id == other.id and self.type == other.type

    def add_data_object(self, data_object):
        self.data_objects_by_type[data_object.data_object_type] = data_object

    @property
    def id(self):
        return self.process.id

    @property
    def type(self):
        return self.process.type

    @property
    def name(self):
        return self.process.name

    @property
    def has_input(self):
        return self.process.has_input

    @property
    def has_output(self):
        return self.process.has_output

    @property
    def git_url(self):
        """ workflow executions have a git_url field, data generations do not"""
        default_url = "http://github.com/microbiomedata"
        return getattr(self.process, "git_url", default_url)

    @property
    def version(self):
        """ workflow executions have a version field, data generations do not"""
        return getattr(self.process, "version", None)

    @property
    def analyte_category(self):
        """ data generations have an analyte_category field, workflow executions do not"""
        return getattr(self.process, "analyte_category", None)

    @property
    def was_informed_by(self):
        """ workflow executions have a was_informed_by field, data generations get set to their own id"""
        return getattr(self.process, "was_informed_by", self.id)




