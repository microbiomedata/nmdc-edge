import configparser
import pandas as pd
import ast
import pytest
from pathlib import Path

FIXTURE_DIR = Path(__file__).parent / "fixtures"


# @pytest.fixture
# def import_config():
#     config = configparser.ConfigParser()
#     config.read(FIXTURE_DIR / "import_config.ini")
#     return config


@pytest.fixture
def grow_analysis_df():
    grow_analysis_df = pd.read_csv(FIXTURE_DIR / "grow_analysis_projects.csv")
    grow_analysis_df.columns = [
        "apGoldId",
        "studyId",
        "itsApId",
        "projects",
        "biosample_id",
        "seq_id",
        "file_name",
        "file_status",
        "file_size",
        "jdp_file_id",
        "md5sum",
        "analysis_project_id",
    ]
    grow_analysis_df = grow_analysis_df[
        [
            "apGoldId",
            "studyId",
            "itsApId",
            "projects",
            "biosample_id",
            "seq_id",
            "file_name",
            "file_status",
            "file_size",
            "jdp_file_id",
            "md5sum",
            "analysis_project_id",
        ]
    ]
    grow_analysis_df["projects"] = grow_analysis_df["projects"].apply(ast.literal_eval)
    return grow_analysis_df
