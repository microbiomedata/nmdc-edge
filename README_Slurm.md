
# nmdc_automation: Running Jobs on SLURM and Condor
This document provides instructions for running jobs on SLURM and Condor using the nmdc_automation package. It includes examples of how to submit jobs, check their status, and retrieve results.

#### Provision Workers

1. `sbatch ~/workers_perlmutter.sl`

- `sbatch` is the command to submit a job to the Slurm scheduler
- `~/workers_perlmutter.sl` is the script that will be run by the scheduler which specifies the number of workers to provision

```bash
#!/bin/sh
#SBATCH -N 1
#SBATCH -q regular
#SBATCH -t 12:00:00
#SBATCH -J nmdc_condor_wrk
#SBATCH -C cpu
```

#### Monitoring Jobs

##### Slurm and Condor

- `sqs` Shows the Slurm queue
```shell
JOBID            ST USER      NAME          NODES TIME_LIMIT       TIME  SUBMIT_TIME          QOS             START_TIME           FEATURES       NODELIST(REASON)
35153609         PD nmdcda    condor        1     14-00:00:00       0:00  2025-01-23T09:33:27  workflow        N/A                  cron           (Dependency)   
35153610         R  nmdcda    cromwell      1     4-00:00:00 3-11:09:43  2025-02-08T22:07:23  workflow        2025-02-08T22:08:01  cron           login05        
30091486         R  nmdcda    condor        1     14-00:00:00 11-11:13:11  2025-01-27T09:09:48  workflow        2025-01-31T22:04:33  cron           login04
```
Shows a new job with ID 35153609 in the queue (Pending State), and a running job with ID 35153610
- `cq running` Shows which jobs are being run by Condor
```shell
7d07b3e5-edb2-414f-ba19-c570669f3b5f  f_annotate     65ce4da9-52eb-4d74-82e1-9b2b639e694a  65ce4da9-52eb-4d74-82e1-9b2b639e694a  Running   2024-03-27T00:02:34.316Z
```

##### Watcher State File

The watcher maintains a state file with job configuration, metadata and status information. The location of the 
state file is defined in the site configuration file. For dev this location is:
`/global/cfs/cdirs/m3408/var/dev/agent.state`

Example State File Entry:
<details
><summary>Example State File Entry</summary>

```json
{
      "workflow": {
        "id": "Metagenome Assembly: v1.0.9"
      },
      "created_at": "2025-03-06T18:19:43",
      "config": {
        "git_repo": "https://github.com/microbiomedata/metaAssembly",
        "release": "v1.0.9",
        "wdl": "jgi_assembly.wdl",
        "activity_id": "nmdc:wfmgas-12-k8dxr170.1",
        "activity_set": "workflow_execution_set",
        "was_informed_by": "nmdc:omprc-11-sdyccb57",
        "trigger_activity": "nmdc:wfrqc-12-dvn15085.1",
        "iteration": 1,
        "input_prefix": "jgi_metaAssembly",
        "inputs": {
          "input_files": "https://data.microbiomedata.org/data/nmdc:omprc-11-sdyccb57/nmdc:wfrqc-12-dvn15085.1/nmdc_wfrqc-12-dvn15085.1_filtered.fastq.gz",
          "proj": "nmdc:wfmgas-12-k8dxr170.1",
          "shortRead": false
        },
        "input_data_objects": [],
        "activity": {},
        "outputs": []
      },
      "claims": [],
      "opid": "nmdc:sys0z232qf64",
      "done": true,
      "start": "2025-03-06T19:24:52.176365+00:00",
      "cromwell_jobid": "0b138671-824d-496a-b681-24fb6cb207b3",
      "last_status": "Failed",
      "nmdc_jobid": "nmdc:9380c834-fab7-11ef-b4bd-0a13321f5970",
      "failed_count": 3
    }
```

</details>

Similar to a `jobs` record, with these additional things to note:
- `done` is a boolean indicating if the job is complete
- `cromwell_jobid` is the job ID from the Cromwell service
- `last_status` is the last known status of the job - this is updated by the watcher
- `failed_count` is the number of times the job has failed

##### Cromwell Job Status and Metadata

With the cromwell_jobid, you can query the Cromwell service for the status of the job - the Cromwell service URL is
defined in the site configuration file.

```shell
curl --netrc https://nmdc-cromwell.freeddns.org:8443/api/workflows/v1/0b138671-824d-496a-b681-24fb6cb207b3/status
{"status":"Failed","id":"0b138671-824d-496a-b681-24fb6cb207b3"}
```
Job Metadata can be found in the Cromwell service by querying the metadata endpoint

```shell
curl --netrc https://nmdc-cromwell.freeddns.org:8443/api/workflows/v1/0b138671-824d-496a-b681-24fb6cb207b3/metadata
```
This will include the inputs, outputs and logs for the job, as well as failure information if the job failed.
```json
{
     "status": "Failed",
  "failures": [
    {
      "causedBy": [
        {
          "causedBy": [],
          "message": "Failed to evaluate input 'input_files' (reason 1 of 1): No coercion defined from '\"https://data.microbiomedata.org/data/nmdc:omprc-11-sdyccb57/nmdc:wfrqc-12-dvn15085.1/nmdc_wfrqc-12-dvn15085.1_filtered.fastq.gz\"' of type 'spray.json.JsString' to 'Array[File]'."
        }
      ],
      "message": "Workflow input processing failed"
    }
  ]
}
```

