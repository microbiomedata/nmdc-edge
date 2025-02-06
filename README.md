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

1. The node has child workflow(s) which are not scheduled or in the NMDC database
2. The required data objects for the child node exist

In this case the Scheduler will "schedule" a new job by creating a Job configuration and writing this
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
: Site-specific configuration is provided by a .toml file and defines some parameters that are used
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

1. On Rancher, go to `Deployments`, select `Production` from the clusters list, and find the Scheduler in either `nmdc` or `nmdc-dev`
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
2. Setup NMDC automation environment with `conda` and `poetry`. 
   1. load conda: eval "$__conda_setup"
   2. in the `nmdc_automation` directory: `poetry update`
   3. Install the nmdc_automation project with `poetry install`
   4. `poetry shell` to use the environment

Example setup:
```bash
(nersc-python) nmdcda@perlmutter:login38:~> pwd
/global/homes/n/nmdcda
(nersc-python) nmdcda@perlmutter:login38:~> cd nmdc_automation/dev/
(nersc-python) nmdcda@perlmutter:login38:~/nmdc_automation/dev> eval "$__conda_setup"
(base) nmdcda@perlmutter:login38:~/nmdc_automation/dev> cd nmdc_automation/
(base) nmdcda@perlmutter:login38:~/nmdc_automation/dev/nmdc_automation> poetry update
Package operations: 0 installs, 18 updates, 0 removals

  • Updating attrs (24.3.0 -> 25.1.0)
  • Updating certifi (2024.12.14 -> 2025.1.31)
  • Updating pydantic (2.10.5 -> 2.10.6)
  • Updating rdflib (7.1.2 -> 7.1.3)
  • Updating referencing (0.35.1 -> 0.36.2)
  • Updating curies (0.10.2 -> 0.10.4)
  • Updating wrapt (1.17.0 -> 1.17.2)
  • Updating deprecated (1.2.15 -> 1.2.18)
  • Updating babel (2.16.0 -> 2.17.0)
  • Updating pymdown-extensions (10.14 -> 10.14.3)
  • Updating beautifulsoup4 (4.12.3 -> 4.13.3)
  • Updating mkdocs-material (9.5.49 -> 9.6.2)
  • Updating linkml (1.8.5 -> 1.8.6)
  • Updating numpy (2.2.1 -> 2.2.2)
  • Updating pymongo (4.10.1 -> 4.11)
  • Updating tzdata (2024.2 -> 2025.1)
  • Updating nmdc-schema (11.2.1 -> 11.3.0)
  • Updating semver (3.0.2 -> 3.0.4)

Writing lock file
(base) nmdcda@perlmutter:login38:~/nmdc_automation/dev/nmdc_automation> poetry install
Installing dependencies from lock file

No dependencies to install or update

Installing the current project: nmdc-automation (0.1.0)
(base) nmdcda@perlmutter:login38:~/nmdc_automation/dev/nmdc_automation> poetry shell
Spawning shell within /global/cfs/cdirs/m3408/nmdc_automation/dev/nmdc_automation/.venv
. /global/cfs/cdirs/m3408/nmdc_automation/dev/nmdc_automation/.venv/bin/activate
(base) nmdcda@perlmutter:login38:~/nmdc_automation/dev/nmdc_automation> . /global/cfs/cdirs/m3408/nmdc_automation/dev/nmdc_automation/.venv/bin/activate
(nmdc-automation-py3.11) (base) nmdcda@perlmutter:login38:~/nmdc_automation/dev/nmdc_automation>
```
The `poetry shell` command will activate the environment for the current shell session. 
Environment (nmdc-automation-py3.11) will be displayed in the prompt.



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


