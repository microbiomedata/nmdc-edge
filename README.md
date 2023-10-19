# nmdc_automation

## Goal

Demonstrate how the various stages of a series of workflows could
be tracked and triggered by the runtime.

## Approach

The workflows are defined in a YAML file.  This describes the
following for each workflow

* Name
* Git Repo associated with the workflow
* Version: The current active version that should be run
* WDL: The "top-level" WDL that should be run
* Input Prefix: The string that should be prefixed to all of the inputs.
                This is a workaround because Mongo doesn't like dots in key names
* Inputs: The array of inputs for the workflow.  Not it doesn't deal with nested structures yet.

The main scheduling loop does the following:

1. For each workflow, it gathers up all jobs and activities that match the current
   repo and version.  This basically to figure out what is in-flight or completed that
   matches the current release.  These records also include the trigger object that
   initiated the previous jobs.
2. Using the trigger object type find all objects that could be processed.
3. See if the trigger object exist in the query from step 1.  Anything missing will 
   generate a new job.
4. Generate a job record for each object.  Use the workflow spec to populate the inputs.

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
`nmdc_automation/run_process/run_worklfows.py` will automate job claims, job processing, and analysis record and data object submission via the nmdc runtime-api.
To submit a process that will spawn a daemon that will claim, process, and submit all jobs that have not been claimed, `cd` in to `nmdc_automation/run_process`
and run `python run_workflows.py watcher --config ../../configs/site_configuration_nersc.toml daemon`, this will watch for omics processing records that have not been claimed and processed. 

#### Run Workflow import for data processed by non NMDC workflows
`nmdc_automation/run_process/run_worklfows.py` is designed to take in data files avilable on disk, transform them into NMDC analysis records, and submit them back to the central data store via runtime-api. Currently this process is only suitable for data processed at JGI, but with collaboration, data from other processing centers could be transformed and ingested into NMDC. 
To submit the import process, `cd` in `nmdc_automation/run_process` and run `python run_import.py project-import import.tsv ../../configs/import.yaml`, where import.tsv expects the follow format:

`
omics_id | project_id | directory
----------------------------------------------------------------
nmdc:omprc-11-q8b9dh63 Ga0597031 /global/cfs/cdirs/m3408/aim2/dev/bioscales_mapping/neon_analysis_projects/Ga0597031
`

