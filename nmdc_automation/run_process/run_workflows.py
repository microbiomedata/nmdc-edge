import click
from typing import List
import logging
import os
import sys
from nmdc_automation.workflow_automation.watch_nmdc_dev import Watcher


@click.group()
def cli():
    pass

@cli.command()
@click.argument('site_configuration_file', type=click.Path(exists=True))
def watcher(site_configuration_file):
    
    logging_level = os.getenv('NMDC_LOG_LEVEL', logging.INFO)
    logging.basicConfig(level=logging_level, format='%(asctime)s %(levelname)s: %(message)s')
    logger = logging.getLogger(__name__)
    
    watcher = Watcher(site_configuration_file)

    @click.command()
    @click.argument('job_ids', nargs=-1)
    def submit(job_ids):
        watcher.restore()
        for job_id in job_ids:
            job = watcher.nmdc.get_job(job_id)
            claims = job['claims']
            if not claims:
                logger.error("todo: Handle Empty Claims")
                sys.exit(1)
            else:
                opid = claims[0]['op_id']
                job = watcher.find_job_by_opid(opid)
                if job:
                    print(f"{job_id} use resubmit")
                    continue
            watcher.submit(job, opid, force=True)
            watcher.job_checkpoint()

    @click.command()
    @click.argument('activity_ids', nargs=-1)
    def resubmit(activity_ids):
        watcher.restore()
        for act_id in activity_ids:
            job = None
            if act_id.startswith('nmdc:sys'):
                key = 'opid'
            else:
                key = 'activity_id'
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


    @click.command()
    def sync():
        watcher.restore()
        watcher.update_op_state_all()

    @click.command()
    def daemon():
        watcher.watch()

    @click.command()
    @click.argument('opid')
    def reset(opid):
        print(watcher.nmdc.update_op(opid, done=False))

    cli.add_command(submit)
    cli.add_command(resubmit)
    cli.add_command(sync)
    cli.add_command(daemon)
    cli.add_command(reset)


if __name__ == '__main__':
    cli()