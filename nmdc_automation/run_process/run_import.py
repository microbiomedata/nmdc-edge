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
    """
    Import external metagenome sequencing projects into the NMDC database.

    Arguments:

    - import_file: 'nucleotide_sequencing_id' 'project_id' 'project_path' .tsv file

    - import_yaml: YAML file with import specifications

    - site_configuration: YAML file with site configuration

    Options:

    - update_db: Update the database if True, otherwise print the update json

    The import process:

        1. Parse the import file and import specifications

        2. Initialize the ImportMapper

            - Add DataGeneration and its output data object from the DB
            - Add Workflow Executions and their data objects from the DB
            - Scan files in the Import Directory and add or update mappings

        3. Iterate through the mappings and assign NMDC IDs for data objects and workflow executions if they don't already exist in the DB

        4. Iterate through the mappings by Workflow Execution Type and make DataObject and Workflow Execution records

        5. Validate using the API

        6. If validation passes, update the database if the --update-db flag is set

        - Otherwise, print the update json and update query if there are any
    """
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
        file_mappings = import_mapper.mappings  # This will create and cache the file mappings
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
        for fm in import_mapper.mappings:
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
        for process_type, mappings in import_mapper.mappings_by_workflow_type.items():

            import_spec = import_mapper.import_specs_by_workflow_type.get(process_type) # Sequencing is a special case
            if import_spec and not import_spec['Import']:
                logger.info(f"Skipping {process_type} - Import set to False")
                continue

            process_ids = {mapping.nmdc_process_id for mapping in mappings}
            if len(process_ids) != 1:
                raise ValueError(f"Cannot determine nmdc_process_id for {process_type}: {process_ids}")
            nmdc_process_id = process_ids.pop()
            process_id_in_dbs = {mapping.process_id_in_db for mapping in mappings}
            if len(process_id_in_dbs) != 1:
                raise ValueError(f"Cannot determine process_id_in_db for {process_type}: {process_id_in_dbs}")
            process_id_in_db = process_id_in_dbs.pop()


            nmdc_data_directory = os.path.join(import_mapper.root_directory, nmdc_process_id)
            try:
                os.makedirs(nmdc_data_directory)
            except FileExistsError:
                logger.debug(f"Directory {nmdc_data_directory} already exists")

            # Link data files and create Data Objects if they don't already exist
            for mapping in mappings:
                if mapping.data_object_in_db:
                    logger.info(f"Data Object: {mapping.data_object_id} / {mapping.data_object_type} already exists in DB - skipping")
                    continue

                logger.info(f"Linking: {mapping}")

                nmdc_data_file_name = import_mapper.get_nmdc_data_file_name(mapping)
                export_file = os.path.join(nmdc_data_directory, nmdc_data_file_name)
                import_file = os.path.join(import_mapper.import_project_dir, mapping.import_file)
                logger.info(f"Linking data file to {export_file}")
                if mapping.is_multiple:
                    if not os.path.exists(export_file):
                        with ZipFile(export_file, 'w') as zipf:
                            zipf.write(import_file, arcname=os.path.basename(import_file))
                    else:
                        with ZipFile(export_file, 'a') as zipf:
                            # Check if the file is already in the zip
                            if os.path.basename(import_file) in zipf.namelist():
                                logger.debug(f"File {import_file} already in zip")
                            else:
                                zipf.write(import_file, arcname=os.path.basename(import_file))
                else:
                    try:
                        os.link(import_file, export_file)
                    except FileExistsError:
                        logger.debug(f"File {export_file} already exists")

                import_spec = import_mapper.import_specs_by_data_object_type[mapping.data_object_type]
                filemeta = os.stat(export_file)
                md5 = get_or_create_md5(export_file)
                description = import_spec['description'].replace("{id}", nucleotide_sequencing_id)
                do_record = {
                    'id': mapping.data_object_id,
                    'type': 'nmdc:DataObject',
                    "name": nmdc_data_file_name,
                    "file_size_bytes": filemeta.st_size,
                    "md5_checksum": md5,
                    "data_object_type": mapping.data_object_type,
                    "was_generated_by": mapping.nmdc_process_id,
                    "url": f"{import_mapper.data_source_url}/{import_mapper.data_generation_id}/{export_file}",
                    "description": description
                }
                # Add to the import_db if it doesn't already exist
                existing_do_ids = {do['id'] for do in import_db['data_object_set']}
                if do_record['id'] in existing_do_ids:
                    continue
                else:
                    import_db['data_object_set'].append(do_record)

            # Create Workflow Execution Record if it doesn't already exist
            # Nucleotide Sequencing is a special case:
            #  - No Workflow record is  created
            #  - If the data object is not already in the DB, create an update query

            if process_type == 'nmdc:NucleotideSequencing':
                if len(mappings) != 1:
                    raise ValueError(f"Expected 1 mapping for NucleotideSequencing, got {len(mappings)}")
                mapping = mappings[0]
                if not mapping.data_object_in_db:
                    logger.info(f"Adding update query for {nucleotide_sequencing_id}")
                    update = {
                        "q": {
                            "id": nucleotide_sequencing_id
                        },
                        "u": {
                            "$set": {
                                "has_output": [mapping.data_object_id]
                            }
                        }
                    }
                    data_generation_update_query['updates'].append(update)
                continue
            elif process_id_in_db:
                logger.info(f"Workflow Execution {nmdc_process_id} already exists in DB - skipping")
                continue
            has_input, has_output = import_mapper.get_has_input_has_output_for_workflow_type(process_type)

            wfe_record = {
                'id': nmdc_process_id,
                "name": import_spec["Workflow_Execution"]["name"].replace("{id}", nmdc_process_id),
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
        db_update_json = json.dumps(import_db, indent=4)
        logger.info(
            f"Validating {len(import_db['data_object_set'])} data objects and {len(import_db['workflow_execution_set'])} workflow executions"
            )
        val_result = runtime_api.validate_metadata(import_db)

        # If validation passes, update the database if the --update-db flag is set
        # Otherwise, print the update json and update query if there are any
        if val_result['result'] == "All Okay!":
            logger.info(f"Validation passed")
            if update_db:
                # check if there are any workflow executions or data objects to add
                if import_db['data_object_set'] or import_db['workflow_execution_set']:
                    logger.info(f"Updating Database")
                    resp = runtime_api.post_workflow_executions(import_db)
                    logger.info(f"workflows/workflow_executions response: {resp}")
                else:
                    logger.info(f"No new data objects or workflow executions to add")

                logger.info(f"Applying update queries")
                if data_generation_update_query['updates']:
                    resp = runtime_api.run_query(data_generation_update_query)
                    logger.info(f"queries:run response: {resp}")
                else:
                    logger.info(f"No updates to apply")
            else:
                logger.info(f"Option --update-db not selected. No changes made")
                if import_db['data_object_set'] or import_db['workflow_execution_set']:
                    logger.info(f"Update json:")
                    print(db_update_json)
                else:
                    logger.info(f"No new data objects or workflow executions to add")

                if data_generation_update_query['updates']:
                    logger.info(f"Update query:")
                    print(json.dumps(data_generation_update_query, indent=4))
                else:
                    logger.info(f"No updates to apply")
        else:
            logger.info(f"Validation failed")
            logger.info(f"Validation result: {val_result}")
            print(db_update_json)


        logger.info("Updating minted IDs")
        import_mapper.write_minted_id_file()
        for fm in import_mapper.mappings:
            logger.debug(f"Mapped: {fm}")


def _database_workflow_execution_ids_by_type(import_mapper, runtime_api) -> dict:
    """Return the unique workflow execution IDs by workflow type."""
    wfe_ids_by_type = {}
    for wfe_type in import_mapper.workflow_execution_types:
        filt = {"was_informed_by": import_mapper.data_generation_id, "type": wfe_type}
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
