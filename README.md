[![CI](https://github.com/microbiomedata/nmdc_automation/actions/workflows/blt.yml/badge.svg)](https://github.com/microbiomedata/nmdc_automation/actions/workflows/blt.yml)
![Tests](./badges/tests.svg)
![Coverage](./badges/coverage.svg)


<!-- Pytest Coverage Comment:Begin -->
<!-- Pytest Coverage Comment:End -->

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
~~`nmdc_automation/run_process/run_worklfows.py` will automate job claims, job processing, and analysis record and data object submission via the nmdc runtime-api.~~
~~To submit a process that will spawn a daemon that will claim, process, and submit all jobs that have not been claimed, `cd` in to `nmdc_automation/run_process`
and run `python run_workflows.py watcher --config ../../configs/site_configuration_nersc.toml daemon`, this will watch for omics processing records that have not been claimed and processed.~~

```text
Setting up Watcher/Runner on Perlmutter:
1. After logging into nmdcda on perlmutter do ~/bin/screen.sh prod
2. /global/cfs/cdirs/m3408/squads/napacompliance
    a. check workflows.yaml
3. ./run_prod.sh or ./run.sh - pulling from nmdc and submitting to Cromwell; monitors job to see if it succeeded or failed
4. start up workers, sbatch ~/workers_perlmutter.sl
    a. sbatch -N 5 -q regular ./workers_perlmutter.sl
    b. salloc -N 1 -C cpu -q interactive -t 4:00:00
5. Cq running -> to see what jobs are still running
6. Cq meta <string> ->status of string job

Setting up Scheduler on Rancher:
1. cd /conf
2. /allow.lst is where the allow list is
3. /conf/fetch_latest_workflow_yaml.sh - fetches latest workflow from repo
4. /conf/run.sh in order to reprocess workflows.yaml
5. 'ps aux' to see what the scheduler is currently running
```

### Importing External Projects into the NMDC Database

#### Setup and Configuration
Import automation code and config files can be found
- `/global/homes/n/nmdcda/nmdc_automation/prod`
- `/global/homes/n/nmdcda/nmdc_automation/dev`

1. Get the appropriate branch latest code from the nmdc_automation repo
- in prod or dev `nmcd_automation` directory:
- switch to the branch you want to run the code from - in this case `main`
```bash
(nmdc-automation-py3.11) (base) nmdcda@perlmutter:login38:~/nmdc_automation/dev/nmdc_automation> git status
On branch main
Your branch is up to date with 'origin/main'.
```
- fetch the latest code from the branch
```bash
(nmdc-automation-py3.11) (base) nmdcda@perlmutter:login38:~/nmdc_automation/dev/nmdc_automation> git fetch origin
Unpacking objects: 100% (87/87), 27.19 KiB | 7.00 KiB/s, done.
From github.com:microbiomedata/nmdc_automation
   f313647..89b64f0  332-issues-with-rerunning-import-automation         -> origin/332-issues-with-rerunning-import-automation
(nmdc-automation-py3.11) (base) nmdcda@perlmutter:login38:~/nmdc_automation/dev/nmdc_automation> git pull
Already up to date.
```
2. Activate the nmdcda conda environment
- logged in as `nmdcda` user. Can be run in nmdcda home directory (or any other directory)
```bash
(nersc-python) nmdcda@perlmutter:login16:~> eval "$__conda_setup"
(base) nmdcda@perlmutter:login16:~>
```
3. Run `poetry install` to install the required packages
- in the `nmdc_automation` directory in the `dev` or `prod` directory
```bash
(base) nmdcda@perlmutter:login16:~/nmdc_automation/dev/nmdc_automation> poetry install
Installing dependencies from lock file

No dependencies to install or update

Installing the current project: nmdc-automation (0.1.0)
```

4. Run `poetry shell` to activate the poetry environment
```bash
(base) nmdcda@perlmutter:login16:~/nmdc_automation/dev/nmdc_automation> poetry shell
Spawning shell within /global/cfs/cdirs/m3408/nmdc_automation/dev/nmdc_automation/.venv
. /global/cfs/cdirs/m3408/nmdc_automation/dev/nmdc_automation/.venv/bin/activate
bash: __add_sys_prefix_to_path: command not found
bash: __add_sys_prefix_to_path: command not found
To load conda do: eval "$__conda_setup"
(base) nmdcda@perlmutter:login16:~/nmdc_automation/dev/nmdc_automation> . /global/cfs/cdirs/m3408/nmdc_automation/dev/nmdc_automation/.venv/bin/activate
(nmdc-automation-py3.11) (base) nmdcda@perlmutter:login16:~/nmdc_automation/dev/nmdc_automation> 
```


#### Running the Import Process

 Required files:
- import.tsv in the following format:

| nucleotide_sequencing_id | project_id | project_path |
|----------|------------|-----------|
|nmdc:omprc-11-q8b9dh63 | Ga0597031  | /path/to/project/Ga0597031 |

- import.yaml
Specifies import parameters for:
- - Workflows
```text
  - Name: Reads QC
    Import: true
    Type: nmdc:ReadQcAnalysis
    Git_repo: https://github.com/microbiomedata/ReadsQC
    Version: v1.0.14
    Collection: workflow_execution_set
    WorkflowExecutionRange: ReadQcAnalysis
    Inputs:
      - Metagenome Raw Reads
    Workflow_Execution:
      name: "Read QC for {id}"
      input_read_bases: "{outputs.stats.input_read_bases}"
      input_read_count: "{outputs.stats.input_read_count}"
      output_read_bases: "{outputs.stats.output_read_bases}"
      output_read_count: "{outputs.stats.output_read_count}"
      type: nmdc:ReadQcAnalysis
    Outputs:
      - Filtered Sequencing Reads
      - QC Statistics
```
- - Data Objects
```text
    - data_object_type: Clusters of Orthologous Groups (COG) Annotation GFF
      description: COGs for {id}
      name: GFF3 format file with COGs
      import_suffix: _cog.gff
      nmdc_suffix: _cog.gff
      input_to: [nmdc:MagsAnalysis]
      output_of: nmdc:MetagenomeAnnotation
      multiple: false
      action: rename
```
- - Workflow Metadata
```text
Workflow Metadata:
  Execution Resource: JGI
  Source URL: https://data.microbiomedata.org/data
  Root Directory: /global/cfs/cdirs/m3408/ficus/pipeline_products
```

- site_configuration.toml
- - Contains the following configurations:
```text
[credentials]
client_id = "sys0wm66"
client_secret = xxxxx
```
```text
[nmdc]
url_root = "https://data.microbiomedata.org/data/"
api_url = "http://localhost:8000"
```




