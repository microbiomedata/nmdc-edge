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
from generate_objects import get_md5
from linkml_runtime.dumpers import json_dumper
from nmdcapi import nmdcapi
# from repack import get_contigs,create_new_zip
from Utils import object_action, file_link

logger = logging.getLogger(__name__) 
runtime = nmdcapi()

class GoldMapper():
    
    def __init__(self,file_list,omics_id, yaml_file,root_directory,project_directory):
        
        with open(yaml_file, 'r') as file:
            self.import_data = yaml.safe_load(file)
        
        self.nmdc_db = nmdc.Database()
        self.file_list = file_list
        self.omics_id = omics_id
        self.root_dir = root_directory
        self.project_dir = project_directory
        self.url = "https://data.microbiomedata.org/data"
        #store object name and minted dobj id
        self.unique_objects = {}
        self.unique_object_list = []
        self.multiple_objects_lists = []
        self.activity_store = self.activity_imports()
        
    def object_mapper(self):    
        for file,data_object_dict in zip_longest(self.file_list,self.import_data['Data Objects']['Unique']):
            
            if re.search(data_object_dict['import_suffix'] ,file, re.IGNORECASE):
                    
                activity_dir = self.relate_object_by_activity_id(self.import_data[data_object_dict]['output_of'])
                
                file_destination_name = object_action(file, data_object_dict['action'])
                
                updated_file = file_link(self.project_directory, file, activity_dir, file_destination_name)
                
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
                
            self.objects[data_object_dict] = (data_object_dict['input_to'], data_object_dict['output_of'], dobj)
            
            
            multiple_objects_list = []
            
            for data_object_dict in self.import_data['Data Objects']['Multiples']:
                for file in self.file_list:
                    if re.search(data_object_dict['import_suffix'] ,file, re.IGNORECASE):
                        multiple_objects_list.append(file)
                        
                activity_dir = self.relate_object_by_activity_id(data_object_dict['output_of'])
                
                file_destination_name = object_action(multiple_objects_list, data_object_dict['action'], multiple=True)
                
                updated_file = file_link(self.project_directory, file, activity_dir, file_destination_name)
                
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
                
                self.objects[data_object_dict] = (self.import_data[data_object_dict]['input_to'], self.import_data[data_object_dict]['output_of'],dobj)

        return self.objects

    def activity_mapper(self, iteration):
        
        for workflow in self.import_data['Workflows']:
            if workflow['Type'] in self.activity_store:
                
                has_inputs_list, has_output_list = self.attach_objects_to_activity(workflow['Type'])
                
                database_activity_set = self.activity_store[workflow['Type']][0]
                
                database_activity_range = self.activity_store[workflow['Type']][1]
                
                activity_id = self.activity_store[workflow['Type']][2]
                
                database_activity_set.append(
                    database_activity_range(
                        id=activity_id, #call minter for activity type
                        name=f"Sequencing Activity for {activity_id}",
                        git_url=self.import_data[workflow]['Git_repo'],
                        version=self.import_data[workflow]['Version'],
                        part_of=[self.omics_id],
                        execution_resource=self.import_data['Executionn_resource'],
                        started_at_time=datetime.datetime.now(pytz.utc).isoformat(),
                        has_input=has_inputs_list,
                        has_output=has_output_list, 
                        type=self.import_data[workflow]['Type'],
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
      
    
if __name__=='__main__':
    #go through all the file, create an instance of each activity 
    #go through edge cases. 
    # Submit to endpoint
    
    file = 'Ga0495650_rfam.gff'
   
    first_underscore_pos = file.find('_')
    file_suffix = file[first_underscore_pos:]
    
    with open('import.yaml', 'r') as file:
        yaml_data = yaml.safe_load(file)

    # for workflow in yaml_data['Workflows']:
    #     print(workflow['Name'])
    
    for object in yaml_data['Data Objects']['Unique']:
        print(object['input_to'])