# nmdc_automation/re_iding/file_utils.py
"""
file_utils.py: Provides utility functions for working with files.
"""
import logging
from typing import Dict, Optional

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
    url = data_object_rec["url"]
    if url.endswith("_covstats.txt"):
        return "Assembly Coverage Stats"
    elif url.endswith("_gottcha2_report.tsv"):
        return "GOTTCHA2 Classification Report"
    elif url.endswith("_gottcha2_report_full.tsv"):
        return "GOTTCHA2 Report Full"
    else:
        logger.error(f"Missing type: {url}")
        return None