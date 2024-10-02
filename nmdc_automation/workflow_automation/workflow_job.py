""" Classes for managing workflow jobs. """
from typing import List, Dict, Optional

from nmdc_automation.config.siteconfig import SiteConfig
from nmdc_automation.workflow_automation.models import WorkflowConfig


class WorkflowJob:

    def __init__(self, site_config: SiteConfig, workflow_config: WorkflowConfig):
        self.site_config = site_config
        self.workflow_config = workflow_config