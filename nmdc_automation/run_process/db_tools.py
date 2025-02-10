"""
DB Tools.
"""
import click
import logging

from nmdc_automation.api import NmdcRuntimeApi


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    pass


@cli.command()
@click.argument("config_file", type=click.Path(exists=True))
@click.option("--update-db", default=False, type=bool, help="Update the database")
def update_zero_size_files(config_file, update_db):
    logger.info(f"Updating zero size files from {config_file}")

    runtime = NmdcRuntimeApi(config_file)
