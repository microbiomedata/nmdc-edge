"""
Classes and methods for managing workflow jobs.
"""
import logging
from typing import List, Dict, Any
from abc import ABC, abstractmethod

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobRunner(ABC):
    """
    Abstract base class for a job runner. This class defines the interface
    that  specific job runners (e.g., Cromwell, JAWS) must implement.
    """

    @abstractmethod
    def submit_job(self, force: bool = False) -> Dict[str, Any]:
        """
        Submit a workflow job. The force flag is used to force submission of a
        job that has already been submitted.
        """
        pass

    @abstractmethod
    def check_job_status(self) -> Dict[str, Any]:
        """
        Check the status of a workflow job.
        """
        pass

    @abstractmethod
    def get_job_metadata(self) -> Dict[str, Any]:
        """
        Get metadata for a workflow job.
        """
        pass


class CromwellJobRunner(JobRunner):
    """
    A class for running Cromwell workflows.
    """

    def __init__(self, site_config, workflow_config, state=None):
        pass

    def submit_job(self, force: bool = False) -> Dict[str, Any]:
        """
        Submit a workflow job to Cromwell.
        """
        # Implementation details omitted
        pass

    def check_job_status(self) -> Dict[str, Any]:
        """
        Check the status of a workflow job in Cromwell.
        """
        # Implementation details omitted
        pass

        def get_job_metadata(self) -> Dict[str, Any]:
            """
            Get metadata for a workflow job in Cromwell.
            """
            # Implementation details omitted
            pass


class JawsJobRunner(JobRunner):
    """
    Stub class for a JAWS job runner.
    """
    def __init__(self, site_config, workflow_config, state=None):
        pass

    def submit_job(self, force: bool = False) -> Dict[str, Any]:
        """
        Submit a workflow job to JAWS.
        """
        logger.info("JAWS job submission is not yet implemented.")
        # Future implementation will submit a job to JAWS
        pass

    def check_job_status(self) -> Dict[str, Any]:
        """
        Check the status of a workflow job in JAWS.
        """
        logger.info("JAWS job status check is not yet implemented.")
        # Future implementation will check the status of a job in JAWS
        pass

    def get_job_metadata(self) -> Dict[str, Any]:
        """
        Get metadata for a workflow job in JAWS.
        """
        logger.info("JAWS job metadata retrieval is not yet implemented.")
        # Future implementation will get metadata for a job in JAWS
        pass



class WorkflowJobManager:
    """
    A class for managing workflow jobs.
    """

    def __init__(self, runner_type: str, site_config, workflow_config=None, state=None):
        if runner_type == 'Cromwell':
            self.runner = CromwellJobRunner(site_config, workflow_config, state)
        elif runner_type == 'JAWS':
            self.runner = JawsJobRunner()
        else:
            raise ValueError(f"Unsupported runner type: {runner_type}")

