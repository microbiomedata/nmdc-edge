import click
import csv
import gc
import importlib.resources
from functools import lru_cache
import json
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
@click.pass_context
def cli(ctx: click.Context) -> None:
    log_level_name = os.getenv('NMDC_LOG_LEVEL', 'INFO')
    # convert to numeric log level
    log_level = logging.getLevelName(log_level_name)
    ctx.ensure_object(dict)
    ctx.obj['log_level'] = log_level


@cli.command()
@click.argument("import_file", type=click.Path(exists=True))
@click.argument("import_yaml", type=click.Path(exists=True))
@click.argument("site_configuration", type=click.Path(exists=True))
@click.pass_context
def import_projects(ctx,  import_file, import_yaml, site_configuration):
    log_level = int(ctx.obj['log_level'])
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=log_level )
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)

    logger.info(f"Importing project from {import_file}")
    logger.debug(f"Importing project from {import_yaml}")

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
        file_mappings = import_mapper.file_mappings  # This will create and cache the file mappings
        logger.info(f"Mapped: {len(file_mappings)} files")



        # Data Generation Object
        # Retrieve it from the Database. Check that there is only 1
        logger.info(f"Searching for {nucleotide_sequencing_id} in the database")
        dg_objs = runtime.find_planned_processes(filter_by={'id': nucleotide_sequencing_id})
        if len(dg_objs) == 0:
            logger.error(f"Could not find {nucleotide_sequencing_id} in the database - skipping")
            continue
        elif len(dg_objs) > 1:
            logger.error(f"Found multiple {nucleotide_sequencing_id} in the database - skipping")
            continue
        dg = dg_objs[0]
        logger.info(f"Found {nucleotide_sequencing_id} in the database - checking output")

        # init a db to hold workflow executions and their data objects, one per Data Generation
        db = Database()
        has_output_update = {}

        # Sequencing Output - check for NMDC data object in Data Generation has_output
        # Mint a new Data Object and Update Data Generation if has_output is empty or has a non-NMDC ID
        dg_output = dg.get('has_output', [])
        if len(dg_output) > 1: # We don't know how to handle this case yet
            logging.error(f"Multiple outputs for {nucleotide_sequencing_id} in the database - skipping")
            continue

        if len(dg_output) == 0:
            logger.info(f"{nucleotide_sequencing_id} has no output")
            logger.info(f"Importing sequencing data and creating update for {nucleotide_sequencing_id}")
            import_mapper.update_file_mappings(import_mapper.METAGENOME_RAW_READS, nucleotide_sequencing_id)

        elif dg_output and dg_output[0].startswith('nmdc:dobj'):
            logger.info(f"{nucleotide_sequencing_id} has output: {dg_output[0]} - skipping sequencing data import")
            pass
        else: # shouldn't really happen
            logger.info(f"{nucleotide_sequencing_id} has non-NMDC output: {dg_output[0]}")
            logger.info(f"Importing sequencing data and creating update for {dg_output[0]}")
            import_mapper.update_file_mappings(import_mapper.METAGENOME_RAW_READS, nucleotide_sequencing_id)



        for fm in file_mappings:
            logger.info(f"Mapping: {fm}")





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
