[![CI](https://github.com/microbiomedata/nmdc_automation/actions/workflows/blt.yml/badge.svg)](https://github.com/microbiomedata/nmdc_automation/actions/workflows/blt.yml)
![Tests](./badges/tests.svg)
![Coverage](./badges/coverage.svg)


<!-- Pytest Coverage Comment:Begin -->
<!-- Pytest Coverage Comment:End -->

# nmdc_automation

An automation framework for running sequential metagenome analysis jobs and making the outputs
available as metadata in the NMDC database, and data objects on the NMDC data portal.

## Overview

### System Components


Scheduler
: The Scheduler polls the NMDC database based upon an `Allowlist` of DataGeneration IDs. Based on an allowed 
data-generation ID, the scheduler examines WorkflowExecutions and DataObjects that `was_informed_by` by the 
data generation, and builds a graph of `Workflow Process Nodes`. When the scheduler finds a node where:
: 1. The node has child workflow(s) which are not scheduled or in the NMDC database
: 2. The required data objects for the child node exist
: In this case the Scheduler will "schedule" a new job by creating a Job configuration and writing this
to the `jobs` collection in the NMDC database

Watcher
: The Watcher "watches" the `jobs` table in the NMDC database looking for unclaimed jobs. If found, the 
Watcher will create a `WorkflowJob` to manage the analysis job.  The watcher will then periodically poll
each workflow job for it's status and process successful or failed jobs when they are complete

WorkflowJob
: A `WorkflowJob` consists of a `WorkflowStateManager` and a `JobRunner` and is responsible for preparing the 
required inputs for an analysis job, submitting it to the job running service (e.g., J.A.W.S, Cromwell) and 
for processing the resulting data and metadata when the job completes.  The watcher maintains a record of it's
current activity in a `State File`

### System Configuration

Site Config
: Site-specific configuration if provided by a .toml file and defines some parameters that are used
across the workflow process including

1. URL and credentials for NMDC API
2. Staging and Data filesystem locations for the site
3. Job Runner service URLs
4. Path to the state file

Workflow Definitions
: Workflow definitions in a .yaml file describing each analysis step, specifying:

1. Name, type, version, WDL and git repository for each workflow
2. Inputs, Outputs and Workflow Execution steps
3. Data Object Types, description and name templates for processing workflow output data

---

## Instructions (for NERSC / Perlmutter environment)


### Running the Scheduler

The Scheduler is a Dockerized application running on [Rancher](https://rancher2.spin.nersc.gov). 
To initialize the Scheduler for new DataGeneration IDs, the following steps:

1. On Rancher, go to `Deployments` and find the Scheduler in either `nmdc` or `nmdc-dev`
2. Click on the Scheduler and select `run shell`
3. In the shell, `cd /conf`
4. Update the file `allow.lst` with the Data Generation IDs that you want to schedule
   1. Copy the list of data-generation IDs to you clipboard
   2. In the shell, delete the existing allow list `rm allow.lst`
   3. Replace the file with your copied list:
      1. `cat >allow.lst`
      2. Paste your IDs `command-v`
      3. Ensure a blank line at the end with a `return` 
      4. Terminate cat `control-d`
5. Recommended to set the log level to INFO or you get a *very* large log output
   1. `export NMDC_LOG_LEVEL=INFO`
6. Restart the scheduler.  In the shell, in /conf:  `./run.sh`
7. Ensure the scheduler is running by checking `sched.log`


### Running the Watcher

The watcher is a python application which runs on a login node on Perlmutter. 
The following instructions all assume the user is logged in as user `nmdcda@perlmutter.nersc.gov`

1. Get an ssh key - in your home directory: `./sshproxy.sh -u <your_nersc_username> -c nmdcda`
2. Log in using the key `ssh -i .ssh/nmdcda nmdcda@perlmutter.nersc.gov`

Watcher code and config files can be found 
- `/global/homes/n/nmdcda/nmdc_automation/prod`
- `/global/homes/n/nmdcda/nmdc_automation/dev`

#### Set-Up and Configuration

1. Ensure you have the latest `nmdc_automation` code.
   1. `cd nmdc_automation`
   2. `git status` / `git switch main` if not on main branch
   3. `git fetch origin`
   4. `git pull`
2. Start initial virtual environment including `poetry`
   1. in the nmdc_automation dir: `source .venv/bin/activate`
   2. if .venv does not exist: `virtualenv .venv`
3. Install the nmdc_automation project with `poetry install`
4. `poetry shell` to use the environment

#### Running the Watcher

We run the watcher using `nohup` (No Hangup) - this prevents the watcher process from being terminated
when the user's terminal session ends.  This will cause stdout and stderr to be written to a file
names `nohup.out` in addition to being written to the `watcher.log` file.  

1. change to the working `prod` or `dir` directory
2. `export NMDC_LOG_LEVEL=INFO`
3. `rm nohup.out`
4. `nohup ./run.sh &` OR `nohup ./run_prod.sh &`

#### Provision Workers

1. `sbatch ~/workers_perlmutter.sl`

#### Monitoring the Watcher

1. The watcher writes a file `host-prod.last` showing which node it is running on
2. ssh to that node
3. Search for the Watcher process `ps aux | grep watcher`

#### Monitoring Jobs

- `sqs` Shows the Slurm queue
- `cq running` Shows which jobs are being run by Condor



#### Run Workflow import for data processed by non NMDC workflows
`nmdc_automation/run_process/run_workflows.py` is designed to take in data files avilable on disk, transform them into NMDC analysis records, and submit them back to the central data store via runtime-api. This process includes minting identifers for workflow execution subclasses and data objects. Currently this process is only suitable for data processed at JGI, but with collaboration, data from other processing centers could be transformed and ingested into NMDC. 
To submit the import process, log into Perlmutter using the collaboration account. To run import in the root repository directory run `python nmdc_automation/run_process/run_import.py import-projects import.tsv configs/import.yaml configs/site_configuration.toml`, where import.tsv expects the follow format:


| nucleotide_sequencing_id | project_id | project_path |
|----------|------------|-----------|
|nmdc:omprc-11-q8b9dh63 | Ga0597031  | /path/to/project/Ga0597031 |

The following need to be set in the site_configuration.toml file: `api_url`, `url_root`, `client_id`, `client_secret`.


