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


## Implementation

* nmdc_automation/workflow_automation/job_finder.py has most of the key logic for the runtime scheduling piece
* nmdc_automation/workflow_automation/submitter.py has a rough implementation of what would happen on the compute/cromwell side.

## Install Dependencies
To install the environment using poetry, there are a few steps to take. 
If Poetry is no installed, run:
`pip install poetry`

Once poetry is installed, you can run:
`poetry install` 

To use the environment, you can shell into the env:
`poetry shell`