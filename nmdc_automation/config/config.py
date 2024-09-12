from pathlib import Path
import tomli
from typing import Union
import yaml
import os
from pathlib import Path

WORKFLOWS_DIR = Path(__file__).parent / "workflows"

class UserConfig:
    def __init__(self, path):
        with open(path, "rb") as file:
            self.config_data = tomli.load(file)

    @property
    def base_url(self):
        return self.config_data["api"]["base_url"]

    @property
    def username(self):
        return self.config_data["api"]["username"]

    @property
    def password(self):
        return self.config_data["api"]["password"]

class Config:
    def __init__(self, path: Union[str, Path]):
        with open(path, "rb") as file:
            self.config_data = tomli.load(file)

    @property
    def cromwell_url(self):
        return self.config_data["cromwell"]["cromwell_url"]

    @property
    def cromwell_api(self):
        return self.config_data["cromwell"]["cromwell_api"]

    @property
    def stage_dir(self):
        return self.config_data["directories"]["stage_dir"]

    @property
    def template_dir(self):
        return self.config_data["directories"]["template_dir"]

    @property
    def data_dir(self):
        return self.config_data["directories"]["data_dir"]

    @property
    def raw_dir(self):
        return self.config_data["directories"]["raw_dir"]

    @property
    def resource(self):
        return self.config_data["site"]["resource"]

    @property
    def site(self):
        return self.config_data["site"]["site"]

    @property
    def url_root(self):
        return self.config_data["nmdc"]["url_root"]

    @property
    def api_url(self):
        return self.config_data["nmdc"]["api_url"]

    @property
    def watch_state(self):
        return self.config_data["state"]["watch_state"]

    @property
    def agent_state(self):
        return self.config_data["state"]["agent_state"]

    @property
    def activity_id_state(self):
        return self.config_data["state"]["activity_id_state"]

    @property
    def workflows_config(self):
        return self.config_data["workflows"]["workflows_config"]

    @property
    def client_id(self):
        return self.config_data["credentials"]["client_id"]

    @property
    def client_secret(self):
        return self.config_data["credentials"]["client_secret"]

    @property
    def allowed_workflows(self):
        """Generate a list of allowed workflows."""
        workflows_config_file = self.config_data["workflows"]["workflows_config"]
        # print current working directory
        print(os.getcwd())
        with open(WORKFLOWS_DIR / workflows_config_file, "r") as stream:
            workflows = yaml.safe_load(stream)

        # Initialize an empty list to store the results
        enabled_workflows = []

        # Iterate over the workflows
        for workflow in workflows["Workflows"]:
            # Check if the workflow is enabled
            if workflow.get("Enabled", True):
                # Concatenate name and version and append to list
                enabled_workflows.append(
                    f"{workflow['Name']}: {workflow.get('Version','')}"
                )

        # Return the results
        return enabled_workflows
