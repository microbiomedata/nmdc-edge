#!/usr/bin/env python3
""" bug_fix.py - a Click script with commands to fix bugs in data path names and file names. """

import click
import logging
from pathlib import Path
import time

from nmdc_automation.re_iding.file_utils import assembly_file_operations

PROD_DATAFILE_DIR = Path("/global/cfs/cdirs/m3408/results")
LOCAL_DATAFILE_DIR = Path.home().joinpath("Documents/data/results")
REPO_DATA_DIR = Path(__file__).parent.absolute().joinpath("data")

# Set up logging
logger = logging.getLogger(__name__)

@click.group()
def cli():
    pass

@click.command()
@click.option('--expected-paths-file', type=click.Path(exists=True), required=False,
              default=REPO_DATA_DIR.joinpath("malformed_assembly_paths", "expected_paths.txt"))
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
                old_file_path = datafile
                new_file_path = working_dir.joinpath(f"nmdc_{exp_datafile_assembly_id}_{datafile_type}")
                num_processed += 1
                logger.info(f"Data file name does not match expected: {datafile.name}")
                logger.info(f"Data object type: {data_object_type}")
                logger.info(f"Old path: {old_file_path}")
                logger.info(f"New path: {new_file_path}")

                if update_files:
                    if not data_object_type:
                        logger.error(f"Do not know how to update with no data object type: {datafile.name}")
                        continue
                    md5, size = assembly_file_operations(
                        old_workflow_id, new_workflow_id, data_object_type, old_file_path, new_file_path)
                    logger.info(f"New path: {new_file_path}")
                    logger.info(f"MD5: {md5}, Size: {size}")

                    # Remove the old file
                    old_file_path.unlink()

                else:
                    logger.info("--update-files not set.")
                    logger.info(f"Would update to {new_file_path}")

    logger.info(f"Processed {num_processed} files in {time.time() - start_time} seconds.")



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



cli.add_command(fix_malformed_assembly_paths)

if __name__ == '__main__':
    cli()
