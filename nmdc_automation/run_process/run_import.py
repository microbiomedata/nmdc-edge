import click
import csv
import datetime
import pytz
import json
import logging
import os
from zipfile import ZipFile


from nmdc_automation.api import NmdcRuntimeApi
from nmdc_automation.import_automation.import_mapper import ImportMapper
from nmdc_automation.import_automation.utils import get_or_create_md5


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
@click.option("--update-db", is_flag=True)
@click.pass_context
def import_projects(ctx,  import_file, import_yaml, site_configuration, update_db):
    log_level = int(ctx.obj['log_level'])
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s')
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)

    logger.info(f"Importing project from {import_file}")
    logger.info(f"Import Specifications:  from {import_yaml}")
    logger.info(f"Site Configuration:  from {site_configuration}")

    runtime_api = NmdcRuntimeApi(site_configuration)


    data_imports = _parse_tsv(import_file)
    for data_import in data_imports:
        project_path = data_import["project_path"]
        nucleotide_sequencing_id = data_import["nucleotide_sequencing_id"]

        # Initialize the import mapper
        # 1. Add DataGeneration and it's output data object
        # 2. Add Workflow Executions and their data objects
        # 3. Scan files in the Import Directory and add or update mappings
        logger.info(f"Importing project {project_path} into {nucleotide_sequencing_id}")
        import_mapper = ImportMapper(nucleotide_sequencing_id, project_path, import_yaml, runtime_api)
        import_mapper.add_do_mappings_from_data_generation()
        import_mapper.add_do_mappings_from_workflow_executions()
        import_mapper.update_do_mappings_from_import_files()
        logger.info(f"Project has {len(import_mapper._import_files)} files")
        file_mappings = import_mapper.file_mappings  # This will create and cache the file mappings
        logger.info(f"Mapped: {len(file_mappings)} files")

        # init a db to hold workflow executions and their data objects, one per Data Generation
        import_db = {
            'data_object_set': [],
            'workflow_execution_set': []
        }
        data_generation_update_query = {
            "update": "data_generation_set",
            "updates": []
        }

        # Make root directory for import
        try:
            os.makedirs(import_mapper.root_directory)
        except FileExistsError:
            logger.debug(f"Directory {import_mapper.root_directory} already exists")


        # Iterate through all mappings, assigning NMDC IDs for
        # data objects and workflow executions if they don't already exist in the DB
        for fm in import_mapper.file_mappings:
            if fm.data_object_in_db:
                logger.info(f"Data Object: {fm.data_object_id} / {fm.data_object_type} already exists in DB - skipping")
                continue
            data_object_id = import_mapper.get_or_create_minted_id(
                "nmdc:DataObject", data_object_type=fm.data_object_type
            )
            if not data_object_id:
                logger.error(f"Cannot determine data_object_id for {fm.data_object_type}")
                continue
            fm.data_object_id = data_object_id

            if fm.process_id_in_db:
                logger.info(f"Process {fm.nmdc_process_id} already exists in DB - skipping")
                continue
            nmdc_process_id = import_mapper.get_or_create_minted_id(
                fm.output_of
            )
            if not nmdc_process_id:
                logger.error(f"Cannot determine nmdc_process_id for {fm.output_of}")
                continue
            fm.nmdc_process_id = nmdc_process_id


        # Iterate through the mappings by Workflow Execution Type and
        # 1. Make the NMDC data directory based on workflow execution ID if it does not exist
        # 2. Link the data file and determine file size and MD5 hash
        # 3. Make DataObject record
        # 4. Make Workflow Execution record
        for process_type, mappings in import_mapper.file_mappings_by_workflow_type.items():
            process_ids = [mapping.nmdc_process_id for mapping in mappings]
            if len(process_ids) != 1:
                raise ValueError(f"Cannot determine nmdc_process_id for {process_type}")
            nmdc_process_id = process_ids[0]

            nmdc_data_directory = os.path.join(import_mapper.root_directory, nmdc_process_id)
            try:
                os.makedirs(nmdc_data_directory)
            except FileExistsError:
                logger.debug(f"Directory {nmdc_data_directory} already exists")








            # # Link data files and create Data Objects
            # logger.info(f"Found {len(mappings)} file mappings to import for {wfe_id}")
            # for mapping in mappings:
            #     logger.debug(f"Importing {mapping}")
            #
            #     # link files
            #     nmdc_data_file_name = import_mapper.get_nmdc_data_file_name(mapping)
            #     export_file = os.path.join(nmdc_wfe_dir, nmdc_data_file_name)
            #     import_file = os.path.join(import_mapper.import_project_dir, mapping.import_file)
            #     # single data files get linked
            #     if not mapping.is_multiple:
            #         try:
            #             os.link(import_file, export_file)
            #         except FileExistsError:
            #             logger.debug(f"File {export_file} already exists")
            #     else:
            #         if not os.path.exists(export_file):
            #             with ZipFile(export_file, 'w') as zip:
            #                 zip.write(import_file)
            #         else:
            #             with ZipFile(export_file, 'a') as zip:
            #                 zip.write(import_file)
            #
            #     # Check if the Data Object already exists in the DB
            #
            #     # make a DataObject
            #     filemeta = os.stat(export_file)
            #     md5 = get_or_create_md5(export_file)
            #     description = import_spec_by_do_type[mapping.data_object_type]['description'].replace(
            #         "{id}", nucleotide_sequencing_id
            #     )
            #
            #     do_record = {
            #         'id': mapping.data_object_id,
            #         'type': 'nmdc:DataObject',
            #         "name": nmdc_data_file_name,
            #         "file_size_bytes": filemeta.st_size,
            #         "md5_checksum": md5,
            #         "data_object_type": mapping.data_object_type,
            #         "was_generated_by": mapping.nmdc_process_id,
            #         "url": f"{import_mapper.data_source_url}/{import_mapper.nucleotide_sequencing_id}/"
            #                f"{export_file}",
            #         "description": description
            #     }
            #     logging.debug(f"Data Object: {do_record}")
            #
            #     existing_do_ids = [do['id'] for do in import_db['data_object_set']]
            #     if do_record['id'] in existing_do_ids:
            #         continue
            #     else:
            #         import_db['data_object_set'].append(do_record)
            #
            # # Create Workflow Execution Record - we do not do this for sequencing
            # if wfe_type == 'nmdc:NucleotideSequencing':
            #     continue
            # has_input, has_output = import_mapper.get_has_input_has_output_for_workflow_type(wfe_type)
            # logger.info(f"{wfe_type} has {len(has_input)} inputs and {len(has_output)} outputs")
            # import_spec = import_spec_by_wfe_type[wfe_type]
            # wfe_record = {
            #     'id': wfe_id,
            #     "name": import_spec["Workflow_Execution"]["name"].replace("{id}", wfe_id),
            #     "type": import_spec["Type"],
            #     "has_input": has_input,
            #     "has_output": has_output,
            #     "git_url": import_spec["Git_repo"],
            #     "version": import_spec["Version"],
            #     "execution_resource": import_mapper.import_specifications["Workflow Metadata"]["Execution Resource"],
            #     "started_at_time": datetime.datetime.now(pytz.utc).isoformat(),
            #     "ended_at_time": datetime.datetime.now(pytz.utc).isoformat(),
            #     "was_informed_by": nucleotide_sequencing_id,
            # }
            # import_db['workflow_execution_set'].append(wfe_record)

        # Validate using the api
        db_update_json = json.dumps(import_db, indent=4)
        logger.info(
            f"Validating {len(import_db['data_object_set'])} data objects and {len(import_db['workflow_execution_set'])} workflow executions"
            )
        val_result = runtime_api.validate_metadata(import_db)

        if val_result['result'] == "All Okay!":
            logger.info(f"Validation passed")
            if update_db:
                logger.info(f"Updating Database")
                resp = runtime_api.post_objects(import_db)
                logger.info(f"workflows/workflow_executions response: {resp}")

                logger.info(f"Applying update queries")
                resp = runtime_api.run_query(data_generation_update_query)
                logger.info(f"queries:run response: {resp}")
            else:
                logger.info(f"Option --update-db not selected. No changes made")
                print(db_update_json)

                print(json.dumps(data_generation_update_query, indent=4))
        else:
            logger.info(f"Validation failed")
            logger.info(f"Validation result: {val_result}")
            print(db_update_json)


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


def _parse_tsv(file):
    with open(file) as f:
        reader = csv.DictReader(f, delimiter="\t")
        data = [row for row in reader]

    return data


if __name__ == "__main__":

    cli()
