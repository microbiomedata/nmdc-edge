""" Factory methods for NMDC models. """
import importlib.resources
from typing import Any, Dict, Union
import linkml_runtime
import linkml.validator

import yaml

with importlib.resources.open_text("nmdc_schema", "nmdc_materialized_patterns.yaml") as f:
    nmdc_materialized = yaml.safe_load(f)


from nmdc_schema.nmdc import DataGeneration, FileTypeEnum, MagsAnalysis, MetagenomeAnnotation, MetagenomeAssembly, \
    MetatranscriptomeAnnotation, MetatranscriptomeAssembly, MetatranscriptomeExpressionAnalysis, NucleotideSequencing, \
    ReadBasedTaxonomyAnalysis, ReadQcAnalysis, WorkflowExecution
import nmdc_schema.nmdc as nmdc


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
    target_class = record["type"].split(":")[1]
    validation_report = linkml.validator.validate(record, nmdc_materialized, target_class)
    if validation_report.results:
        for result in validation_report.results:
            # TODO: remove this once the schema is fixed
            # ignore the members_id error for MagsAnalysis
            if result.instantiates == 'MagsAnalysis' and "members_id" in result.message:
                pass
            else:
                raise ValueError(f"Validation error: {result.message}")



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
    empty_values = [None, "", [], "null",]
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
        # _id is a MongoDB field that makes the parent class fail to initialize
        record.pop("_id", None)
        if "type" not in record:
            record["type"] = "nmdc:DataObject"
        validation_report = linkml.validator.validate(record, nmdc_materialized, "DataObject")
        if validation_report.results:
            for result in validation_report.results:
                raise ValueError(f"Validation error: {result.message}")
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
