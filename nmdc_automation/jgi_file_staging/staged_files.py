import configparser
import os
import pandas as pd
import argparse
import logging
from pathlib import Path

from mongo import get_mongo_db

logging.basicConfig(
    filename="file_staging.log",
    format="%(asctime)s.%(msecs)03d %(levelname)s {%(module)s} [%(funcName)s] %(message)s",
    datefmt="%Y-%m-%d,%H:%M:%S",
    level=logging.DEBUG,
)


def get_list_staged_files(project, config, save_file_list=None):
    base_dir = Path(config["GLOBUS"]["dest_root_dir"], f"{project}_analysis_projects")
    proj_list = []
    for analysis_proj in os.listdir(base_dir):
        [
            proj_list.append({"analysis_project": analysis_proj, "file": f})
            for f in os.listdir(os.path.join(base_dir, analysis_proj))
        ]

    stage_df = pd.DataFrame(proj_list)
    stage_df.to_csv("staged_files.csv", index=False) if save_file_list else None

    return stage_df


def get_list_missing_staged_files(
    project_name, config_file, save_file_list=None
) -> list:
    """
    Get list of files on file system for a project and compare to list of files in database
    """
    config = configparser.ConfigParser()
    config.read(config_file)
    stage_df = get_list_staged_files(project_name, config, save_file_list)
    stage_df["file_key"] = stage_df.apply(
        lambda x: f"{x.analysis_project}-{x.file}", axis=1
    )
    mdb = get_mongo_db()
    samples_df = pd.DataFrame([s for s in mdb.samples.find({"project": project_name})])
    samples_df["file_key"] = samples_df.apply(
        lambda x: f"{x.apGoldId}-{x.file_name}", axis=1
    )
    db_samples_df = pd.merge(
        samples_df, stage_df, left_on="file_key", right_on="file_key", how="outer"
    )
    db_samples_df.to_csv("merge_db_staged.csv", index=False)
    return db_samples_df.loc[
        pd.isna(db_samples_df.analysis_project), ["apGoldId", "file_name"]
    ].to_dict("records")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("project_name")
    parser.add_argument("config_file")
    parser.add_argument(
        "-s",
        "--save_file_list",
        action="store_true",
        help="save list of staged files to output file",
        default=False,
    )
    args = vars((parser.parse_args()))
    get_list_missing_staged_files(
        args["project_name"], args["config_file"], args["save_file_list"]
    )
