import sys
import os
import logging


class config():

    def __init__(self):
        cf = os.path.join(os.environ['HOME'], '.wf_config')
        self.conf_file = os.environ.get('WF_CONFIG_FILE', cf)
        self.conf = self._read_config()
        # self.workflows = self._load_workflows()

    def _read_config(self):
        """
        Read config file for URL, WDL dir and template dir
        """
        conf = dict()
        if not os.path.exists(self.conf_file):
            sys.stderr.write("Missing %s.\n" % (self.conf_file))
            sys.stderr.write("Create or set WF_CONFIG_FILE\n")
            raise OSError("Missing configuration file")

        with open(self.conf_file) as f:
            for line in f:
                if line.startswith("#") or line == '\n':
                    continue
                (k, v) = line.rstrip().split('=')
                conf[k.lower()] = v
            if 'cromwell_url' not in conf:
                logging.error("Missing URL")
                raise ValueError("Missing cromwell URL")
            conf['url'] = conf['cromwell_url']
            if 'api' not in conf['url']:
                conf['url'] = conf['url'].rstrip('/') + "/api/workflows/v1"
        return conf

    def get_data_dir(self):
        return self.conf['data_dir']

    def get_stage_dir(self):
        return self.conf['stage_dir']
