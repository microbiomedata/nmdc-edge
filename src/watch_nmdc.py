#!/usr/bin/env python

from src.nmdcapi import nmdcapi
from src.config import config
from src.wfutils import job as wfjob
from time import sleep as _sleep
import json
import os
import sys
import requests
import shutil
import traceback
import jsonschema


class watcher():
    config = config()
    nmdc = nmdcapi()
    cromurl = config.conf['url']
    state_file = config.conf['agent_state']
    _POLL = 20
    _MAX_FAILS = 2

    _ALLOWED = ['Reads QC: v0.0.1']
#    _ALLOWED = ['metag-1.0.0', 'metat-1.0.0']
#    _ALLOWED = ['metag-1.0.0']

    def __init__(self):
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

    def watch(self):
        """
        The endless loop
        """
        print("Entering polling loop")
        while True:
            try:
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

                # Update op state
                # self.update_op_state()
            except Exception as e:
                print("Error")
                print(e)
                traceback.print_exc(file=sys.stdout)
            _sleep(self._POLL)

    def update_op_state(self, job):
        rec = self.nmdc.get_op(job.opid)
        if not rec['metadata'] or 'site_id' not in rec['metadata']:
            print("Corrupt op: %s" % (job.opid))
            # Botched record
            return None
        cur = rec['metadata'].get('extra')
        # Skip if nothing has changed
        if cur and cur['last_status'] == job.last_status:
            return None
        print("updating %s" % (job.opid))
        md = job.get_state()
        res = self.nmdc.update_op(job.opid, done=job.done, meta=md)
        return res

    def update_op_state_all(self):
        for job in self.jobs:
            if job.opid:
                self.update_op_state(job)

    def cromwell_list_jobs_label(self, key, value):
        query = f"label={key}:{value}&additionalQueryResultFields=labels"
        url = "%s/query?%s" % (self.cromurl, query)
        resp = requests.get(url)
        d = resp.json()
        return d

    def reconstruct_state(self, op):
        if 'job' not in op['metadata']:
            return None
        nmdc_jobid = op['metadata']['job']['id']
        # This is the remote job rec
        rj = op['metadata']['job']
        if rj['workflow']['id'] not in self._ALLOWED:
            return None
        if 'object_id' not in rj['config']:
            # Legacy.  Skip.
            return None
        # This is the input object id
        inp = rj['config']['object_id']
        obj = self.nmdc.get_object(inp, decode=True)
        url = obj['access_methods'][0]['access_url']['url']
        fn = url.split('/')[-1]
        dest = os.path.join(self.stage_dir, fn)
        mdata = obj['metadata']
        proj = mdata['proj']
        typ = mdata['type']
        # Let's try to figure out the last cromwell job
        # that ran for this data.
        cjobs = self.cromwell_list_jobs_label('project_id', proj)
        for cj in cjobs['results']:
            # If it doesn't have an activity record it is old
            act_id = cj['labels'].get('activity_id')
            if not act_id:
                continue
            # If the activity ID has this, then they are old
            if act_id.startswith('nmdc:mg0') or act_id.startswith('nmdc.mt0'):
                act_id = None
                continue
            break
        jstate = {
                "nmdc_jobid": nmdc_jobid,
                "opid": op['id'],
                "done": op['done'],
                "input": inp,
                "type": typ,
                "activity_id": act_id,
                "fn": dest,
                "cromwell_jobid": cj['id'],
                "last_status": cj['status'],
                "proj": proj
                }
        return jstate

    def find_job_by_opid(self, opid):
        for j in self.jobs:
            if j.opid == opid:
                return j
        return None

    def submit(self, njob, opid, force=False):
        wfid = njob['workflow']['id']
        # Collect some info from the object
        if 'object_id_latest' in njob['config']:
            print("Old record. Skipping.")
            return
        job = self.find_job_by_opid(opid)
        if job:
            print("Previously cached job")
            print("Reusing activity %s" % (job.activity_id))
        else:
            # Create a new job
            job = wfjob(wfid, njob['id'], njob['config'], opid,
                        activity_id=njob['config']['activity_id'])
            self.jobs.append(job)
        job.cromwell_submit(force=False)

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
#            if j['workflow']['id'] not in self._ALLOWED:
#                continue
            if jid in known:
                continue
            resp.append(j)
        return resp

    def claim_jobs(self):
        for j in self.refresh_remote_jobs():
            jid = j['id']
            if j.get('claims') and len(j.get('claims')) > 0:
                continue
            print("try to claim:" + jid)
            self.nmdc.refresh_token()

            # claim job
            claim = self.nmdc.claim_job(jid)
            if not claim['claimed']:
                self.submit(j, claim['id'])
                self.ckpt()
#                sys.exit(1)
            else:
                # Previously claimed
                opid = claim['detail']['id']
                op = self.nmdc.get_op(opid)
                print("Previously claimed.")
                print(opid, op)
                self.submit(j, opid)
                self.ckpt()

    def _load_json(self, fn):
        return json.loads(open(fn).read())

    def validate_objects(self, results):
        schemafile = os.environ.get("SCHEMA")
        if schemafile:
            schema = self._load_json(schemafile)
            try:
                jsonschema.validators.validate(results, schema)
            except jsonschema.exceptions.ValidationError as ex:
                print("Failed validation")
                print(ex)

    def fix_urls(self, dos, actid, subdir):
        root = self.config.conf['url_root'].rstrip('/')
        for do in dos:
            fn = do['url'].split('/')[-1]
            new_url = f"{root}/{actid}/{subdir}/{fn}"
            do['url'] = new_url


    def post_job_done(self, job):
        # Prepare the result record
        print("Running post for op %s" % (job.opid))
        md = job.get_metadata()
        dd = self.config.get_data_dir()
        subdir = "{directory}.{iteration}".format(**job.conf)
        outdir = os.path.join(dd, job.activity_id, subdir)
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
                    sys.stderr.write(f"ERROR: output {np} exist.  Skipping\n")
                    continue
                shutil.copyfile(v, np)
        mdf = os.path.join(outdir, "metadata.json")
        if not os.path.exists(mdf):
            json.dump(md, open(mdf, "w"))
        resp = self.nmdc.post_objects(obj)
        print(resp)
        #job.done = True
        #resp = self.nmdc.update_op(job.opid, done=True,
        #                           meta=md)
        sys.exit(1)
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
                print("%s op:%s: crom: %s %s" % (job.nmdc_jobid,
                                                 job.opid,
                                                 job.jobid,
                                                 status))


def jprint(obj):
    print(json.dumps(obj, indent=2))


def main():
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


if __name__ == "__main__":
    main()
