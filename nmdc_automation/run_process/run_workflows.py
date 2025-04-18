import click
from typing import List
import logging
import os
import sys
from nmdc_automation.workflow_automation import Watcher

logging_level = os.getenv("NMDC_LOG_LEVEL", logging.INFO)
logging.basicConfig(
    level=logging_level, format="%(asctime)s %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

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
    logger.info(f"Initializing Watcher: config file: {site_configuration_file}")
    if jaws:
        logger.info("Using JAWS")
    else:
        logger.info("Using Cromwell")
    ctx.obj = Watcher(site_configuration_file, use_jaws=jaws)


@watcher.command()
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
            job = watcher.job_manager.find_job_by_opid(opid)
            if job:
                print(f"{job_id} use resubmit")
                continue
        watcher.submit(job, opid, force=True)
        watcher.job_checkpoint()




@watcher.command()
@click.pass_context
@click.option(
    "operation_ids", "-o", "--opid", multiple=True, required=False,
    help="Operation IDs to resubmit"
    )
@click.option("--all-failures", is_flag=True, default=False, help="Resubmit all failed workflows")
@click.option("--submit", is_flag=True, default=False, help="Submit the workflows")
def resubmit(ctx, operation_ids, all_failures, submit):
    """
    Resubmit failed jobs

    If --all-failures is set, all failed jobs will be resubmitted.
    If --opid is set, the specified operation IDs will be resubmitted.
    If --submit is set, the jobs will be submitted. Otherwise, the jobs will be listed in the log output.
    """
    watcher = ctx.obj
    watcher.restore_from_checkpoint()

    if all_failures:
        logger.info("Resubmitting all failed jobs")
        failed_jobs = watcher.job_manager.get_failed_jobs()
        logger.info(f"Found {len(failed_jobs)} failed jobs")

        for job in failed_jobs:
            msg =f"Job {job.opid} for {job.was_informed_by} / {job.workflow_execution_id} Status: {job.job_status}"

            if submit:
                logger.info(f"Resubmitting {msg}")
                job.job.submit_job()
            else:
                logger.info(f"Submit flag not set. Found {msg}")

    if operation_ids:
        for opid in operation_ids:
            job = watcher.job_manager.find_job_by_opid(opid)
            if job:
                msg = f"Job for {job.was_informed_by} / {job.workflow_execution_id} Status: {job.job_status}"
                if submit:
                    logger.info(f"Resubmitting {msg}")
                    job.job.submit_job()
                else:
                    logger.info(f"Submit flag not set. Found {msg}")

    logger.info("Saving checkpoint")
    watcher.job_manager.save_checkpoint()


@watcher.command()
@click.pass_context
def sync(ctx):
    # TODO: Implement sync
    pass


@watcher.command()
@click.pass_context
def daemon(ctx):
    watcher = ctx.obj
    watcher.watch()


@watcher.command()
@click.pass_context
def report(ctx):
    watcher = ctx.obj
    watcher.restore_from_checkpoint()

    reports = watcher.job_manager.report()

    header = "wdl, release, last_status, was_informed_by, workflow_execution_id"
    print(header)
    for rpt in reports:
        print(f"{rpt['wdl']}, {rpt['release']}, {rpt['last_status']}, {rpt['was_informed_by']}, {rpt['workflow_execution_id']}")



@watcher.command()
@click.pass_context
@click.argument("opid")
def reset(ctx, opid):
    watcher = ctx.obj
    print(watcher.nmdc.update_operation(opid, done=False))


if __name__ == "__main__":
    cli()
