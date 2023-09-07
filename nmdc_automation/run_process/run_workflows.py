import click
from typing import List
import logging
import os
import sys
from nmdc_automation.workflow_automation.watch_nmdc import Watcher


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
@click.pass_context
def watcher(ctx, site_configuration_file):
    logging_level = os.getenv("NMDC_LOG_LEVEL", logging.INFO)
    logging.basicConfig(
        level=logging_level, format="%(asctime)s %(levelname)s: %(message)s"
    )
    logger = logging.getLogger(__name__)

    ctx.obj = Watcher(site_configuration_file)


@watcher.command()
@click.pass_context
@click.argument("job_ids", nargs=-1)
def submit(ctx, job_ids):
    watcher = ctx.obj
    watcher.restore()
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


@watcher.command()
@click.pass_context
@click.argument("activity_ids", nargs=-1)
def resubmit(ctx, activity_ids):
    watcher = ctx.obj
    watcher.restore()
    for act_id in activity_ids:
        job = None
        if act_id.startswith("nmdc:sys"):
            key = "opid"
        else:
            key = "activity_id"
        for found_job in watcher.jobs:
            job_record = found_job.get_state()
            if job_record[key] == act_id:
                job = found_job
                break
        if not job:
            print(f"No match found for {act_id}")
            continue
        if job.last_status in ["Running", "Submitted"]:
            print(f"Skipping {act_id}, {job.last_status}")
            continue
        job.cromwell_submit(force=True)
        watcher.ckpt()


@watcher.command()
@click.pass_context
def sync(ctx):
    watcher = ctx.obj
    watcher.restore()
    watcher.update_op_state_all()


@watcher.command()
@click.pass_context
def daemon(ctx):
    watcher = ctx.obj
    watcher.watch()


@watcher.command()
@click.pass_context
@click.argument("opid")
def reset(ctx, opid):
    watcher = ctx.obj
    print(watcher.nmdc.update_op(opid, done=False))


if __name__ == "__main__":
    cli()
