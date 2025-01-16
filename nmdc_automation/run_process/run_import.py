import click
import csv
import datetime
import pytz
import gc
import importlib.resources
from functools import lru_cache
import json
import logging
import os
import linkml.validator
from linkml_runtime.dumpers import yaml_dumper
import yaml

from nmdc_automation.api import NmdcRuntimeApi
from nmdc_automation.import_automation.import_mapper import ImportMapper
from nmdc_automation.import_automation.utils import get_or_create_md5
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
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s')
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)

    logger.info(f"Importing project from {import_file}")
    logger.info(f"Import Specifications:  from {import_yaml}")
    logger.info(f"Site Configuration:  from {site_configuration}")

    runtime_api = NmdcRuntimeApi(site_configuration)
    nmdc_materialized = _get_nmdc_materialized()


    data_imports = _parse_tsv(import_file)
    for data_import in data_imports:
        project_path = data_import["project_path"]
        nucleotide_sequencing_id = data_import["nucleotide_sequencing_id"]

        # Initialize the import mapper
        logger.info(f"Importing project {project_path} into {nucleotide_sequencing_id}")
        import_mapper = ImportMapper(nucleotide_sequencing_id, project_path, import_yaml, runtime_api)
        logger.info(f"Project has {len(import_mapper._import_files)} files")
        file_mappings = import_mapper.file_mappings  # This will create and cache the file mappings
        logger.info(f"Mapped: {len(file_mappings)} files")

        # init a db to hold workflow executions and their data objects, one per Data Generation
        import_db = {
            'data_object_set': [],
            'workflow_execution_set': []
        }


        # Data Generation Object
        # Retrieve it from the Database. Check that there is only 1
        logger.info(f"Searching for {nucleotide_sequencing_id} in the database")
        dg_results = runtime_api.find_planned_processes({"id":nucleotide_sequencing_id})
        if not dg_results:
            logger.error(f"Could not find {nucleotide_sequencing_id} in the database - skipping")
            continue
        data_generation = dg_results[0]
        logger.info(f"Found {nucleotide_sequencing_id} in the database - checking output")



        # Map Sequencing Output - check for NMDC data object in Data Generation has_output
        # Mint a new Data Object and Update Data Generation if has_output is empty or has a non-NMDC ID
        dg_output = data_generation.get('has_output', [])
        # We don't know how to handle this case yet
        if len(dg_output) > 1:
            logging.error(f"Multiple outputs for {nucleotide_sequencing_id} in the database - skipping")
            continue
        # No output
        if len(dg_output) == 0:
            logger.info(f"{nucleotide_sequencing_id} has no output")
            logger.info(f"Importing sequencing data and creating update for {nucleotide_sequencing_id}")
            # mint a new data object ID if needed
            seq_data_obj_id = import_mapper.get_or_create_minted_id('nmdc:DataObject', 'Metagenome Raw Reads')
            import_mapper.update_file_mappings(import_mapper.METAGENOME_RAW_READS, seq_data_obj_id, nucleotide_sequencing_id)

        # Already has nmdc output
        elif dg_output and dg_output[0].startswith('nmdc:dobj'):
            logger.info(f"{nucleotide_sequencing_id} has output: {dg_output[0]} - skipping sequencing data import")
            pass
        else: # shouldn't really happen
            logger.error(f"{nucleotide_sequencing_id} has non-NMDC output: {dg_output[0]}")
            continue


        # Go though file and update data object and workflow executions IDs
        for fm in import_mapper.file_mappings:
            data_object_id = import_mapper.get_or_create_minted_id(
                'nmdc:DataObject', fm.data_object_type
            )
            if not data_object_id:
                logger.error(f"Cannot determine an ID for {fm.data_object_type}")
                continue

            if fm.data_object_type == 'Metagenome Raw Reads':
                workflow_execution_id = nucleotide_sequencing_id
            else:
                workflow_execution_id = import_mapper.get_or_create_minted_id(
                    fm.output_of
                )
            if not workflow_execution_id:
                logger.error(f"Cannot determine an ID for {fm.output_of}")
                continue

            import_mapper.update_file_mappings(
                fm.data_object_type, data_object_id, workflow_execution_id
            )

        # Check the Database for any workflow executions that may already exist
        logger.info(f"Checking for workflow executions informed by {nucleotide_sequencing_id}")
        file_mappings_by_wfe_type = import_mapper.file_mappings_by_workflow_type


        db_wfe_ids_by_wfe_type = _database_workflow_execution_ids_by_type(
            import_mapper, runtime_api
        )
        logger.info(f"Found {len(file_mappings_by_wfe_type)} workflow executions in Database")

        # Make root directory for import
        try:
            os.makedirs(import_mapper.root_directory)
        except FileExistsError:
            logger.debug(f"Directory {import_mapper.root_directory} already exists")


        import_spec_by_wfe_type = import_mapper.import_specs_by_workflow_type
        for wfe_type, db_wfe_ids in db_wfe_ids_by_wfe_type.items():
            if len(db_wfe_ids) != 0:
                logger.warning(f"Found {len(db_wfe_ids)} workflow executions for {wfe_type} in database - skipping")
                continue

            logger.info(f"Importing data objects and workflow execution for {wfe_type}")
            import_spec_by_do_type = import_mapper.import_specs_by_data_object_type

            # Get the workflow ID for these mappings (there can be only 1) and use it to make the output dir
            mappings = file_mappings_by_wfe_type.get(wfe_type, [])
            wfe_ids = {mapping.workflow_execution_id for mapping in mappings}
            if len(wfe_ids) != 1:
                raise Exception(f"Found multiple workflow execution IDs for {wfe_type}")
            wfe_id = wfe_ids.pop()

            nmdc_wfe_dir = os.path.join(import_mapper.root_directory, wfe_id)
            try:
                os.makedirs(nmdc_wfe_dir)
            except FileExistsError:
                logger.info(f"Directory {nmdc_wfe_dir} already exists")


            # Link data files and create Data Objects
            logger.info(f"Found {len(mappings)} file mappings to import for {wfe_id}")
            for mapping in mappings:
                logger.info(f"Importing {mapping}")

                # link files
                nmdc_data_file_name = import_mapper.get_nmdc_data_file_name(mapping)
                export_file = os.path.join(nmdc_wfe_dir, nmdc_data_file_name)
                import_file = os.path.join(import_mapper.import_project_dir, mapping.file)
                try:
                    os.link(import_file, export_file)
                except FileExistsError:
                    logger.info(f"File {export_file} already exists")

                # make a DataObject
                filemeta = os.stat(export_file)
                md5 = get_or_create_md5(export_file)
                description = import_spec_by_do_type[mapping.data_object_type]['description'].replace(
                    "{id}", nucleotide_sequencing_id
                )

                do_record = {
                    'id': mapping.data_object_id,
                    'type': 'nmdc:DataObject',
                    "name": nmdc_data_file_name,
                    "file_size_bytes": filemeta.st_size,
                    "md5_checksum": md5,
                    "data_object_type": mapping.data_object_type,
                    "was_generated_by": mapping.workflow_execution_id,
                    "url": f"{import_mapper.data_source_url}/{import_mapper.nucleotide_sequencing_id}/"
                           f"{export_file}",
                    "description": description
                }
                logging.info(do_record)
                import_db['data_object_set'].append(do_record)

            # Create Workflow Execution Record - we do not do this for sequencing
            if wfe_type == 'nmdc:NucleotideSequencing':
                continue
            has_input, has_output = import_mapper.get_has_input_has_output_for_workflow_type(wfe_type)
            logger.info(f"{wfe_type} has {len(has_input)} inputs and {len(has_output)} outputs")
            import_spec = import_spec_by_wfe_type[wfe_type]
            wfe_record = {
                'id': wfe_id,
                "name": import_spec["Workflow_Execution"]["name"].replace("{id}", wfe_id),
                "type": import_spec["Type"],
                "has_input": has_input,
                "has_output": has_output,
                "git_url": import_spec["Git_repo"],
                "version": import_spec["Version"],
                "execution_resource": import_mapper.import_specifications["Workflow Metadata"]["Execution Resource"],
                "started_at_time": datetime.datetime.now(pytz.utc).isoformat(),
                "ended_at_time": datetime.datetime.now(pytz.utc).isoformat(),
                "was_informed_by": nucleotide_sequencing_id,
            }
            import_db['workflow_execution_set'].append(wfe_record)

        # Validate using the api
        db_update_json = json.dumps(import_db)
        logger.info(
            f"Validating {len(import_db['data_object_set'])} data objects and {len(import_db['workflow_execution_set'])} workflow executions"
            )
        val_result = runtime_api.validate_metadata(import_db)
        logger.info(f"Validation result: {val_result}")






        logger.info("Updating minted IDs")
        import_mapper.write_minted_id_file()
        for fm in import_mapper.file_mappings:
            logger.debug(f"Mapped: {fm}")


def _database_workflow_execution_ids_by_type(import_mapper, runtime_api) -> dict:
    """Return the unique workflow execution IDs by workflow type."""
    wfe_ids_by_type = {}
    for wfe_type in import_mapper.workflow_execution_types:
        filt = {"was_informed_by": import_mapper.nucleotide_sequencing_id, "type": wfe_type}
        workflow_executions = runtime_api.find_planned_processes(filt)
        wfe_ids_by_type[wfe_type] = [wfe['id'] for wfe in workflow_executions]
    return wfe_ids_by_type


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
