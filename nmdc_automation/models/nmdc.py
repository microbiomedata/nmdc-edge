""" Factory methods for NMDC models. """
import importlib.resources
from typing import Any, Dict, Union
import linkml_runtime
import linkml.validator
import importlib.resources
from functools import lru_cache
from linkml_runtime.dumpers import yaml_dumper
import yaml


from nmdc_schema.nmdc import DataGeneration, FileTypeEnum, MagsAnalysis, MetagenomeAnnotation, MetagenomeAssembly, \
    MetatranscriptomeAnnotation, MetatranscriptomeAssembly, MetatranscriptomeExpressionAnalysis, NucleotideSequencing, \
    ReadBasedTaxonomyAnalysis, ReadQcAnalysis, WorkflowExecution
import nmdc_schema.nmdc as nmdc


@lru_cache(maxsize=None)
def get_nmdc_materialized():
    with importlib.resources.open_text("nmdc_schema", "nmdc_materialized_patterns.yaml") as f:
        return yaml.safe_load(f)

def workflow_process_factory(record: Dict[str, Any], validate: bool = False) -> Union[DataGeneration,
WorkflowExecution]:
    """
    Factory function to create a PlannedProcess subclass object from a record.
    Subclasses are determined by the "type" field in the record, and can be
    either a WorkflowExecution or DataGeneration object.
    """
    nmdc_materialized = get_nmdc_materialized()
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
    target_class = record["type"].split(":")[1]
    if validate:
        validation_report = linkml.validator.validate(record, nmdc_materialized, target_class)
        if validation_report.results:
            raise ValueError(f"Validation error: {validation_report.results[0].message}")

    try:
        cls = process_types[record["type"]]
    except KeyError:
        raise ValueError(f"Invalid workflow execution type: {record['type']}")
    wfe = cls(**record)
    return wfe


def _normalize_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """ Normalize the record by removing the _id field and converting the type field to a string """
    record.pop("_id", None)
    normalized_record = _strip_empty_values(record)
    if not normalized_record.get("type"):
        return normalized_record
    # get rid of any legacy 'Activity' suffixes in the type
    normalized_record["type"] = normalized_record["type"].replace("Activity", "")
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
        # strip output_dir if present
        if "output_dir" in mag:
            record["mags_list"][i].pop("output_dir")
        # add type to eukaryotic_evaluation if it exists
        if "eukaryotic_evaluation" in mag:
            record["mags_list"][i]["eukaryotic_evaluation"]["type"] = "nmdc:EukEval"
            # conpleteness and contamination need to be converted from string to float
            if "completeness" in mag["eukaryotic_evaluation"]:
                record["mags_list"][i]["eukaryotic_evaluation"]["completeness"] = float(mag["eukaryotic_evaluation"]["completeness"])
            if "contamination" in mag["eukaryotic_evaluation"]:
                record["mags_list"][i]["eukaryotic_evaluation"]["contamination"] = float(mag["eukaryotic_evaluation"]["contamination"])
        # gene count should be a positive integer - remove if 'null'
        if "gene_count" in mag and mag["gene_count"] == "null":
            mag.pop("gene_count")
    return record


def _strip_empty_values(d: Dict[str, Any]) -> Dict[str, Any]:
    """ Strip empty values from a record """
    empty_values = [None, "", []]
    def clean_dict(d):
        if isinstance(d, dict):
            return {k: clean_dict(v) for k, v in d.items() if v not in empty_values}
        elif isinstance(d, list):
            return [clean_dict(v) for v in d if v not in empty_values]
        return d
    return clean_dict(d)


class DataObject(nmdc.DataObject):
    """
    Extends the NMDC DataObject dataclass with additional methods for serialization.
    """
    def __init__(self, **record):
        """ Initialize the object from a dictionary """
        normalized_record = _normalize_record(record)
        if "type" not in record:
            record["type"] = "nmdc:DataObject"
        super().__init__(**record)

    def as_dict(self) -> Dict[str, Any]:
        """ Convert the object to a dictionary """
        return yaml.safe_load(yaml_dumper.dumps(self))
