import logging
import asyncio
from datetime import datetime
import uuid
import os
from time import sleep as _sleep
from nmdc_automation.api.nmdcapi import nmdcapi
from nmdc_automation.workflow_automation.workflows import load_workflows, Workflow
from functools import lru_cache
from pymongo import MongoClient
from pymongo.database import Database as MongoDatabase
from nmdc_automation.workflow_automation.activities import load_activities, Activity
from semver.version import Version


_POLL_INTERVAL = 60
_WF_YAML_ENV = "NMDC_WORKFLOW_YAML_FILE"


@lru_cache
def get_mongo_db() -> MongoDatabase:
    for k in ["HOST", "USERNAME", "PASSWORD", "DBNAME"]:
        if f"MONGO_{k}" not in os.environ:
            raise KeyError(f"Missing MONGO_{k}")
    _client = MongoClient(
        host=os.getenv("MONGO_HOST"),
        username=os.getenv("MONGO_USERNAME"),
        password=os.getenv("MONGO_PASSWORD"),
    )
    return _client[os.getenv("MONGO_DBNAME")]


def within_range(wf1: Workflow, wf2: Workflow) -> bool:
    """
    Determine if two workflows are within a major and minor
    version of each other.
    """
    def get_version(wf):
        v_string = wf1.version.lstrip("b").lstrip("v")
        return Version.parse(v_string)

    # Apples and oranges
    if wf1.name != wf2.name:
        return False
    v1 = get_version(wf1)
    v2 = get_version(wf2)
    if v1.major == v2.major and v1.minor == v2.minor:
        return True
    return False


"""
This is still a prototype implementation.  The plan
is to migrate this fucntion into Dagster.
"""


class Job():
    """
    Class to hold information for new jobs
    """

    def __init__(self, workflow: Workflow,
                 trigger_act: str):
        self.workflow = workflow
        self.trigger_act = trigger_act
        self.informed_by = trigger_act.was_informed_by
        self.trigger_id = trigger_act.id


class Scheduler():
    # TODO: Get this from the config
    _sets = ['metagenome_annotation_activity_set',
             'metagenome_assembly_set',
             'read_qc_analysis_activity_set',
             'mags_activity_set',
             'read_based_analysis_activity_set']

    def __init__(self, db, wfn="workflows.yaml"):
        logging.info("Initializing Scheduler")
        # Init
        wf_file = os.environ.get(_WF_YAML_ENV, wfn)
        self.workflows = load_workflows(wf_file)
        self.db = db
        self.api = nmdcapi()

    async def run(self):
        logging.info("Starting Scheduler")
        while True:
            self.cycle()
            await asyncio.sleep(_POLL_INTERVAL)

    def add_job_rec(self, job: Job):
        """
        This takes a job and using the workflow definition,
        resolves all the information needed to create a
        job record.
        """
        # Get all the data objects
        next_act = job.trigger_act
        do_by_type = dict()
        while next_act:
            for do_type, val in next_act.data_objects_by_type.items():
                do_by_type[do_type] = val.__dict__
            # do_by_type.update(next_act.data_objects_by_type.__dict__)
            next_act = next_act.parent

        wf = job.workflow
        base_id, iteration = self.get_activity_id(wf, job.informed_by)
        activity_id = f"{base_id}.{iteration}"
        inp_objects = []
        inp = dict()
        for k, v in job.workflow.inputs.items():
            if v.startswith('do:'):
                do_type = v[3:]
                dobj = do_by_type.get(do_type)
                if not dobj:
                    raise ValueError(f"Unable to resolve {do_type}")
                inp_objects.append(dobj)
                v = dobj["url"]
            # TODO: Make this smarter
            elif v == "{was_informed_by}":
                v = job.informed_by
            elif v == "{activity_id}":
                v = activity_id

            inp[k] = v

        # Build the respoonse
        job_config = {
                "git_repo": wf.git_repo,
                "release": wf.version,
                "wdl": wf.wdl,
                "activity_id": activity_id,
                "activity_set": wf.collection,
                "was_informed_by": job.informed_by,
                "trigger_activity": job.trigger_id,
                "iteration": iteration,
                "input_prefix": wf.input_prefix,
                "inputs": inp,
                "input_data_objects": inp_objects
                }
        if wf.activity:
            job_config["activity"] = wf.activity
        if wf.outputs:
            outputs = []
            for output in wf.outputs:
                # Mint an ID
                output["id"] = self.api.minter("nmdc:DataObject",
                                               job.informed_by)
                outputs.append(output)
            job_config["outputs"] = outputs

        jr = {
            "workflow": {
                "id": f"{wf.name}: {wf.version}"
            },
            "id": self.generate_job_id(),
            "created_at": datetime.today().replace(microsecond=0),
            "config": job_config,
            "claims": []
        }
        self.db.jobs.insert_one(jr, bypass_document_validation=True)
        logging.info(f'JOB RECORD: {jr["id"]}')
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
            "nmdc:ReadBasedTaxonomyAnalysisActivity": "mgrbt"
        }
        return f"nmdc:wf{mapping[id_type]}-11-xxxxxx"

    def get_activity_id(self, wf: Workflow, informed_by: str):
        """
        See if anything exist for this and if not
        mint a new id.
        """
        # We need to see if any version exist and
        # if so get its ID
        ct = 0
        q = {"was_informed_by": informed_by}
        for doc in self.db[wf.collection].find(q):
            ct += 1
            last_id = doc['id']

        if ct == 0:
            # Get an ID
            if os.environ.get("MOCK_MINT"):
                root_id = self.mock_mint(wf.type)
            else:
                root_id = self.api.minter(wf.type, informed_by)
            return root_id, 1
        else:
            root_id = '.'.join(last_id.split('.')[0:-1])
            return root_id, ct+1

    @lru_cache(maxsize=128)
    def get_existing_jobs(self, wf: Workflow):
        existing_jobs = set()
        # Filter by git_repo and version
        # Find all existing jobs for this workflow
        q = {'config.git_repo': wf.git_repo,
             'config.release': wf.version}
        for j in self.db.jobs.find(q):
            act = j['config']['trigger_activity']
            existing_jobs.add(act)
        return existing_jobs

    def find_new_jobs(self, act: Activity) -> list[Job]:
        """
        For a given activity see if there are any new jobs
        that should be created.
        """
        new_jobs = []
        # Loop over the derived workflows for this
        # activities' workflow
        for wf in act.workflow.children:
            # Ignore disabled workflows
            if not wf.enabled:
                continue
            # See if we already have a job for this
            if act.id in self.get_existing_jobs(wf):
                continue
            # Look at previously generated derived
            # activities to see if this is already done.
            for child_act in act.children:
                if within_range(child_act.workflow, wf):
                    break
            else:
                # These means no existing activities were
                # found that matched this workflow, so we
                # add a job
                logging.debug(f"Creating a job {wf.name} for {act.id}")
                new_jobs.append(Job(wf, act))

        return new_jobs

    def cycle(self) -> list:
        """
        This function does a single cycle of looking for new jobs
        """
        acts = load_activities(self.db, self.workflows)
        self.get_existing_jobs.cache_clear()
        job_recs = []
        for act in acts:
            jobs = self.find_new_jobs(act)
            for job in jobs:
                try:
                    jr = self.add_job_rec(job)
                    if jr:
                        job_recs.append(jr)
                except Exception as ex:
                    logging.error(str(ex))
                    raise ex
        return job_recs


def main():
    """
    Main function
    """
    sched = Scheduler(get_mongo_db())
    while True:
        sched.cycle()
        _sleep(_POLL_INTERVAL)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
