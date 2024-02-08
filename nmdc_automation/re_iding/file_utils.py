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
    if "data_object_type" in data_object_rec:
        return data_object_rec["data_object_type"]
    url = data_object_rec.get("url")
    if url:
        return _infer_data_object_type_from_url(url)
    name = data_object_rec.get("name")
    if name:
        return _infer_data_object_type_from_name(name)
    return None



def _infer_data_object_type_from_url(url: str) -> Optional[str]:
    """
    Determine the data_object_type for a DO record based on its URL extension.

    Args:
    - url (str): The URL of the data object.

    Returns:
    - str: The determined data type or None if the type could not be determined.
    """
    if url.endswith("_covstats.txt"):
        return "Assembly Coverage Stats"
    elif url.endswith("_gottcha2_report.tsv"):
        return "GOTTCHA2 Classification Report"
    elif url.endswith("_gottcha2_report_full.tsv"):
        return "GOTTCHA2 Report Full"
    else:
        logger.error(f"Missing type: {url}")
        return None

def _infer_data_object_type_from_name(name: str) -> Optional[str]:
    """
    Determine the data_object_type for a DO record based on its name.

    Args:
    - name (str): The name of the data object.

    Returns:
    - str: The determined data type or None if the type could not be determined.
    """
    if name == "mapping_stats.txt":
        return "Assembly Coverage Stats"
    elif name == "assembly_contigs.fna":
        return "Assembly Contigs"
    elif name == "assembly_scaffolds.fna":
        return "Assembly Scaffolds"
    elif name == "assembly.agp":
        return "Assembly AGP"
    elif name == "pairedMapped_sorted.bam":
        return "Assembly Coverage BAM"
    else:
        logger.error(f"Missing type: {name}")
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


def read_json_file(filename: str)-> Dict[str, str]:
    """
    Read a JSON file and return its content as a dictionary.

    Parameters:
    - filename (str): The path to the JSON file.

    Returns:
    - dict: The content of the JSON file.
    """
    with open(filename, "r") as json_file:
        data = json.load(json_file)
    return data


def rewrite_id(src: str, dst: str, old_id: str, new_id: str, prefix: str =
None) -> Tuple[str, int]:
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


def assembly_contigs(src, dst, act_id):
    scaf = str(src).replace("_contigs", "_scaffolds")
    old_id = find_assembly_id(scaf)
    return rewrite_id(src, dst, old_id, act_id, prefix=">")


def assembly_scaffolds(src, dst, act_id):
    old_id = find_assembly_id(src)
    return rewrite_id(src, dst, old_id, act_id, prefix=">")


def assembly_coverage_stats(src, dst, act_id):
    scaf = str(src).replace("_covstats.txt", "_scaffolds.fna")
    old_id = find_assembly_id(scaf)
    return rewrite_id(src, dst, old_id, act_id)


def assembly_agp(src, dst, act_id):
    scaf = str(src).replace("_assembly.agp", "_scaffolds.fna")
    old_id = find_assembly_id(scaf)
    return rewrite_id(src, dst, old_id, act_id)


def convert_script(script, src, dst, old_id, act_id):
    cmd = [script, src, dst, old_id, act_id]
    results = check_output(cmd)
    md5 = md5_sum(dst)
    size = os.stat(dst).st_size
    return md5, size


def assembly_coverage_bam(script, src, dst, act_id):
    scaf = str(src).replace("_pairedMapped_sorted.bam", "_scaffolds.fna")
    old_id = find_assembly_id(scaf)
    return convert_script(script, src, dst, old_id, act_id)


def rewrite_sam(input_sam, output_sam, old_id, new_id):
    with gzip.open(input_sam, "rt") as f_in, gzip.open(output_sam, "wt") as f_out:
        for line in f_in:
            f_out.write(line.replace(old_id, new_id))


def get_old_file_path(data_object_record: dict, old_base_dir: Union[str, os.PathLike]) -> Path:
    old_url = data_object_record["url"]
    suffix = old_url.split("https://data.microbiomedata.org/data/")[1]
    old_file_path = Path(old_base_dir, suffix)

    return old_file_path


def assembly_file_operations(data_object_record, data_object_type,
                             destination, act_id, old_base_dir):
    logging.info(f"Processing {data_object_type} for {act_id}")
    logging.info(f"Destination: {destination}")
    logging.info(f"Old base dir: {old_base_dir}")
    # get old file path upfront
    old_file_path = get_old_file_path(data_object_record, old_base_dir)
    logging.info(f"Old file path: {old_file_path}")

    if data_object_type == "Assembly Coverage Stats":
        md5, size = assembly_coverage_stats(old_file_path, destination, act_id)
    elif data_object_type == "Assembly Contigs":
        md5, size = assembly_contigs(old_file_path, destination, act_id)
    elif data_object_type == "Assembly Scaffolds":
        md5, size = assembly_scaffolds(old_file_path, destination, act_id)
    elif data_object_type == "Assembly AGP":
        md5, size = assembly_agp(old_file_path, destination, act_id)
    elif data_object_type == "Assembly Coverage BAM":
        md5, size = assembly_coverage_bam(
            BAM_SCRIPT, old_file_path, destination, act_id
        )

    return md5, size


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


def link_data_file_paths(old_url: str, old_base_dir: Union[str, os.PathLike], new_path: Union[str, os.PathLike])-> \
        None:
    suffix = old_url.split("https://data.microbiomedata.org/data/")[1]
    old_file_path = Path(old_base_dir, suffix)
    try:
        os.link(old_file_path, new_path)
        logging.info(f"Successfully created link between {old_file_path} and {new_path}")
    except OSError as e:
        logging.error(f"An error occurred while linking the file: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")