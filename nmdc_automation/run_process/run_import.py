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
from nmdc_schema.nmdc import Database


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    pass


@cli.command()
@click.argument("import_file", type=click.Path(exists=True))
@click.argument("import_yaml", type=click.Path(exists=True))
@click.argument("site_configuration", type=click.Path(exists=True))
@click.option("--iteration", default=1, type=str, help="Number of iterations")
def import_projects(import_file, import_yaml, site_configuration, iteration):

    logger.info(f"Importing project from {import_file}")

    runtime = NmdcRuntimeApi(site_configuration)
    nmdc_materialized = _get_nmdc_materialized()

    data_imports = _parse_tsv(import_file)
    for data_import in data_imports:
        project_path = data_import["project_path"]
        nucleotide_sequencing_id = data_import["nucleotide_sequencing_id"]
        files_list = [
            os.path.join(project_path, f)
            for f in os.listdir(os.path.abspath(project_path))
            if os.path.isfile(os.path.join(project_path, f))
        ]

        logger.info(f"Importing {nucleotide_sequencing_id} from {project_path}: {len(files_list)} files")
        mapper = GoldMapper(
            iteration,
            files_list,
            nucleotide_sequencing_id,
            import_yaml,
            project_path,
            runtime,
        )
        db = Database()
        data_generation_update = None

        # Nucleotide sequencing data
        logger.info(f"Checking for existing nucleotide_sequencing_id: {nucleotide_sequencing_id}")
        nucleotide_sequencing = runtime.find_planned_process(nucleotide_sequencing_id)
        if not nucleotide_sequencing:
            raise Exception(f"nucleotide_sequencing_id {nucleotide_sequencing_id} not found")

        if _nucleotide_sequencing_has_output(nucleotide_sequencing, nucleotide_sequencing_id):
            logger.info(f"nucleotide_sequencing_id {nucleotide_sequencing_id} already has output: {nucleotide_sequencing['has_output']}")
            continue

        logger.info(f"Mapping sequencing data for nucleotide_sequencing_id: {nucleotide_sequencing_id}")

        # Initialize the db with the sequencing data and create an update to be applied
        # to the sequencing data generation has_output list
        # logger.info("Mapping sequencing data")
        # db, data_generation_update = mapper.map_sequencing_data()
        # Map the rest of the data files - single files
        # logger.info("Mapping single data files")
        # db, do_mapping = mapper.map_data(db)
        # Map the rest of the data files - multiple files
        # logger.info("Mapping multiple data files")
        # db, do_mapping = mapper.map_data(db, unique=False)

        # map the workflow executions
        logger.info("Mapping workflow executions")
        # db = mapper.map_workflow_executions(db)

        # validate the database
        # logger.info("Validating imported data")
        # db_dict = yaml.safe_load(yaml_dumper.dumps(db))
        # del db # free up memory
        # del do_mapping # free up memory
        # validation_report = linkml.validator.validate(db_dict, nmdc_materialized)
        # if validation_report.results:
        #     logger.error(f"Validation Failed")
        #     for result in validation_report.results:
        #         logger.error(result.message)
        #     raise Exception("Validation Failed")
        # else:
        #     logger.info("Validation Passed")

        # apply the update to the sequencing data generation has_output list
        # logger.info("Applying update to sequencing data generation")
        # try:
        #     runtime.run_query(data_generation_update)
        # except Exception as e:
        #     logger.error(f"Error applying update to sequencing data generation: {e}")
        #     logger.error(data_generation_update)
        #     raise e


        # Post the data to the API
        logger.info("Posting data to the API")
        # try:
        #     runtime.post_objects(db_dict)
        #     del db_dict # free up memory
        # except Exception as e:
        #     logger.error(f"Error posting data to the API: {e}")
        #     raise e
        #
        # gc.collect()


def _nucleotide_sequencing_has_output(nucleotide_sequencing, nucleotide_sequencing_id) -> bool:
    """
    Check if the nucleotide sequencing has an output and if it is an NMDC data object.
    """
    seq_has_output = nucleotide_sequencing.get("has_output", [])
    if seq_has_output:
        # Raise an exception if there is more than one output or if the output is not an NMDC data object
        if len(seq_has_output) > 1:
            raise Exception(f"nucleotide_sequencing_id {nucleotide_sequencing_id} has more than one output")
        seq_do_id = seq_has_output[0]
        if not seq_do_id.startswith("nmdc:dobj-"):
            raise Exception(f"nucleotide_sequencing_id {nucleotide_sequencing_id} has a non-NMDC output")

        logger.info(f"nucleotide_sequencing_id {nucleotide_sequencing_id} has output {seq_do_id}")
        return True
    else:
        logger.info(f"nucleotide_sequencing_id {nucleotide_sequencing_id} has no outputs")
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
