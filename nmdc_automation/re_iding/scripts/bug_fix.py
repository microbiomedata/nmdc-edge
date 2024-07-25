#!/usr/bin/env python3
""" bug_fix.py - a Click script with commands to fix bugs in data path names and file names. """

import click
import csv
import json
import logging
from pathlib import Path
import requests
import time

from nmdc_automation.re_iding.file_utils import assembly_file_operations


PROD_DATAFILE_DIR = Path("/global/cfs/cdirs/m3408/results")
LOCAL_DATAFILE_DIR = Path.home().joinpath("Documents/data/results")
REPO_DATA_DIR = Path(__file__).parent.absolute().joinpath("data")
BUG_FIX_DATA_DIR = REPO_DATA_DIR.joinpath("bug_fix")

# Set up logging
logger = logging.getLogger(__name__)

@click.group()
def cli():
    pass

@cli.command()
@click.option('--expected-paths-file', type=click.Path(exists=True), required=False,
              default=BUG_FIX_DATA_DIR.joinpath("213_malformed_assembly_paths", "expected_paths.txt"))
@click.option("--production", is_flag=True, default=False,
              help="Use the Production data file directory, default is a local data file directory.")
@click.option("--update-files", is_flag=True, default=False, help="Update the files with the fixed paths.")
@click.option("--debug", is_flag=True, help="Enable debug logging.")
def fix_malformed_assembly_paths(expected_paths_file, production, update_files, debug):
    """ Fix malformed assembly paths to match the expected path. """
    start_time = time.time()
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if production:
        datafile_dir = PROD_DATAFILE_DIR
    else:
        datafile_dir = LOCAL_DATAFILE_DIR

    api_url = "https://api.microbiomedata.org/data_objects"
    data_object_changesheet = "data_object_changesheet.tsv"
    changesheet_header = "id\taction\tattribute\tvalue"
    data_object_changes = set()

    logger.info(f"Expected paths file: {expected_paths_file}")
    logger.info(f"Production: {production}")
    logger.info(f"Update files: {update_files}")

    # Read the expected paths file
    with open(expected_paths_file) as f:

        num_processed = 0
        for line in f:
            # Parse out the components of the path
            line = line.strip()
            logger.debug(f"line: {line}")
            _data_dir, omics_dirname, exp_assembly_id, exp_filename = line.rsplit("/", maxsplit=3)
            logger.debug(f"omics_type: {omics_dirname}, assembly: {exp_assembly_id}, file_name: {exp_filename}")

            # Find the omics data dir
            omics_data_dir = datafile_dir.joinpath(omics_dirname)
            if not omics_data_dir.exists():
                if production:
                    logger.error(f"Omics data directory does not exist: {omics_data_dir}")
                    continue
                # Skip silently if using local data directory
                continue

            # Search for the malformed assembly directory
            assembly_id = None
            for dir in omics_data_dir.iterdir():
                if exp_assembly_id in dir.name:
                    assembly_id = dir.name
                    working_dir = omics_data_dir.joinpath(assembly_id)
                    break
            if assembly_id is None:
                logger.error(f"Assembly directory not found: {exp_assembly_id}")
                continue
            logger.info(f"Found assembly directory: {assembly_id}")

            # Rename the assembly directory to the expected name if it does not match and update_files is True
            if assembly_id != exp_assembly_id:
                new_assembly_dir = omics_data_dir.joinpath(exp_assembly_id)
                if update_files:
                    working_dir = working_dir.rename(new_assembly_dir)
                    logger.info(f"Renamed assembly directory: {working_dir}")
                else:
                    logger.info(f"Would rename assembly directory: {assembly_id} to {exp_assembly_id}")

            # Data Files
            # Parse the expected data file name
            _nmdc, exp_datafile_assembly_id, exp_datafile_type = exp_filename.split("_", maxsplit=2)
            # Search for the malformed data file(s) - check all files as the expected_paths_file is not comprehensive
            datafiles = list(working_dir.glob(f"*{exp_datafile_assembly_id}*"))
            if len(datafiles) == 0:
                logger.error(f"Data files not found for: {exp_datafile_assembly_id}")
                continue
            logger.info(f"Found {len(datafiles)} data files for: {exp_datafile_assembly_id}")
            for datafile in datafiles:
                logger.info(f"Examining: {datafile}")
                # Parse the data file name
                _nmdc, datafile_assembly_id, datafile_type = datafile.name.split("_", maxsplit=2)

                # exact match - no need to rename
                if datafile_assembly_id == exp_datafile_assembly_id and datafile_type == exp_datafile_type:
                    logger.info(f"Data file name matches expected: {datafile.name}")
                    continue
                # datafile names match - assume no need to rename
                if datafile_assembly_id == exp_datafile_assembly_id:
                    logger.info(f"Data file name matches assembly id: {datafile.name}")
                    continue

                # datafile names do not match - rename
                old_workflow_id = assembly_id
                new_workflow_id = exp_assembly_id
                data_object_type = _infer_data_object_type_from_name(datafile.name)
                new_datafile_name = f"nmdc_{exp_datafile_assembly_id}_{datafile_type}"
                old_file_path = datafile
                new_file_path = working_dir.joinpath(new_datafile_name)
                num_processed += 1
                logger.info(f"Data file name does not match expected: {datafile.name}")
                logger.info(f"Data object type: {data_object_type}")
                logger.info(f"Old path: {old_file_path}")
                logger.info(f"New path: {new_file_path}")

                # Query the API to get the id of the data object - e.g.
                params = {
                    "filter": f"name:{new_datafile_name}",
                    "per_page": 25
                }

                response = requests.get(api_url, params=params)
                # show what we submitted
                logger.info(f"API request: {response.url}")
                if response.status_code != 200:
                    logger.error(f"API request failed: {response.status_code}")
                    continue
                    # api returns a 200 response even if no data object is found
                elif len(response.json()["results"]) == 0:
                    logger.error(f"No data object found for: {datafile.name}")
                    continue
                else:
                    logger.info(f"API request successful: {response.status_code}")

                data_object = response.json()["results"][0]
                logger.info(f"DataObject ID: {data_object['id']}")
                logger.info(f"DataObject Size: {data_object['file_size_bytes']}")
                logger.info(f"DataObject MD5: {data_object['md5_checksum']}")


                if update_files:
                    if not data_object_type:
                        logger.error(f"Do not know how to update with no data object type: {datafile.name}")
                        continue
                    logger.info(f"Processing: {data_object_type}: {old_file_path}")
                    logger.info(f"New path: {new_file_path}")
                    md5, size = assembly_file_operations(
                        old_workflow_id, new_workflow_id, data_object_type, old_file_path, new_file_path)
                    logger.info(f"MD5: {md5}, Size: {size}")
                    # Check size and md5
                    if size != data_object['file_size_bytes']:
                        logger.warning(f"Size mismatch: {size} != {data_object['file_size_bytes']}")
                        change = (data_object['id'], "update", "file_size_bytes", str(size))
                        data_object_changes.add(change)
                    if md5 != data_object['md5_checksum']:
                        logger.warning(f"MD5 mismatch: {md5} != {data_object['md5_checksum']}")
                        change = (data_object['id'], "update", "md5_checksum", md5)
                        data_object_changes.add(change)

                    # Remove the old file
                    old_file_path.unlink()

                else:
                    logger.info("--update-files not set.")
                    logger.info(f"Would update to {new_file_path}")

    logger.info(f"Processed {num_processed} files in {time.time() - start_time} seconds.")
    logger.info(f"Data Object Changes: {data_object_changes}")
    # Write the data object changes to a changesheet
    changesheet_file = REPO_DATA_DIR.joinpath(data_object_changesheet)
    with open(changesheet_file, "w") as f:
        f.write(changesheet_header + "\n")
        for change in data_object_changes:
            f.write("\t".join(change) + "\n")


@cli.command()
@click.option(
    "--input-file", type=click.Path(exists=True), required=False,
    default=BUG_FIX_DATA_DIR.joinpath("201_blade_mismatch", "asm_blade_not_in_mongo.txt")
    )
@click.option(
    "--production", is_flag=True, default=False,
    help="Use the Production data file directory. Default is a local data file directory."
    )
@click.option("--update-files", is_flag=True, default=False, help="Update the files with the fixed paths.")
def fix_blade_mismatch(input_file, production, update_files):
    """
    Fix blade mismatch in data paths. Only study nmdc:sty-11-547rwq94 (EMP500) is affected, and only
    metagenome_assembly_set records are affected.
    https://github.com/microbiomedata/nmdc_automation/issues/201
    """
    STUDY_ID = "nmdc:sty-11-547rwq94"
    start_time = time.time()

    # Paths to the data files from re-IDing
    updated_identifiers_file = REPO_DATA_DIR.joinpath(STUDY_ID, "nmdc:sty-11-547rwq94_updated_record_identifiers.tsv")
    legacy_records_file = REPO_DATA_DIR.joinpath(STUDY_ID, "nmdc:sty-11-547rwq94_associated_record_dump.json")

    # Create a dict of legacy_id: new_id for data_object_set entries in the updated_identifiers_file .tsv file
    data_object_id_map = {}
    with open(updated_identifiers_file) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if row["collection_name"] == "data_object_set":
                data_object_id_map[row["new_id"]] = row["legacy_id"]



    if production:
        datafile_dir = PROD_DATAFILE_DIR
    else:
        datafile_dir = LOCAL_DATAFILE_DIR

    logger.info(f"Input file: {input_file}")
    logger.info(f"Production: {production}")
    logger.info(f"Update files: {update_files}")



    with open(input_file) as f:
        for line in f:
            line = line.strip()
            # logger.info(f"line: {line}")

            # Parse out the components of the path from the input file
            _data_dir, omics_dirname, workflow_id, filename = line.rsplit("/", maxsplit=3)
            # remove does not exist or any other trailing text
            filename = filename.split(" ")[0]
            logger.info(f"omics_id: {omics_dirname}, workflow_id: {workflow_id}, filename: {filename}")

            # Get the metagenome_assembly_set record
            url = "https://api.microbiomedata.org/nmdcschema/metagenome_assembly_set"
            params = {
                "filter": f'{{"id": "{workflow_id}"}}',
                "max_page_size": 20
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            workflow_record = response.json()["resources"][0]

            data_object_ids = workflow_record.get("has_output", [])
            if not data_object_ids:
                logger.error(f"No data objects found for: {workflow_id}")
                continue
            logger.info(f"Found {len(data_object_ids)} data objects for: {workflow_id}")
            for do_id in data_object_ids:
                legacy_id = data_object_id_map.get(do_id)
                if not legacy_id:
                    logger.error(f"Legacy ID not found for: {do_id}")
                    continue
                logger.info(f"Legacy ID: {legacy_id}")






def _infer_data_object_type_from_name(name: str) -> str:
    # Infer the data type from the data file name and extension
    data_type = None
    if name.endswith("pairedMapped_sorted.bam"):
        data_type = "Assembly Coverage BAM"
    elif name.endswith("assembly.agp"):
        data_type = "Assembly AGP"
    elif name.endswith("_scaffolds.fna"):
        data_type = "Assembly Scaffolds"
    elif name.endswith("_contigs.fna"):
        data_type = "Assembly Contigs"
    elif name.endswith("mapping_stats.txt") or name.endswith("_covstats.txt"):
        data_type = "Assembly Coverage Stats"
    else:
        logger.error(f"Unknown data file type: {name}")
    return data_type





if __name__ == '__main__':
    cli()
