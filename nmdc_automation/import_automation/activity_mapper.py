import os
import sys
import re
import csv
import logging
import datetime
import pytz
import hashlib
import yaml
from itertools import zip_longest
import nmdc_schema.nmdc as nmdc
from linkml_runtime.dumpers import json_dumper
from nmdc_automation.api.nmdcapi import nmdcapi
from utils import object_action, file_link, get_md5

logger = logging.getLogger(__name__) 
runtime = nmdcapi()

class GoldMapper():
    
    def __init__(self,file_list,omics_id, yaml_file,root_directory,project_directory):
        
        with open(yaml_file, 'r') as file:
            self.import_data = yaml.safe_load(file)
        
        self.nmdc_db = nmdc.Database()
        self.file_list = file_list
        self.omics_id = omics_id
        self.root_dir = os.path.join(root_directory,omics_id)
        self.project_dir = project_directory
        self.url = "https://data.microbiomedata.org/data"
        #store object name and minted dobj id
        self.objects = {}
        self.activity_store = self.activity_imports()
        
    def object_mapper(self):    
        
        self.unique_object_mapper()
        
        self.multiple_objects_mapper()

        return self.objects
    
    def unique_object_mapper(self):
        
        for data_object_dict in self.import_data['Data Objects']['Unique']:
            for file in self.file_list:
            
                if data_object_dict == None:
                    continue
                
                elif re.search(data_object_dict['import_suffix'] ,file, re.IGNORECASE):
                        
                    activity_id = self.relate_object_by_activity_id(data_object_dict['output_of'])
                    
                    file_destination_name = object_action(file, data_object_dict['action'], activity_id, data_object_dict['nmdc_suffix'])
                    
                    activity_dir = os.path.join(self.root_dir,activity_id)
                    
                    updated_file = file_link(self.project_dir, file, activity_dir, file_destination_name)
                    
                    print('Updated File: ', updated_file)
                    
                    filemeta = os.stat(updated_file)
                    
                    md5 = get_md5(updated_file)
                    
                    dobj = runtime.minter("nmdc:DataObject")
                    
                    self.nmdc_db.data_object_set.append(
                        nmdc.DataObject(
                            file_size_bytes=filemeta.st_size,
                            name=data_object_dict['name'],
                            url=f"{self.url}/{self.omics_id}/{activity_id}/{file_destination_name}",
                            data_object_type=data_object_dict['data_object_type'],
                            type="nmdc:DataObject",
                            id=dobj,
                            md5_checksum=md5, 
                            description=data_object_dict['description'].replace("{id}", self.omics_id)
                    ))
                    
                    self.objects[data_object_dict['data_object_type']] = (data_object_dict['input_to'], [data_object_dict['output_of']], dobj)
            
    def multiple_objects_mapper(self):
        
        multiple_objects_list = []
        
        for data_object_dict in self.import_data['Data Objects']['Multiples']:
            for file in self.file_list:
                if re.search(data_object_dict['import_suffix'] ,file, re.IGNORECASE):
                    multiple_objects_list.append(file)
                    
            activity_id = self.relate_object_by_activity_id(data_object_dict['output_of'])
            
            activity_dir = os.path.join(self.root_dir,activity_id)
            
            file_destination_name = object_action(multiple_objects_list, data_object_dict['action'], activity_id, data_object_dict['nmdc_suffix'], activity_dir=activity_dir, multiple=True)
            
            print(file_destination_name)
            
            updated_file = file_link(self.project_dir, multiple_objects_list, activity_dir, file_destination_name)
            
            print(updated_file)
            
            filemeta = os.stat(updated_file)
            
            md5 = get_md5(updated_file)
            
            dobj = runtime.minter("nmdc:DataObject")
            
            self.nmdc_db.data_object_set.append(
                nmdc.DataObject(
                    file_size_bytes=filemeta.st_size,
                    name=data_object_dict['name'],
                    url=f"{self.url}/{self.omics_id}/{activity_dir}/{file_destination_name}",
                    data_object_type=data_object_dict['data_object_type'],
                    type="nmdc:DataObject",
                    id=dobj,
                    md5_checksum=md5, 
                    description=data_object_dict['description'].replace("{id}", self.omics_id)
            ))
            
            self.objects[data_object_dict['data_object_type']] = (data_object_dict['input_to'], [data_object_dict['output_of']],dobj)


    def activity_mapper(self):
        
        for workflow in self.import_data['Workflows']:
            if workflow['Type'] in self.activity_store:
                
                has_inputs_list, has_output_list = self.attach_objects_to_activity(workflow['Type'])
                #quick fix because nmdc-schema does not support [], even though raw product has none
                if len(has_inputs_list) == 0:
                    has_inputs_list = ['None']
                    
                print("Inputs List", has_inputs_list)
                print("Outputs List", has_output_list)
                
                database_activity_set = self.activity_store[workflow['Type']][0]
                
                database_activity_range = self.activity_store[workflow['Type']][1]
                
                activity_id = self.activity_store[workflow['Type']][2]
                
                database_activity_set.append(
                    database_activity_range(
                        id=activity_id, #call minter for activity type
                        name=f"Sequencing Activity for {activity_id}",
                        git_url=workflow['Git_repo'],
                        version=workflow['Version'],
                        part_of=[self.omics_id],
                        execution_resource=self.import_data['Workflow Metadata']['Execution Resource'],
                        started_at_time=datetime.datetime.now(pytz.utc).isoformat(),
                        has_input=has_inputs_list,
                        has_output=has_output_list, 
                        type=workflow['Type'],
                        ended_at_time=datetime.datetime.now(pytz.utc).isoformat(), 
                        was_informed_by=self.omics_id, 
                    ))
                    
    def activity_imports(self):
        '''Inform Object Mapping Process what activies need to be imported and distrubuted across the process'''
        
        activity_store_dict = {
            'nmdc:MetagenomeSequencing': (self.nmdc_db.metagenome_sequencing_activity_set, nmdc.MetagenomeSequencingActivity, runtime.minter("nmdc:MetagenomeSequencingActivity")),
            'nmdc:ReadQcAnalysisActivity': (self.nmdc_db.read_qc_analysis_activity_set,nmdc.MetagenomeSequencingActivity, runtime.minter("nmdc:ReadQcAnalysisActivity")),
            'nmdc:ReadBasedTaxonomyAnalysisActivity': (self.nmdc_db.read_based_taxonomy_analysis_activity_set, nmdc.ReadBasedTaxonomyAnalysisActivity, runtime.minter("nmdc:ReadBasedTaxonomyAnalysisActivity")),
            'nmdc:MetagenomeAssembly': (self.nmdc_db.metagenome_assembly_set, nmdc.MetagenomeAssembly, runtime.minter("nmdc:MetagenomeAssembly")),
            'nmdc:MetagenomeAnnotationActivity': (self.nmdc_db.metagenome_annotation_activity_set, nmdc.MetagenomeAnnotationActivity, runtime.minter("nmdc:MetagenomeAnnotationActivity")),
            'nmdc:MAGsAnalysisActivity': (self.nmdc_db.mags_activity_set, nmdc.MagsAnalysisActivity, runtime.minter("nmdc:MagsAnalysisActivity"))
        }
        
        
        for activity_config in self.import_data['Workflows']:
            if activity_config['Import'] == False:
                del activity_store_dict[activity_config['Type']]
                
        return activity_store_dict
        
    def relate_object_by_activity_id(self, output_of):
        '''Map data object to activity type and minted activity id return id'''
        
        
        return self.activity_store[output_of][2]
    
    def attach_objects_to_activity(self, activity_type):
        '''Get data objects that inform acttivity inputs and outputs'''
        
        data_object_outputs_of_list = []
        
        data_object_inputs_to_list = []
        
        for _, data_object_items in self.objects.items():
            if activity_type in data_object_items[1]:
                data_object_outputs_of_list.append(data_object_items[2])
            elif activity_type in data_object_items[0]:
                data_object_inputs_to_list.append(data_object_items[2])
                
        
        return data_object_inputs_to_list,data_object_outputs_of_list
    
    def post_nmdc_database_object(self):
        
        nmdc_database_object = json_dumper.dumps(self.nmdc_db,inject_type=False)
        res = runtime.post_objects(nmdc_database_object)
      
        return res
    
    def get_database_object_dump(self):
        
        return self.nmdc_db
    
if __name__=='__main__':

    if len(sys.argv) < 2:
        print("Usage: mapper.py <input.tsv>")
        sys.exit()
    input_tsv = sys.argv[1]
    
    logging.basicConfig(filename='processingTest.log',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)
    
    destination_root_dir = '/global/cfs/cdirs/m3408/ficus/pipeline_products'
    
    imports_yaml = "/global/cfs/cdirs/m3408/aim2/dev/refactor_23/nmdc_automation/configs/import.yaml"
    
    with open(input_tsv) as bioscales_file:
        mappings = csv.reader(bioscales_file, delimiter='\t')

        for line in mappings:
                
            gold_biosample = line[0].split(':')[-1]
            omics_processing_id = line[2]
            ga_id = line[3]
            project_path = line[4]
            files_list = [os.path.join(project_path,f) for f in os.listdir(os.path.abspath(project_path)) if os.path.isfile(os.path.join(project_path, f))]
            
            gold_mappings = GoldMapper(files_list, omics_processing_id, imports_yaml, destination_root_dir, project_path)
            
            gold_mappings.unique_object_mapper()
            gold_mappings.multiple_objects_mapper()
            gold_mappings.activity_mapper()
            db_obj = gold_mappings.get_database_object_dump()
            print(db_obj)