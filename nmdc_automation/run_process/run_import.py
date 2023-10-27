import click
from typing import List
import csv
import os
from nmdc_automation.import_automation import GoldMapper


@click.group()
def cli():
    pass


@cli.command()
@click.argument("import_file", type=click.Path(exists=True))
@click.argument("import_yaml", type=click.Path(exists=True))
@click.argument("site_configuration", type=click.Path(exists=True))
@click.option("--iteration", default=1, type=str, help="Number of iterations")
def project_import(import_file, import_yaml, site_configuration, iteration):
    with open(import_file) as bioscales_file:
        mappings = csv.reader(bioscales_file, delimiter="\t")

        for line in mappings:
            omics_processing_id = line[0]
            project_path = line[3]
            files_list = [
                os.path.join(project_path, f)
                for f in os.listdir(os.path.abspath(project_path))
                if os.path.isfile(os.path.join(project_path, f))
            ]

            gold_mappings = GoldMapper(
                iteration,
                files_list,
                omics_processing_id,
                import_yaml,
                project_path,
                site_configuration,
            )

            gold_mappings.unique_object_mapper()
            # gold_mappings.multiple_objects_mapper()
            gold_mappings.activity_mapper()
            response = gold_mappings.post_nmdc_database_object()
            print(response)
            print(f"processed {omics_processing_id}")


if __name__ == "__main__":
    cli()
