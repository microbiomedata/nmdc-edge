""" Model classes for the workflow automation app. """
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set

from nmdc_schema.nmdc import (
    FileTypeEnum,
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
from nmdc_schema import nmdc


def workflow_process_factory(record: Dict[str, Any]) -> PlannedProcess:
    """
    Factory function to create a PlannedProcess subclass object from a record.
    Subclasses are determined by the "type" field in the record, and can be
    either a WorkflowExecution or DataGeneration object.
    """
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
    def __init__(self, record: Dict[str, Any], workflow: "WorkflowConfig"):
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


class DataObject(nmdc.DataObject):
    """
    Extends the NMDC DataObject dataclass with additional methods for serialization.
    """
    def __init__(self, **record):
        """ Initialize the object from a dictionary """
        # _id is a MongoDB field that makes the parent class fail to initialize
        record.pop("_id", None)
        super().__init__(**record)

    def as_dict(self):
        """ Return the object as a dictionary, excluding None values, empty lists, and data_object_type as a string """
        return {
            key: value
            for key, value in self.__dict__.items()
            if not key.startswith("_") and value
        } | {"data_object_type": self.data_object_type}

    @property
    def data_object_type(self):
        """ Return the data object type as a string """
        if isinstance(self._data_object_type, FileTypeEnum):
            return self._data_object_type.code.text
        return str(self._data_object_type)

    @data_object_type.setter
    def data_object_type(self, value):
        """ Set the data object type from a string or FileTypeEnum """
        if isinstance(value, FileTypeEnum):
            self._data_object_type = value
        else:
            self._data_object_type = FileTypeEnum(value)


@dataclass
class WorkflowConfig:
    """ Configuration for a workflow execution """
    # Sequencing workflows only have these fields
    name: str
    collection: str
    enabled: bool
    analyte_category: str
    filter_output_objects: List[str]
    # TODO should type be optional?
    type: Optional[str] = None

    # workflow repository information
    git_repo: Optional[str] = None
    version: Optional[str] = None
    wdl: Optional[str] = None
    # workflow execution and input / output information
    filter_output_objects: List[str] = field(default_factory=list)
    predecessors: List[str] = field(default_factory=list)
    filter_input_objects: List[str] = field(default_factory=list)
    input_prefix: str = None
    inputs: Dict[str, str] = field(default_factory=dict)
    optional_inputs: List[str] = field(default_factory=list)
    workflow_execution: Dict[str, Any] = field(default_factory=dict)
    outputs: List[Dict[str, str]] = field(default_factory=list)

    # populated after initialization
    children: Set["WorkflowConfig"] = field(default_factory=set)
    parents: Set["WorkflowConfig"] = field(default_factory=set)
    data_object_types: List[str] = field(default_factory=list)

    def __post_init__(self):
        """ Initialize the object """
        for _, inp_param in self.inputs.items():
            if inp_param.startswith("do:"):
                self.data_object_types.append(inp_param[3:])
        if not self.type:
            # Infer the type from the name
            if self.collection == 'data_generation_set' and 'Sequencing' in self.name:
                self.type = 'nmdc:NucleotideSequencing'

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name


    def add_child(self, child: "WorkflowConfig"):
        """ Add a child workflow """
        self.children.add(child)

    def add_parent(self, parent: "WorkflowConfig"):
        """ Add a parent workflow """
        self.parents.add(parent)