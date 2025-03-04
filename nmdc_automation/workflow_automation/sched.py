import logging
import asyncio
from datetime import datetime
import uuid
import os
from time import sleep as _sleep
from nmdc_automation.api.nmdcapi import NmdcRuntimeApi
from nmdc_automation.workflow_automation.workflows import load_workflow_configs
from functools import lru_cache
from pymongo import MongoClient
from pymongo.database import Database as MongoDatabase
from nmdc_automation.workflow_automation.workflow_process import load_workflow_process_nodes
from nmdc_automation.models.workflow import WorkflowConfig, WorkflowProcessNode
from semver.version import Version
import sys


_POLL_INTERVAL = 60
_WF_YAML_ENV = "NMDC_WORKFLOW_YAML_FILE"

# TODO: Berkley refactoring:
#   The Scheduler interacts with the API to mint new IDs for activities and jobs.
#   The Scheduler pulls WorkflowExecution and DataObject records from the MongoDB database - need to ensure these
#   the handling of these records is compatible with the Berkley schema.
#   The Scheduler looks for new jobs to create by examining the 'Activity' object graph that is constructed from
#   the retrieved WorkflowExecution and DataObject records. This data structure will be somewhat different in the
#   Berkley schema, so the find_new_jobs method will need to be updated to handle this.
# configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
@lru_cache
def get_mongo_db() -> MongoDatabase:
    _client = MongoClient(
        host=os.getenv("MONGO_HOST", "localhost"),
        port=int(os.getenv("MONGO_PORT", "27018")),
        username=os.getenv("MONGO_USERNAME", "admin"),
        password=os.getenv("MONGO_PASSWORD", "root"),
        directConnection=True,
    )[os.getenv("MONGO_DBNAME", "nmdc")]
    return _client



def within_range(wf1: WorkflowConfig, wf2: WorkflowConfig, force=False) -> bool:
    """
    Determine if two workflows are within a major and minor
    version of each other.
    """

    def get_version(wf):
        v_string = wf.version.lstrip("b").lstrip("v")
        return Version.parse(v_string)

    # Apples and oranges
    if wf1.name != wf2.name:
        return False
    v1 = get_version(wf1)
    v2 = get_version(wf2)
    if force:
        return v1 == v2
    if v1.major == v2.major and v1.minor == v2.minor:
        return True
    return False


"""
This is still a prototype implementation.  The plan
is to migrate this fucntion into Dagster.
"""

# TODO: Change the name of this to distinguish it from the database Job object
class SchedulerJob:
    """
    Class to hold information for new jobs
    """

    def __init__(self, workflow: WorkflowConfig, trigger_act: WorkflowProcessNode):
        self.workflow = workflow
        self.trigger_act = trigger_act
        self.informed_by = trigger_act.was_informed_by
        self.trigger_id = trigger_act.id


class Scheduler:

    def __init__(self, db, workflow_yaml,
                 site_conf="site_configuration.toml"):

        # Init
        # wf_file = os.environ.get(_WF_YAML_ENV, wfn)
        self.workflows = load_workflow_configs(workflow_yaml)
        self.db = db
        self.api = NmdcRuntimeApi(site_conf)
        # TODO: Make force a optional parameter
        self.force = False
        if os.environ.get("FORCE") == "1":
            logger.info("Setting force on")
            self.force = True
        self._messages = []

    async def run(self):
        logger.info("Starting Scheduler")
        while True:
            self.cycle()
            await asyncio.sleep(_POLL_INTERVAL)

    def create_job_rec(self, job: SchedulerJob):
        """
        This takes a job and using the workflow definition,
        resolves all the information needed to create a
        job record.
        """
        # Get all the data objects
        next_act = job.trigger_act
        do_by_type = dict()
        while next_act:
            for do_type, data_object in next_act.data_objects_by_type.items():
                if do_type in do_by_type:
                    logger.debug(f"Ignoring Duplicate type: {do_type} {data_object.id} {next_act.id}")
                    continue
                do_by_type[do_type] = data_object
            # do_by_type.update(next_act.data_objects_by_type.__dict__)
            next_act = next_act.parent

        wf = job.workflow
        base_id, iteration = self.get_activity_id(wf, job.informed_by)
        workflow_execution_id = f"{base_id}.{iteration}"
        input_data_objects = []
        inputs = dict()
        optional_inputs = wf.optional_inputs
        for k, v in job.workflow.inputs.items():
            # some inputs are booleans and should not be modified
            if isinstance(v, bool):
                inputs[k] = v
                continue
            elif v.startswith("do:"):
                do_type = v[3:]
                dobj = do_by_type.get(do_type)
                if not dobj:
                    if k in optional_inputs:
                        continue
                    raise ValueError(f"Unable to find {do_type} in {do_by_type}")
                input_data_objects.append(dobj.as_dict())
                v = dobj["url"]
            # TODO: Make this smarter
            elif v == "{was_informed_by}":
                v = job.informed_by
            elif v == "{workflow_execution_id}":
                v = workflow_execution_id
            elif v == "{predecessor_activity_id}":
                v = job.trigger_act.id

            inputs[k] = v

        # Build the respoonse
        job_config = {
            "git_repo": wf.git_repo,
            "release": wf.version,
            "wdl": wf.wdl,
            "activity_id": workflow_execution_id,
            "activity_set": wf.collection,
            "was_informed_by": job.informed_by,
            "trigger_activity": job.trigger_id,
            "iteration": iteration,
            "input_prefix": wf.input_prefix,
            "inputs": inputs,
            "input_data_objects": input_data_objects,
        }
        if wf.workflow_execution:
            job_config["activity"] = wf.workflow_execution
        if wf.outputs:
            outputs = []
            for output in wf.outputs:
                # Mint an ID
                output["id"] = self.api.minter("nmdc:DataObject", job.informed_by)
                outputs.append(output)
            job_config["outputs"] = outputs

        jr = {
            "workflow": {"id": f"{wf.name}: {wf.version}"},
            "id": self.generate_job_id(),
            "created_at": datetime.today().replace(microsecond=0),
            "config": job_config,
            "claims": [],
        }

        logger.info(f'JOB RECORD: {jr["id"]}')
        # This would make the job record
        # print(json.dumps(ji, indent=2))
        return jr

    def generate_job_id(self) -> str:
        """
        Generate an ID for the job

        Note: This is not currently Napa compliant.  Since these are somewhat
        ephemeral I'm not sure if it matters though.
        """
        u = str(uuid.uuid1())
        return f"nmdc:{u}"

    def mock_mint(self, id_type):  # pragma: no cover
        """
        Return a fixed pattern used for testing
        """
        mapping = {
            "nmdc:ReadQcAnalysisActivity": "mgrqc",
            "nmdc:MetagenomeAssembly": "mgasm",
            "nmdc:MetagenomeAnnotationActivity": "mgann",
            "nmdc:MAGsAnalysisActivity": "mgmag",
            "nmdc:ReadBasedTaxonomyAnalysisActivity": "mgrbt",
        }
        return f"nmdc:wf{mapping[id_type]}-11-xxxxxx"

    def get_activity_id(self, wf: WorkflowConfig, informed_by: str):
        """
        See if anything exist for this and if not
        mint a new id.
        """
        # We need to see if any version exist and
        # if so get its ID
        ct = 0
        q = {"was_informed_by": informed_by, "type": wf.type}
        for doc in self.db[wf.collection].find(q):
            ct += 1
            last_id = doc["id"]

        if ct == 0:
            # Get an ID
            if os.environ.get("MOCK_MINT"):
                root_id = self.mock_mint(wf.type)
            else:
                root_id = self.api.minter(wf.type, informed_by)
            return root_id, 1
        else:
            root_id = ".".join(last_id.split(".")[0:-1])
            return root_id, ct + 1

    # TODO: Rename this to reflect what it does - it returns a list of the trigger activity IDs
    #      from the jobs collection for a given workflow. Also activity should be execution to conform
    #      to the new schema.
    @lru_cache(maxsize=128)
    def get_existing_jobs(self, wf: WorkflowConfig):
        existing_jobs = set()
        # Filter by git_repo and version
        # Find all existing jobs for this workflow
        q = {"config.git_repo": wf.git_repo, "config.release": wf.version}
        for j in self.db.jobs.find(q):
            # the assumption is that a job in any state has been triggered by an activity
            # that was the result of an existing (completed) job
            act = j["config"]["trigger_activity"]
            existing_jobs.add(act)
        return existing_jobs

    # TODO: Rename this to reflect what it does and add unit tests
    def find_new_jobs(self, wfp_node: WorkflowProcessNode) -> list[SchedulerJob]:
        """
        For a given activity see if there are any new jobs
        that should be created.
        """
        new_jobs = []
        # Loop over the derived workflows for this
        # activities' workflow
        for wf in wfp_node.workflow.children:
            # Ignore disabled workflows
            if not wf.enabled:
                msg = f"Skipping disabled workflow {wf.name}:{wf.version}"
                if msg not in self._messages:
                    logger.info(msg)
                    self._messages.append(msg)
                continue
            # See if we already have a job for this
            if wfp_node.id in self.get_existing_jobs(wf):
                msg = f"Skipping existing job for{wfp_node.id} {wf.name}:{wf.version}"
                if msg not in self._messages:
                    logger.info(msg)
                    self._messages.append(msg)
                continue
            # Look at previously generated derived
            # activities to see if this is already done.
            for child_act in wfp_node.children:
                if within_range(child_act.workflow, wf, force=self.force):
                    msg = f"Skipping existing job for {child_act.id} {wf.name}:{wf.version}"
                    if msg not in self._messages:
                        logger.info(msg)
                        self._messages.append(msg)
                    break
            else:
                # These means no existing activities were
                # found that matched this workflow, so we
                # add a job
                msg = f"Creating a job {wf.name}:{wf.version} for {wfp_node.process.id}"
                if msg not in self._messages:
                    logger.info(msg)
                    self._messages.append(msg)
                new_jobs.append(SchedulerJob(wf, wfp_node))

        return new_jobs

    def cycle(self, dryrun: bool = False, skiplist: list[str] = None,
              allowlist=None) -> list:
        """
        This function does a single cycle of looking for new jobs
        """
        wfp_nodes = load_workflow_process_nodes(self.db, self.workflows, allowlist)
        if wfp_nodes:
            for wfp_node in wfp_nodes:
                msg = f"Found workflow process node {wfp_node.id}"
                if msg not in self._messages:
                    logger.info(msg)
                    self._messages.append(msg)
        else:
            msg = f"No workflow process nodes found for {allowlist}"
            if msg not in self._messages:
                logger.info(msg)
                self._messages.append(msg)

        self.get_existing_jobs.cache_clear()
        job_recs = []

        for wfp_node in wfp_nodes:
            if skiplist and wfp_node.id in skiplist:
                continue
            if not wfp_node.workflow.enabled:
                continue
            jobs = self.find_new_jobs(wfp_node)
            if jobs:
                logger.info(f"Found {len(jobs)} new jobs for {wfp_node.id}")
            for job in jobs:
                msg = f"new job: informed_by: {job.informed_by} trigger: {job.trigger_id} "
                msg += f"wf: {job.workflow.name} ver: {job.workflow.version}"
                logger.info(msg)

                if dryrun:
                    continue
                try:
                    jr = self.create_job_rec(job)
                    self.db.jobs.insert_one(jr)
                    if jr:
                        job_recs.append(jr)
                except Exception as ex:
                    logger.error(str(ex))
                    raise ex
        return job_recs



def main(site_conf, wf_file):  # pragma: no cover
    """
    Main function
    """
    # site_conf = os.environ.get("NMDC_SITE_CONF", "site_configuration.toml")
    db = get_mongo_db()
    logger.info("Initializing Scheduler")
    sched = Scheduler(db, wf_file, site_conf=site_conf)

    dryrun = False
    if os.environ.get("DRYRUN") == "1":
        dryrun = True
    skiplist = set()
    allowlist = None
    if os.environ.get("SKIPLISTFILE"):
        with open(os.environ.get("SKIPLISTFILE")) as f:
            for line in f:
                skiplist.add(line.rstrip())

    logger.info("Reading Allowlist")
    if os.environ.get("ALLOWLISTFILE"):
        allowlist = set()
        with open(os.environ.get("ALLOWLISTFILE")) as f:
            for line in f:
                allowlist.add(line.rstrip())
        logger.info(f"Read {len(allowlist)} items")
        for item in allowlist:
            logger.info(f"Allowing: {item}")

    logger.info(f"Adding ID: nmdc:omprc-11-pf500b03 to Allowlist")
    allowlist = ["nmdc:omprc-11-pf500b03"]


    logger.info("Starting Scheduler")
    cycle_count = 0
    while True:
        sched.cycle(dryrun=dryrun, skiplist=skiplist, allowlist=allowlist)
        cycle_count += 1
        if dryrun:
            break
        _sleep(_POLL_INTERVAL)
        if cycle_count % 100 == 0:
            logger.info(f"Cycles: {cycle_count}")


if __name__ == "__main__":  # pragma: no cover
    # site_conf and wf_file are passed in as arguments
    main(site_conf=sys.argv[1], wf_file=sys.argv[2])
