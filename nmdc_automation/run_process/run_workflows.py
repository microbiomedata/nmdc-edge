import click
from typing import List
import logging
import os
import sys
from nmdc_automation.workflow_automation import Watcher


@click.group()
def cli():
    pass


@cli.group()
@click.option(
    "-config",
    "--config",
    "site_configuration_file",
    type=click.Path(exists=True),
    required=True,
)
@click.option(  "-jaws", "--jaws", is_flag=True, type=bool, default=False)
@click.pass_context
def watcher(ctx, site_configuration_file, jaws):
    logging_level = os.getenv("NMDC_LOG_LEVEL", logging.INFO)
    logging.basicConfig(
        level=logging_level, format="%(asctime)s %(levelname)s: %(message)s"
    )
    logger = logging.getLogger(__name__)
    logger.info(f"Initializing Watcher: config file: {site_configuration_file}")
    ctx.obj = Watcher(site_configuration_file, use_jaws=jaws)


@cli.command()
@click.pass_context
@click.argument("job_ids", nargs=-1)
def submit(ctx, job_ids):
    watcher = ctx.obj
    watcher.restore_from_checkpoint()
    for job_id in job_ids:
        job = watcher.nmdc.get_job(job_id)
        claims = job["claims"]
        if not claims:
            print("todo: Handle Empty Claims")
            sys.exit(1)
        else:
            opid = claims[0]["op_id"]
            job = watcher.find_job_by_opid(opid)
            if job:
                print(f"{job_id} use resubmit")
                continue
        watcher.submit(job, opid, force=True)
        watcher.job_checkpoint()


@cli.command()
@click.pass_context
@click.argument("workflow_execution_ids", nargs=-1)
def resubmit(ctx, workflow_execution_ids):
    watcher = ctx.obj
    # watcher.restore_from_checkpoint()
    for wf_id in workflow_execution_ids:
        logging.info(f"Checking {wf_id}")
        wfj = None
        if wf_id.startswith("nmdc:sys"):
            key = "opid"
        else:
            key = "activity_id"
        found_jobs = watcher.job_manager.job_cache
        logging.info(f"Checking {len(found_jobs)} jobs")
        for found_job in watcher.job_manager.job_cache:
            job_record = found_job.workflow.state
            logging.info(f"Checking {job_record[key]} against {wf_id}")
            if job_record[key] == wf_id:
                wfj = found_job
                break
        if not wfj:
            print(f"No match found for {wf_id}")
            continue
        if wfj.job_status in ["Running", "Submitted"]:
            print(f"Skipping {wf_id}, {wfj.last_status}")
            continue
        wfj.job.submit_job(force=True)
        watcher.job_manager.save_checkpoint()


@cli.command()
@click.pass_context
def sync(ctx):
    watcher = ctx.obj
    watcher.restore_from_checkpoint()
    watcher.update_op_state_all()


@cli.command()
@click.pass_context
def daemon(ctx):
    watcher = ctx.obj
    watcher.watch()


@cli.command()
@click.pass_context
@click.argument("opid")
def reset(ctx, opid):
    watcher = ctx.obj
    print(watcher.nmdc.update_operation(opid, done=False))


if __name__ == "__main__":
    cli()
