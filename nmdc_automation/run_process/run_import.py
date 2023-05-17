import click
from typing import List
import csv
import os
from nmdc_automation.import_automation.activity_mapper import GoldMapper


@click.group()
def cli():
    pass

@cli.command()
@click.argument('import_file', type=click.Path(exists=True))
@click.argument('import_yaml', type=click.Path(exists=True))
def project_import(import_file, import_yaml):
 
    with open(import_file) as bioscales_file:
        mappings = csv.reader(bioscales_file, delimiter='\t')

        for line in mappings:
                
            gold_biosample = line[0].split(':')[-1]
            omics_processing_id = line[2]
            ga_id = line[3]
            project_path = line[4]
            files_list = [os.path.join(project_path,f) for f in os.listdir(os.path.abspath(project_path)) if os.path.isfile(os.path.join(project_path, f))]
            
            gold_mappings = GoldMapper(files_list, omics_processing_id, import_yaml, project_path)
            
            gold_mappings.unique_object_mapper()
            gold_mappings.multiple_objects_mapper()
            gold_mappings.activity_mapper()
            response = gold_mappings.post_nmdc_database_object()
            print(response)
            
if __name__ == '__main__':
    cli()