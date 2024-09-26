""" Model classes for the workflow automation app. """
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from nmdc_automation.workflow_automation.workflows import Workflow
from nmdc_schema.nmdc import (
    WorkflowExecution,
    NucleotideSequencing,
    MagsAnalysis,
    MetagenomeAssembly,
    MetagenomeAnnotation,
    MetatranscriptomeAssembly,
    MetatranscriptomeAnnotation,
    MetatranscriptomeExpressionAnalysis,
    ReadBasedTaxonomyAnalysis,
    ReadQcAnalysis,
)
workflow_types = {
    "nmdc:NucleotideSequencing": NucleotideSequencing,
    "nmdc:MagsAnalysis": MagsAnalysis,
    "nmdc:MetagenomeAnnotation": MetagenomeAnnotation,
    "nmdc:MetagenomeAssembly": MetagenomeAssembly,
    "nmdc:MetatranscriptomeAnnotation": MetatranscriptomeAnnotation,
    "nmdc:MetatranscriptomeAssembly": MetatranscriptomeAssembly,
    "nmdc:MetatranscriptomeExpressionAnalysis": MetatranscriptomeExpressionAnalysis,
    "nmdc:ReadBasedTaxonomyAnalysis": ReadBasedTaxonomyAnalysis,
    "nmdc:ReadQcAnalysis": ReadQcAnalysis,
}

def workflow_execution_factory(record: Dict[str, Any]) -> WorkflowExecution:
    """
    Factory function to create a WorkflowExecution object from a record.
    """
    record.pop("_id", None)
    try:
        cls = workflow_types[record["type"]]
    except KeyError:
        raise ValueError(f"Invalid workflow execution type: {record['type']}")
    return cls(**record)



class WorkflowExecutionNode(object):
    """
    Class to represent a workflow execution node.
    Represents a node in a workflow execution graph of data generation and workflow execution nodes,
    and their associated data objects.
    """
