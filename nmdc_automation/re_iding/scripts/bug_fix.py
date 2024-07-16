#!/usr/bin/env python3
""" bug_fix.py - a Click script with commands to fix bugs in data path names and file names. """

import click
import logging
from pathlib import Path
import time

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

    logger.info(f"Expected paths file: {expected_paths_file}")
    logger.info(f"Production: {production}")
    logger.info(f"Update files: {update_files}")

    # Read the expected paths file
    with open(expected_paths_file) as f:

        if production:
            datafile_dir = PROD_DATAFILE_DIR
        else:
            datafile_dir = LOCAL_DATAFILE_DIR

        for line in f:
            # Parse out the components of the path
            line = line.strip()
            logger.debug(f"line: {line}")
            _data_dir, omics_dirname, exp_assembly_dirname, exp_filename = line.rsplit("/", maxsplit=3)
            logger.debug(f"omics_type: {omics_dirname}, assembly: {exp_assembly_dirname}, file_name: {exp_filename}")

            # Find the omics data dir
            omics_data_dir = datafile_dir.joinpath(omics_dirname)
            if not omics_data_dir.exists():
                if production:
                    logger.error(f"Omics data directory does not exist: {omics_data_dir}")
                    continue
                # Skip silently if using local data directory
                continue
            # Search for the malformed assembly directory
            assembly_dirname = None
            for dir in omics_data_dir.iterdir():
                if exp_assembly_dirname in dir.name:
                    assembly_dirname = dir
                    break
            if assembly_dirname is None:
                logger.error(f"Assembly directory not found: {exp_assembly_dirname}")
                continue
            logger.info(f"Found assembly directory: {assembly_dirname}")




cli.add_command(fix_malformed_assembly_paths)

if __name__ == '__main__':
    cli()
