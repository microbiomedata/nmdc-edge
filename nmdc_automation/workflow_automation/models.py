""" Model classes for the workflow automation app. """
from dataclasses import dataclass, field
from dateutil import parser
from datetime import datetime
from typing import List, Dict, Any, Optional, Set, Union

from nmdc_schema.nmdc import (
    DataGeneration,
    FileTypeEnum,
    NucleotideSequencing,
    MagsAnalysis,
    MetagenomeAssembly,
    MetagenomeAnnotation,
    MetatranscriptomeAssembly,
    MetatranscriptomeAnnotation,
    MetatranscriptomeExpressionAnalysis,
    ReadBasedTaxonomyAnalysis,
    ReadQcAnalysis,
    WorkflowExecution
)
from nmdc_schema import nmdc


def workflow_process_factory(record: Dict[str, Any]) -> Union[DataGeneration, WorkflowExecution]:
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
    record = _normalize_record(record)

    try:
        cls = process_types[record["type"]]
    except KeyError:
        raise ValueError(f"Invalid workflow execution type: {record['type']}")
    wfe = cls(**record)
    return wfe

def _normalize_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """ Normalize the record by removing the _id field and converting the type field to a string """
    record.pop("_id", None)
    # for backwards compatibility strip Activity from the end of the type
    record["type"] = record["type"].replace("Activity", "")
    normalized_record = _strip_empty_values(record)

    # type-specific normalization
    if normalized_record["type"] == "nmdc:MagsAnalysis":
        normalized_record = _normalize_mags_record(normalized_record)

    return normalized_record

def _normalize_mags_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """ Normalize the record for a MagsAnalysis object """
    for i, mag in enumerate(record.get("mags_list", [])):
        if not mag.get("type"):
            # Update the original dictionary in the list
            record["mags_list"][i]["type"] = "nmdc:MagBin"
        # for backwards compatibility normalize num_tRNA to num_t_rna
        if "num_tRNA" in mag:
            record["mags_list"][i]["num_t_rna"] = mag.pop("num_tRNA")
        # add type to eukaryotic_evaluation if it exists
        if "eukaryotic_evaluation" in mag:
            record["mags_list"][i]["eukaryotic_evaluation"]["type"] = "nmdc:EukEval"
    return record


def _strip_empty_values(d: Dict[str, Any]) -> Dict[str, Any]:
    """ Strip empty values from a record """
    empty_values = [None, "", [], "null", 0]
    def clean_dict(d):
        if isinstance(d, dict):
            return {k: clean_dict(v) for k, v in d.items() if v not in empty_values}
        elif isinstance(d, list):
            return [clean_dict(v) for v in d if v not in empty_values]
        return d
    return clean_dict(d)


class WorkflowProcessNode(object):
    """
    Class to represent a workflow processing node. This is a node in a tree
    structure that represents the tree of data generation and
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
        return getattr(self.process, "git_url", None)

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
        if "type" not in record:
            record["type"] = "nmdc:DataObject"
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
    """ Configuration for a workflow execution. Defined by .yaml files in nmdc_automation/config/workflows """
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


@dataclass
class JobWorkflow:
    id: str

@dataclass
class JobConfig:
    """ Represents a job configuration from the NMDC API jobs endpoint / MongoDB jobs collection """
    git_repo: str
    release: str
    wdl: str
    activity_id: str
    activity_set: str
    was_informed_by: str
    trigger_activity: str
    iteration: int
    input_prefix: str
    inputs: Dict[str, str]
    input_data_objects: List[DataObject]
    activity: Dict[str, str]
    outputs: List[Dict[str, str]]


@dataclass
class JobClaim:
    op_id: str
    site_id: str

@dataclass
class JobOutput:
    """ Represents a job output specification. """
    output: str
    data_object: DataObject = field(init=False)

    # Raw fields that will map to DataObject fields
    data_object_type: str
    description: Optional[str]
    name: str
    id: str

    def __post_init__(self):
        """ Initialize the object """
        self.data_object = DataObject(
            id=self.id,
            name=self.name,
            data_object_type=self.data_object_type,
            description=self.description,
        )

@dataclass
class Job:
    """ Represents a job from the NMDC API jobs endpoint / MongoDB jobs collection """
    id: str
    workflow: JobWorkflow
    config: JobConfig
    created_at: Optional[datetime] = field(default=None)
    claims: List[JobClaim] = field(default_factory=list)

    def __post_init__(self):
        """ If created_at is a string, convert it to a datetime object """
        if isinstance(self.created_at, str):
            self.created_at = parser.isoparse(self.created_at)

        if isinstance(self.workflow, dict):
            self.workflow = JobWorkflow(**self.workflow)

        if isinstance(self.config, dict):
            self.config = JobConfig(**self.config)

        if isinstance(self.claims, list):
            self.claims = [JobClaim(**claim) for claim in self.claims]
