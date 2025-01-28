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

The watcher is a python application which runs on a login node on Perlmutter






## Install Dependencies
To install the environment using poetry, there are a few steps to take. 
If Poetry is no installed, run:
`pip install poetry`

Once poetry is installed, you can run:
`poetry install` 

To use the environment, you can shell into the env:
`poetry shell`


## Implementation
This package is meant to be used on NMDC approvied compute instances with directories that can be accessed via https and are linked to the microbiomedata.org/data endpoint.

The main python drivers can be found in the `nmdc_automation/run_process directory` that contians two processes that require configurations to be supplied. 
 
#### Run NMDC Workflows with corresponding omics processing records
~~`nmdc_automation/run_process/run_worklfows.py` will automate job claims, job processing, and analysis record and data object submission via the nmdc runtime-api.~~
~~To submit a process that will spawn a daemon that will claim, process, and submit all jobs that have not been claimed, `cd` in to `nmdc_automation/run_process`
and run `python run_workflows.py watcher --config ../../configs/site_configuration_nersc.toml daemon`, this will watch for omics processing records that have not been claimed and processed.~~

```text
Setting up Watcher/Runner on Perlmutter:
1. Environment
    a. Ensure the watcher will not be affected when you terminal session closes 
        1. using screen: ~/bin/screen.sh prod
        2. using tmux:
        3. run watcher using nohup
2. Watcher locations on Perlmutter
    a. Production Instance:  /global/homes/n/nmdcda/nmdc_automation/prod
    b. Development Instance: /global/homes/n/nmdcda/nmdc_automation/dev
3. Updating and Running Watcher
    a. Automation code is in `nmdc_automation` under git version control - example pulling latest main:
    
    b. Initial running environment:
        1. In the nmdc_automation dir:
        source .venv/bin/activate
        poetry update
        poetry install
        poetry shell
        
    c. Invoke the Watcher:
        1. in /global/homes/n/nmdcda/nmdc_automation/ dev or prod:
        export NMDC_LOG_LEVEL=INFO    # The default is DEBUG and is very verbose
        nohup ./run.sh & or nohup ./run_prod.sh &
4. start up workers, sbatch ~/workers_perlmutter.sl
    a. sbatch -N 5 -q regular ./workers_perlmutter.sl
    b. salloc -N 1 -C cpu -q interactive -t 4:00:00
5. Cq running -> to see what jobs are still running
6. Cq meta <string> ->status of string job
7. Monitoring the Watcher:
    a. The Watcher runs on a login node of Perlmutter - the file host-prod.last indicates which node the watcher is running on
    b. ssh to that node and search for the watcher:  ps aux | grep watcher

Setting up Scheduler on Rancher:
1. cd /conf
2. /allow.lst is where the allow list is
3. /conf/fetch_latest_workflow_yaml.sh - fetches latest workflow from repo
4. /conf/run.sh in order to reprocess workflows.yaml
5. 'ps aux' to see what the scheduler is currently running
```

#### Run Workflow import for data processed by non NMDC workflows
`nmdc_automation/run_process/run_workflows.py` is designed to take in data files avilable on disk, transform them into NMDC analysis records, and submit them back to the central data store via runtime-api. This process includes minting identifers for workflow execution subclasses and data objects. Currently this process is only suitable for data processed at JGI, but with collaboration, data from other processing centers could be transformed and ingested into NMDC. 
To submit the import process, log into Perlmutter using the collaboration account. To run import in the root repository directory run `python nmdc_automation/run_process/run_import.py import-projects import.tsv configs/import.yaml configs/site_configuration.toml`, where import.tsv expects the follow format:


| nucleotide_sequencing_id | project_id | project_path |
|----------|------------|-----------|
|nmdc:omprc-11-q8b9dh63 | Ga0597031  | /path/to/project/Ga0597031 |

The following need to be set in the site_configuration.toml file: `api_url`, `url_root`, `client_id`, `client_secret`.


