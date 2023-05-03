import os
import sys
import re
import csv
import logging
import datetime
import pytz
import hashlib
import yaml
import nmdc_schema.nmdc as nmdc
from generate_objects import get_md5
from linkml_runtime.dumpers import json_dumper
from nmdcapi import nmdcapi
# from repack import get_contigs,create_new_zip
import zipfile

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
        self.objects = {}
        
        self.activity_store=1
        
    def object_mapper(self):    
        for file,data_object_name in zip(self.file_list,self.import_data['Data Objects']):
            
            if re.search(self.import_data[data_object_name]['suffix'] ,file, re.IGNORECASE):
                
                raw_reads = os.path.basename(file)
                
                filemeta = os.stat(file)
                
                md5 = get_md5(file)
                
                dobj = runtime.minter("nmdc:DataObject")
                
                os.makedirs(raw_dir,exist_ok=True)
                
                os.link(file, os.path.join(raw_dir, raw_reads))
                
                self.nmdc_db.data_object_set.append(
                    nmdc.DataObject(
                        file_size_bytes=filemeta.st_size,
                        name="Raw sequencer read data",
                        url=f"{self.url}/{self.omics_id}/{raw_id}/{raw_reads}",
                        data_object_type="Metagenome Raw Reads",
                        type="nmdc:DataObject",
                        id=dobj,
                        md5_checksum=md5, 
                        description=f"Metagenome Raw Reads for {self.omics_id}"
                ))
                
            self.objects[data_object_name] = dobj
        
        return self.objects

    def activity_mapper(self, iteration):
        
        nmdc_destination_dir = f'{self.root_dir}/{self.omics_id}/{raw_id}'
        
        nmdc_file_id = activity_id.replace(':','_')
        
        database_activity_set = self.activity_store[moniker][0]
        
        database_activity_range = self.activity_store[moniker][1]
        
        database_activity_set.append(
            database_activity_range(
                id=activity_id, #call minter for activity type
                name=f"Sequencing Activity for {activity_id}",
                git_url=self._raw_git_url,
                version="v1.0.0",#get version
                part_of=[activity_id],
                execution_resource=self.import_data['Executionn_resource'], #ask at sync
                started_at_time=datetime.datetime.now(pytz.utc).isoformat(), #command to generate time now
                has_input='None', #mapping to raw reads
                has_output=map_objects, #nmdc: + md5sum of qc filter and qc report
                type="nmdc:MetagenomeSequencing", #can keep this
                ended_at_time=datetime.datetime.now(pytz.utc).isoformat(), #function to generate end time
                was_informed_by=self.omics_id, #gold id
            ))
                    
    def activity_imports(self):
        
        activty_store_dict = {
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
        
                                        
    def mags_mapper(self,inputs):
        mag_id = mint_id('wfmag') + '.1'
        # hash_mag_id = hash_type_string(mag_id)
        mag_file_id = mag_id.replace(':','_')
        dobj_bin = mint_id('dobj')
        mag_directory = f'{self.root_dir}/{self.omics_id}/{mag_id}'
        mag_url = f'{self.url}/{self.omics_id}/{mag_id}'
        output_objects = []
        bins_list = []
        for file in self.file_list:
            if re.search('_[0-9]+.tar.gz', file, re.IGNORECASE) and not re.search('chaff.tar.gz',file, re.IGNORECASE):
                bins_list.append(file)
            else:
                logger.debug(f'{file} not an instance of acceptable nmdc mags file')
                
        #zip tar files for project
        nmdc_mag_tar = mag_file_id + '_hqmq_bin.zip'
        with zipfile.ZipFile(os.path.join(self.project_dir,nmdc_mag_tar),'w') as zip:
            for bin in bins_list:
                zip.write(bin, os.path.basename(bin),compress_type=zipfile.ZIP_DEFLATED)
        file = os.path.join(self.project_dir,nmdc_mag_tar)
        self.file_handler(file, nmdc_mag_tar, mag_directory)
        filemeta = os.stat(os.path.join(mag_directory,nmdc_mag_tar))
        md5_mags_tar = get_md5(os.path.join(mag_directory,nmdc_mag_tar))
        output_objects.append(dobj_bin)
        self.nmdc_db.data_object_set.append(
            nmdc.DataObject(
                file_size_bytes=filemeta.st_size,
                name=f"Metagenome bins contigs fasta",
                url=f"{mag_url}/{nmdc_mag_tar}",
                data_object_type="Metagenome Bins",
                type="nmdc:DataObject",
                id=dobj_bin, 
                md5_checksum=md5_mags_tar, 
                description=f"Metagenome Bins for {mag_id}"
        ))
                
                
        self.nmdc_db.mags_activity_set.append(
                nmdc.MagsAnalysisActivity(
                    id=mag_id,
                    name=f"MAGs Activity for {mag_id}",
                    git_url=self._mags_git_url,
                    version=self._mags_version,
                    part_of=[mag_id],
                    execution_resource="JGI",
                    started_at_time=datetime.datetime.now(pytz.utc).isoformat(),
                    has_input=inputs,
                    has_output=output_objects, 
                    type="nmdc:MagsAnalysisActivity",
                    ended_at_time=datetime.datetime.now(pytz.utc).isoformat(),
                    was_informed_by=self.omics_id,
                ))
                
        return self.nmdc_db
    
    def file_handler(self,original_file, updated_file, destination_dir):
        try:
            os.makedirs(destination_dir)
        except FileExistsError:
            logger.debug(f'{destination_dir} already exists')
        
        original_path = os.path.join(self.project_dir,original_file)
        linked_path = os.path.join(destination_dir,updated_file)
        try:
            os.link(original_path, linked_path)
        except FileExistsError:
            logger.info(f'{linked_path} already exists')
    
            
def hash_type_string(minted_id):
    return hashlib.md5(minted_id.encode('utf-8')).hexdigest() 
    
    
if __name__=='__main__':
    #go through all the file, create an instance of each activity 
    #go through edge cases. 
    # Submit to endpoint
    
    file = 'Ga0495650_rfam.gff'
   
    first_underscore_pos = file.find('_')
    file_suffix = file[first_underscore_pos:]
    
    with open('import.yaml', 'r') as file:
        yaml_data = yaml.safe_load(file)

    # for second_key in yaml_data['Data Objects']:
    #     if file_suffix == yaml_data['Data Objects'][second_key]['suffix']:
    #         print(yaml_data['Data Objects'][second_key]['suffix'])
    #         print(yaml_data['Data Objects'][second_key]['name'])
    
    activty_store_dict = {
            'nmdc:MetagenomeSequencing': ('dkaj', runtime.minter("nmdc:MetagenomeSequencingActivity")),
            'nmdc:ReadQcAnalysisActivity': ('dkfaddf', runtime.minter("nmdc:ReadQcAnalysisActivity")),
            'nmdc:ReadBasedTaxonomyAnalysisActivity': ('fjkadsfdj', runtime.minter("nmdc:ReadBasedTaxonomyAnalysisActivity")),
            'nmdc:MetagenomeAssembly': ('dfjadkf', runtime.minter("nmdc:MetagenomeAssembly")),
            'nmdc:MetagenomeAnnotationActivity': ('fkadfjad', runtime.minter("nmdc:MetagenomeAnnotationActivity")),
            'nmdc:MAGsAnalysisActivity': ('kdfjkads', runtime.minter("nmdc:MagsAnalysisActivity"))
        }
        
        
    for activity_config in yaml_data['Workflows']:
        if activity_config['Import'] == False:
            del activity_store_dict[activity_config['Type']]

    print(activity_store_dict)

    # if re.search(yaml_data['Data Objects'][]['suffix'] ,file, re.IGNORECASE):
    #     yaml_data['Data Objects']['suffix']