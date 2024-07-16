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
            assembly_dirname = None
            for dir in omics_data_dir.iterdir():
                if exp_assembly_id in dir.name:
                    assembly_dirname = dir.name
                    working_dir = omics_data_dir.joinpath(assembly_dirname)
                    break
            if assembly_dirname is None:
                logger.error(f"Assembly directory not found: {exp_assembly_id}")
                continue
            logger.info(f"Found assembly directory: {assembly_dirname}")

            # Rename the assembly directory to the expected name if it does not match and update_files is True
            if assembly_dirname != exp_assembly_id:
                new_assembly_dir = omics_data_dir.joinpath(exp_assembly_id)
                if update_files:
                    working_dir.rename(new_assembly_dir)
                    logger.info(f"Renamed assembly directory: {working_dir} to {new_assembly_dir}")
                else:
                    logger.info(f"Would rename assembly directory: {assembly_dirname} to {exp_assembly_id}")

            # Data Files
            # need to break up expected and actual file names into components
            # e.g nmdc_wfmgas-11-nvt77985.1.1_pairedMapped_sorted.bam
            _nmdc, exp_datafile_name, exp_datafile_type = exp_filename.split("_", maxsplit=2)
            # Search for the data file
            datafile = None
            logger.debug(f"exp_assembly_id: {exp_assembly_id} exp_datafile_type: {exp_datafile_type}")
            for file in working_dir.iterdir():
                logger.debug(f"file: {file}")
                if exp_datafile_name in file.name and exp_datafile_type in file.name:
                    datafile = file
                    break
            if datafile is None:
                logger.error(f"Data file not found: {exp_filename}")
                continue
            logger.info(f"Found data file: {datafile}")

            # Infer the data type from the data file name and extension
            if datafile.name.endswith("pairedMapped_sorted.bam"):
                data_type = "Assembly Coverage BAM"
            elif datafile.name.endswith("assembly.agp"):
                data_type = "Assembly AGP"
            elif datafile.name.endswith("_scaffolds.fna"):
                data_type = "Assembly Scaffolds"
            elif datafile.name.endswith("_contigs.fna"):
                data_type = "Assembly Contigs"
            elif datafile.name.endswith("mapping_stats.txt"):
                data_type = "Assembly Coverage Stats"
            else:
                logger.error(f"Unknown data file type: {datafile.name}")
                continue


            old_workflow_id = assembly_dirname
            new_workflow_id = exp_assembly_id
            data_object_type = data_type
            old_file_path = datafile
            new_file_path = working_dir.joinpath(exp_filename)

            logger.info(f"old_workflow_id: {old_workflow_id}")
            logger.info(f"new_workflow_id: {new_workflow_id}")
            logger.info(f"data_object_type: {data_object_type}")
            logger.info(f"old_file_path: {old_file_path}")
            logger.info(f"new_file_path: {new_file_path}")









cli.add_command(fix_malformed_assembly_paths)

if __name__ == '__main__':
    cli()
