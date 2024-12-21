import click
import csv
import gc
import importlib.resources
from functools import lru_cache
import logging
import os
import linkml.validator
from linkml_runtime.dumpers import yaml_dumper
import yaml

from nmdc_automation.import_automation import GoldMapper
from nmdc_automation.api import NmdcRuntimeApi
from nmdc_automation.import_automation.import_mapper import ImportMapper
from nmdc_schema.nmdc import Database




@click.group()
def cli():
    pass


@cli.command()
@click.argument("import_file", type=click.Path(exists=True))
@click.argument("import_yaml", type=click.Path(exists=True))
@click.argument("site_configuration", type=click.Path(exists=True))
def import_projects(import_file, import_yaml, site_configuration):
    logging_level = os.getenv("NMDC_LOG_LEVEL", logging.DEBUG)
    logging.basicConfig(
        level=logging_level, format="%(asctime)s %(levelname)s: %(message)s"
    )
    logger = logging.getLogger(__name__)

    logger.info(f"Importing project from {import_file}")

    runtime = NmdcRuntimeApi(site_configuration)
    nmdc_materialized = _get_nmdc_materialized()

    data_imports = _parse_tsv(import_file)
    for data_import in data_imports:
        project_path = data_import["project_path"]
        nucleotide_sequencing_id = data_import["nucleotide_sequencing_id"]

        # Initialize the import mapper
        logger.info(f"Importing project {project_path} into {nucleotide_sequencing_id}")
        import_mapper = ImportMapper(nucleotide_sequencing_id, project_path, import_yaml)
        logger.info(f"Project has {len(import_mapper._import_files)} files")
        file_mappings = import_mapper.file_mappings     # This will create and cache the file mappings
        logger.info(f"Mapped: {len(file_mappings)} files")

        for fm in file_mappings:
            logger.debug(f"Mapping: {fm}")




def _get_nucleotide_sequencing(runtime, nucleotide_sequencing_id):
    """ Get the nucleotide sequencing process from the runtime API. """
    procs = runtime.find_planned_processes(filter_by={"id": nucleotide_sequencing_id})
    if not procs:
        raise Exception(f"nucleotide_sequencing_id {nucleotide_sequencing_id} not found")
    elif len(procs) > 1:  # This should never happen
        raise Exception(f"nucleotide_sequencing_id {nucleotide_sequencing_id} has multiple processes")
    nucleotide_sequencing = procs[0]
    return nucleotide_sequencing


def _nucleotide_sequencing_has_output(nucleotide_sequencing) -> bool:
    """
    Check if the nucleotide sequencing has an output and if it is an NMDC data object.
    """
    seq_has_output = nucleotide_sequencing.get("has_output", [])
    if seq_has_output:
        # Raise an exception if there is more than one output or if the output is not an NMDC data object
        if len(seq_has_output) > 1:
            raise Exception(f"nucleotide_sequencing_id {nucleotide_sequencing['id']} has more than one output")
        seq_do_id = seq_has_output[0]
        if not seq_do_id.startswith("nmdc:dobj-"):
            raise Exception(f"nucleotide_sequencing_id {nucleotide_sequencing['id']} has a non-NMDC output")

        logger.info(f"nucleotide_sequencing_id {nucleotide_sequencing['id']} has output {seq_do_id}")
        return True
    else:
        logger.info(f"nucleotide_sequencing_id {nucleotide_sequencing['id']} has no outputs")
        return False


@lru_cache(maxsize=None)
def _get_nmdc_materialized():
    with importlib.resources.open_text("nmdc_schema", "nmdc_materialized_patterns.yaml") as f:
        return yaml.safe_load(f)

def _parse_tsv(file):
    with open(file) as f:
        reader = csv.DictReader(f, delimiter="\t")
        data = [row for row in reader]

    return data


if __name__ == "__main__":
    cli()
