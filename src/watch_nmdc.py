#!/usr/bin/env python

from src.nmdcapi import nmdcapi
from src.config import config
from src.wfutils import job as wfjob
from time import sleep as _sleep
import json
import os
import sys
import shutil
import traceback
import jsonschema
import logging


class watcher():
    _POLL = 20
    _MAX_FAILS = 2
    # This is mainly used for testing
    cycles = -1

    _ALLOWED = ['Reads QC: v0.0.1']
#    _ALLOWED = ['metag-1.0.0', 'metat-1.0.0']
#    _ALLOWED = ['metag-1.0.0']

    def __init__(self):
        self.config = config()
        self.nmdc = nmdcapi()
        self.cromurl = self.config.conf['url']
        self.state_file = self.config.conf['agent_state']
        self.stage_dir = self.config.get_stage_dir()
        self.raw_dir = self.config.conf['raw_dir']
        self.jobs = []
        self.restored = False

    def restore(self, nocheck=False):
        """
        Restore from chkpt
        """
        if not os.path.exists(self.state_file):
            self.restored = True
            return
        data = json.loads(open(self.state_file).read())
        new_job_list = []
        seen = dict()
        for job in data['jobs']:
            jid = job['nmdc_jobid']
            if jid in seen:
                continue
            jr = wfjob(state=job, nocheck=nocheck)
            new_job_list.append(jr)
            seen[jid] = True
        self.jobs = new_job_list
        self.restored = True

    def ckpt(self):
        jobs = []
        for job in self.jobs:
            jobs.append(job.get_state())
        data = {'jobs': jobs}
        with open(self.state_file, "w") as f:
            f.write(json.dumps(data, indent=2))

    def cycle(self):
        self.nmdc.refresh_token()
        # Restore the state in case some other
        # process made a change
        self.restore()
        # Check for new jobs
        if not os.environ.get("SKIP_CLAIM"):
            self.claim_jobs()
        # Check existing jobs
        self.nmdc.refresh_token()
        self.check_status()

    def watch(self):
        """
        The endless loop
        """
        logging.info("Entering polling loop")
        while self.cycles != 0:
            try:
                self.cycle()
            except Exception as e:
                logging.error("Error")
                logging.error(e)
                traceback.print_exc(file=sys.stdout)
            if self.cycles > 0:
                self.cycles -= 1
            _sleep(self._POLL)

    def find_job_by_opid(self, opid):
        for j in self.jobs:
            if j.opid == opid:
                return j
        return None

    def submit(self, njob, opid, force=False):
        wfid = njob['workflow']['id']
        # Collect some info from the object
        if 'object_id_latest' in njob['config']:
            logging.warning("Old record. Skipping.")
            return
        job = self.find_job_by_opid(opid)
        if job:
            logging.debug("Previously cached job")
            logging.info("Reusing activity %s" % (job.activity_id))
        else:
            # Create a new job
            job = wfjob(wfid, njob['id'], njob['config'], opid,
                        activity_id=njob['config']['activity_id'])
            self.jobs.append(job)
        job.cromwell_submit(force=force)

    def refresh_remote_jobs(self):
        """
        Return a filtered list of nmdc jobs.
        """
        filt = {"workflow.id": {"$in": self._ALLOWED}}
        jobs = self.nmdc.list_jobs(filt=filt)
        # Get the jobs we know about
        known = dict()
        for j in self.jobs:
            known[j.nmdc_jobid] = 1
        resp = []
        for j in jobs:
            jid = j['id']
            if jid in known:
                continue
            resp.append(j)
        return resp

    def claim_jobs(self):
        for j in self.refresh_remote_jobs():
            jid = j['id']
            if j.get('claims') and len(j.get('claims')) > 0:
                continue
            logging.debug(f"try to claim: {jid}")
            self.nmdc.refresh_token()

            # claim job
            claim = self.nmdc.claim_job(jid)
            if not claim['claimed']:
                self.submit(j, claim['id'])
                self.ckpt()
            else:
                # Previously claimed
                opid = claim['detail']['id']
                # op = self.nmdc.get_op(opid)
                logging.info("Previously claimed.")
                self.submit(j, opid)
                self.ckpt()

    def _load_json(self, fn):
        return json.loads(open(fn).read())

    # Future
    def validate_objects(self, results):  # pragma: no cover
        schemafile = os.environ.get("SCHEMA")
        if schemafile:
            schema = self._load_json(schemafile)
            try:
                jsonschema.validators.validate(results, schema)
            except jsonschema.exceptions.ValidationError as ex:
                logging.error("Failed validation")
                logging.error(ex)

    def fix_urls(self, dos, actid, subdir):
        root = self.config.conf['url_root'].rstrip('/')
        for do in dos:
            fn = do['url'].split('/')[-1]
            new_url = f"{root}/{actid}/{subdir}/{fn}"
            do['url'] = new_url

    def post_job_done(self, job):
        # Prepare the result record
        logging.info("Running post for op %s" % (job.opid))
        md = job.get_metadata()
        dd = self.config.get_data_dir()
        subdir = "{directory}.{iteration}".format(**job.conf)
        outdir = os.path.join(dd, job.activity_id, subdir)
        obj = dict()
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        for k, v in md['outputs'].items():
            np = os.path.join(outdir, os.path.basename(v))
            if k.endswith("objects"):
                obj = json.load(open(v))
                # TODO Move this into the workflow
                self.fix_urls(obj['data_object_set'], job.activity_id, subdir)
                if not os.path.exists(np):
                    json.dump(obj, open(np, "w"))
            else:
                if os.path.exists(np):
                    logging.warning(f"output {np} exist.  Skipping\n")
                    continue
                shutil.copyfile(v, np)
        mdf = os.path.join(outdir, "metadata.json")
        if not os.path.exists(mdf):
            json.dump(md, open(mdf, "w"))
        resp = self.nmdc.post_objects(obj)
        job.done = True
        resp = self.nmdc.update_op(job.opid, done=True,
                                   meta=md)
        return resp

    def check_status(self):
        for job in self.jobs:
            if job.done:
                continue
            status = job.check_status()
            if status == 'Succeeded' and job.opid and not job.done:
                self.post_job_done(job)
                self.ckpt()
            elif status == 'Failed' and job.opid:
                if job.failed_count < self._MAX_FAILS:
                    job.failed_count += 1
                    job.cromwell_submit()
                self.ckpt()
            elif job.opid and not job.done:
                continue


def jprint(obj):
    print(json.dumps(obj, indent=2))


def main():  # pragma: no cover
    w = watcher()
    if len(sys.argv) > 1:
        # Manual mode
        if sys.argv[1] == 'submit':
            w.restore()
            for jobid in sys.argv[2:]:
                job = w.nmdc.get_job(jobid)
                claims = job['claims']
                if len(claims) == 0:
                    print("todo")
                    sys.exit(1)
                    claim = w.nmdc.claim_job(jobid)
                    opid = claim['detail']['id']
                else:
                    opid = claims[0]['op_id']
                    j = w.find_job_by_opid(opid)
                    if j:
                        print("%s use resubmit" % (jobid))
                        continue
                w.submit(job, opid, force=True)
                w.ckpt()
        elif sys.argv[1] == 'resubmit':
            # Let's do it by activity id
            w.restore()
            for val in sys.argv[2:]:
                job = None
                if val.startswith('nmdc:sys'):
                    key = 'opid'
                else:
                    key = 'activity_id'
                for j in w.jobs:
                    jr = j.get_state()
                    if jr[key] == val:
                        job = j
                        break
                if not job:
                    print("No match found for %s" % (val))
                    continue
                if job.last_status in ["Running", "Submitted"]:
                    print("Skipping %s: %s" % (val, job.last_status))
                    continue
                job.cromwell_submit(force=True)
                jprint(job.get_state())
                w.ckpt()

        elif sys.argv[1] == 'sync':
            w.restore()
            w.update_op_state_all()
        elif sys.argv[1] == 'daemon':
            w.watch()
        elif sys.argv[1] == 'reset':
            print(w.nmdc.update_op(sys.argv[2], done=False))


if __name__ == "__main__":  # pragma: no cover
    main()
