# nmdc_automation/re_iding/file_utils.py
"""
file_utils.py: Provides utility functions for working with files.
"""
import logging
from pathlib import Path
import os
import hashlib
import json
import gzip
import pysam
from subprocess import check_output
from typing import Dict, Optional, Union, Tuple


# BASE_DIR = "/global/cfs/cdirs/m3408/results"
BAM_SCRIPT = Path("rewrite_bam.sh").resolve()
API_BASE_URL = "https://data.microbiomedata.org/data/"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)


def find_data_object_type(data_object_rec: Dict)-> Optional[str]:
    """
    Determine the data_object_type for a DO record based on its URL extension.

    Args:
    - data_object_record (dict): Dictionary containing the 'url' key which
    will be inspected to determine the data type.

    Returns:
    - str: The determined data type or None if the type could not be determined.
    """
    url = data_object_rec.get("url")
    name = data_object_rec.get("name")
    if "data_object_type" in data_object_rec:
        return data_object_rec["data_object_type"]
    elif url:
        return _infer_data_object_type_from_url(data_object_rec)
    elif name:
        return _infer_data_object_type_from_name(data_object_rec)
    else:
        logger.error(f"Could not determine data object type for: {data_object_rec}")
        return None


def _infer_data_object_type_from_url(data_object_rec: Dict) -> Optional[str]:
    """
    Determine the data_object_type for a DO record based on its URL extension.

    Args:
    - data_object_record (dict): Dictionary containing the 'url' key which
    will be inspected to determine the data type.

    Returns:
    - str: The determined data type or None if the type could not be determined.
    """
    if data_object_rec['url'].endswith("_covstats.txt"):
        return "Assembly Coverage Stats"
    elif data_object_rec['url'].endswith("_gottcha2_report.tsv"):
        return "GOTTCHA2 Classification Report"
    elif data_object_rec['url'].endswith("_gottcha2_report_full.tsv"):
        return "GOTTCHA2 Report Full"
    elif data_object_rec['url'].endswith(".fastq.gz") and "Filtered Reads" in data_object_rec['description']:
        return "Filtered Sequencing Reads"
    else:
        logger.error(f"Cannot infer type from url for: {data_object_rec}")
        return None


def _infer_data_object_type_from_name(data_object_rec: Dict) -> Optional[str]:
    """
    Determine the data_object_type for a DO record based on its name.

    Args:
    - data_object_record (dict): Dictionary containing the 'name' key which
    will be inspected to determine the data type.

    Returns:
    - str: The determined data type or None if the type could not be determined.
    """
    if data_object_rec['name'] == "mapping_stats.txt":
        return "Assembly Coverage Stats"
    elif data_object_rec['name'] == "assembly_contigs.fna":
        return "Assembly Contigs"
    elif data_object_rec['name'] == "assembly_scaffolds.fna":
        return "Assembly Scaffolds"
    elif data_object_rec['name'] == "assembly.agp":
        return "Assembly AGP"
    elif data_object_rec['name'] == "pairedMapped_sorted.bam":
        return "Assembly Coverage BAM"
    else:
        logger.error(f"Cannot infer type from name for: {data_object_rec}")
        return None


def md5_sum(fn: str) -> str:
    """
    Calculate the MD5 hash of a file.

    Args:
    - fn (str): Path to the file for which the MD5 hash is to be computed.

    Returns:
    - str: The MD5 hash of the file.
    """
    with open(fn, "rb") as f:
        file_hash = hashlib.md5()
        while chunk := f.read(8192):
            file_hash.update(chunk)
    return file_hash.hexdigest()


def rewrite_file_and_replace_identifiers(
        src: Union[str, os.PathLike],
        dst: Union[str, os.PathLike],
        old_id: str,
        new_id: str,
        prefix: str = None) -> Tuple[str, int]:
    """
    Rewrite lines in a file, replacing occurrences of an old ID with a new ID.
    An optional prefix can be specified to limit which lines are modified.

    Args:
    - src (str): Source file path.
    - dst (str): Destination file path.
    - old_id (str): ID to be replaced.
    - new_id (str): Replacement ID.
    - prefix (str, optional): Prefix character to determine which lines to modify. Defaults to None.

    Returns:
    - tuple: MD5 checksum and size (in bytes) of the modified file.
    """
    fsrc = open(src)
    fdst = open(dst, "w")
    for line in fsrc:
        if not prefix or (prefix and line[0] == prefix):
            line = line.replace(old_id, new_id)
        fdst.write(line)
    fsrc.close()
    fdst.close()
    md5 = md5_sum(dst)
    size = os.stat(dst).st_size
    return md5, size


def find_assembly_id(src):
    fsrc = open(src)
    line = fsrc.readline()
    return "_".join(line[1:].split("_")[0:-1])


def rewrite_bam(input_bam, output_bam, old_id, new_id):
    # First, copy the header and update the reference sequence names
    header_dict = pysam.AlignmentFile(input_bam, "rb").header.copy().to_dict()
    header_dict['SQ'] = [{'LN': sq['LN'], 'SN': sq['SN'].replace(old_id, new_id)} for sq in header_dict['SQ']]
    new_header = pysam.AlignmentHeader.from_dict(header_dict)

    # Write the output file with the modified header and close the file - we will reopen it for writing
    with pysam.AlignmentFile(output_bam, "wb", header=header_dict) as output_bam_file:
        logging.info(f"Writing to {output_bam}")
        pass

    # Reopen the output file for writing
    with pysam.AlignmentFile(output_bam, "wb", header=new_header) as output_bam_file:
        # Iterate over input aligned segments - make a new AlignedSegment object
        for read in pysam.AlignmentFile(input_bam, "rb"):
            read_dict = read.to_dict()
            # replace old_id with new_id in the read_dict anywhere it appears
            for key in read_dict:
                if isinstance(read_dict[key], str):
                    read_dict[key] = read_dict[key].replace(old_id, new_id)
            # create a new AlignedSegment object from the modified read_dict and new_header
            read = pysam.AlignedSegment.from_dict(read_dict, new_header)
            # Write the modified alignment record to the output BAM file
            output_bam_file.write(read)
    # Return the MD5 checksum and size of the modified BAM file
    md5 = md5_sum(output_bam)
    size = os.stat(output_bam).st_size
    return md5, size


def replace_and_write_bam(input_bam, output_bam, old_id, new_id):
    with pysam.AlignmentFile(input_bam, "rb") as input_bam_file, \
            pysam.AlignmentFile(output_bam, "wb", header=input_bam_file.header) as output_bam_file:

        for read in input_bam_file:
            # Replace old_id with new_id in tags and other fields if necessary
            # Modify other attributes of the read as needed

            # Example: Replace old_id in read name
            read.query_name = read.query_name.replace(old_id, new_id)

            # Write the modified read to the output BAM file
            output_bam_file.write(read)


def assembly_file_operations(
        old_workflow_id: str,
        new_workflow_id: str,
        data_object_type: str,
        old_file_path: Path,
        new_file_path: Path
) -> Optional[Tuple[str, int]]:
    """
    Perform file operations for different assembly data object types.
    """
    if new_file_path.exists():
        logging.info(f"File already exists at {new_file_path}. Skipping processing.")
        return

    logging.info(f"Processing {data_object_type} for {new_workflow_id}")
    logging.info(f"Destination: {new_file_path}")
    logging.info(f"Old file path: {old_file_path}")

    if data_object_type == "Assembly Coverage Stats":
        md5, size = rewrite_file_and_replace_identifiers(old_file_path, new_file_path, old_workflow_id, new_workflow_id)
    elif data_object_type == "Assembly Contigs":
        md5, size = rewrite_file_and_replace_identifiers(
            old_file_path, new_file_path,old_workflow_id, new_workflow_id, prefix=">")
    elif data_object_type == "Assembly Scaffolds":
        md5, size = rewrite_file_and_replace_identifiers(
            old_file_path, new_file_path, old_workflow_id, new_workflow_id, prefix=">")
    elif data_object_type == "Assembly AGP":
        md5, size = rewrite_file_and_replace_identifiers(
            old_file_path, new_file_path, old_workflow_id, new_workflow_id)
    elif data_object_type == "Assembly Coverage BAM":
        md5, size = rewrite_bam(
            old_file_path, new_file_path, old_workflow_id, new_workflow_id
        )
    else:
        logging.error(f"Unsupported data object type: {data_object_type}")
        md5, size = None, None
    return md5, size


def get_workflow_id_from_scaffold_file(scaffold_file: Union[str, os.PathLike]) -> str:
    """
    Extract the workflow ID from the first line of a scaffold file.
    """
    with open(scaffold_file, "r") as f:
        line = f.readline()
        return "_".join(line[1:].split("_")[0:-1])


def compute_new_data_file_path(
        old_url: str,
        new_base_dir: Union[str, os.PathLike],
        act_id: str,
) -> Path:
    """
    Compute the new path for the file based on the old url and the new base directory.
    If the old base directory is provided, create a link between the old file and the new file.
    """
    file_name = old_url.split("/")[-1]
    file_extenstion = file_name.lstrip("nmdc_").split("_", maxsplit=1)[-1]
    new_file_name = f"{act_id}_{file_extenstion}"
    modified_new_file_name = new_file_name.replace(":", "_")
    new_data_file_path = Path(new_base_dir, modified_new_file_name)

    return new_data_file_path


def link_data_file_paths(old_url: str, old_base_dir: Union[str, os.PathLike], new_path: Union[str, os.PathLike]) -> \
        None:
    base_url = "https://data.microbiomedata.org/data/"
    if not old_url.startswith(base_url):
        logging.error(f"The URL {old_url} does not start with the expected base URL {base_url}.")
        return
    # Extract the suffix and construct the old file path
    suffix = old_url[len(base_url):]
    old_file_path = Path(old_base_dir, suffix)
    new_file_path = Path(new_path)
    # Check if the destination link already exists
    if new_file_path.exists():
        logging.info(f"File already exists at {new_file_path}. Skipping linking.")
        return

    try:
        os.link(old_file_path, new_path)
        logging.info(f"Successfully created link between {old_file_path} and {new_file_path}")
    except OSError as e:
        logging.error(f"An error occurred while linking the file from {old_file_path} to {new_file_path}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error while linking the file from {old_file_path} to {new_file_path}: {e}")


def get_corresponding_data_file_path_for_url(data_object_url: str, data_dir: Path) -> Optional[Path]:
    """
    Get the corresponding data file for the given data object URL. The URL and/or the data file name
    may contain malformed workflow IDs that need to be fixed, and they may be different between the
    data object URL and the actual data file path.

    Return the best matching data file path
    """
    # Everything after */data/ is the data path
    # e.g. https://data.microbiomedata.org/data/nmdc:omprc-11-wmzpa354/nmdc:wfmgas-11-y43zyn66.1/nmdc_wfmgas-11-y43zyn66.1_contigs.fna
    file_name_from_url = data_object_url.split("/")[-1]
    workflow_dir_from_url = data_object_url.split("/")[-2]
    omics_dir_from_url = data_object_url.split("/")[-3]

    # try to find the data file path based on the URL
    data_file_path = data_dir.joinpath(omics_dir_from_url, workflow_dir_from_url, file_name_from_url)
    if data_file_path.exists():
        logging.info(f"Found data file path based on URL: {data_file_path}")
        return data_file_path
    else:
        logging.warning(f"Exact Data file path not found based on URL: {data_file_path}")
        workflow_path = data_dir.joinpath(omics_dir_from_url, workflow_dir_from_url)
        # prefix is everything before the first .1 in the file name
        prefix = file_name_from_url.split(".1")[0]
        # suffix is everything after the last .1 in the file name
        suffix = file_name_from_url.split(".1")[-1]
        # look for a data file that contains the prefix and suffix - raise an error if there are multiple matches
        # ignore symlinks
        logging.info(workflow_path)
        matching_files = list(workflow_path.glob(f"{prefix}*{suffix}"))
        matching_files = [f for f in matching_files if not os.path.islink(f)]
        if len(matching_files) == 1:
            logging.info(f"Found data file path based on prefix and suffix: {matching_files[0]}")
            return matching_files[0]
        elif len(matching_files) == 0:
            logging.warning(f"No data file found based on prefix and suffix: {prefix}*{suffix}")
            return None
        else:
            logging.error(f"Multiple data files found based on prefix and suffix: {matching_files}")
            raise ValueError(f"Multiple data files found based on prefix and suffix: {matching_files}")
