import os
import tomli
import yaml
import logging


class config():
    def __init__(self,config_file):
        self.conf_file = os.path.abspath(config_file)
        self.conf = self._load_config()

    def _load_config(self):
        """
        Read config toml for URL, WDL dir and template dir
        """
        try:
            with open(self.conf_file, mode='rb') as fp:
                conf = tomli.load(fp)
            conf['url'] = conf['cromwell']['cromwell_url']
            if 'api' not in conf['url']:
                conf['url'] = conf['url'].rstrip('/') + "/api/workflows/v1"
        except OSError:
            logging.error(f'Could not open/read configuration file {self.conf_file}, please provide path to site_configuration.toml')
        return conf
    
    def _dumps_value(value):
        '''
        Check type of config value
        '''
        if isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, list):
            return f"[{', '.join(v for v in value)}]"
        else:
            raise TypeError(f"{type(value).__name__} {value!r} is not supported")
        
    def _generate_allowed_workflows(self):
        
        with open(self.conf['workflows']['workflows'], 'r') as stream:
            workflows = yaml.safe_load(stream)

        # Initialize an empty list to store the results
        enabled_workflows = []

        # Iterate over the workflows
        for workflow in workflows['Workflows']:
            # Check if the workflow is enabled
            if workflow['Enabled']:
                # Concatenate name and version and append to list
                enabled_workflows.append(f"{workflow['Name']}: {workflow['Version']}")

        # Print the results
        return enabled_workflows

    def get_data_dir(self):
        return self.conf['directories']['data_dir']

    def get_stage_dir(self):
        return self.conf['directories']['stage_dir']
