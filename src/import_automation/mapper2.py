import io
import os
import sys
import re
import csv
import json
import logging
import datetime
import pytz
import hashlib
import shutil
import multiprocessing
import nmdc_schema.nmdc as nmdc
from generate_objects import get_md5
from linkml_runtime.dumpers import json_dumper
from src.nmdcapi import nmdcapi
# from repack import get_contigs,create_new_zip
import zipfile

logger = logging.getLogger(__name__) 
runtime = nmdcapi()


class GoldMapper():
    
    def __init__(self,file_list,gold_id,root_directory,project_directory):
        #id -- > gold id
        ##gold id should be omics_processing_record
        self.nmdc_db = nmdc.Database()
        self.file_list = file_list
        self.gold_id = gold_id
        self.root_dir = root_directory
        self.project_dir = project_directory
        self.url = "https://data.microbiomedata.org/data"
        #my responsibility is to generate the activit ids with the minting service, ~ .1 for JGI
        
    def parse_data_objects(self):    
        objects = []
        for file in self.file_list:
            if re.search('fastq.gz',file,re.IGNORECASE) and not re.search('filter-METAGENOME.fastq.gz',file, re.IGNORECASE) and not re.search('input.corr.fastq.gz',file,re.IGNORECASE):
                raw_reads = os.path.basename(file)
                filemeta = os.stat(file)
                md5 = get_md5(file)
                dobj = mint_id('dobj')
                os.makedirs(raw_dir,exist_ok=True)
                os.link(file, os.path.join(raw_dir, raw_reads))
                objects.append(dobj)
                self.nmdc_db.data_object_set.append(
                    nmdc.DataObject(
                        file_size_bytes=filemeta.st_size,
                        name="Raw sequencer read data",
                        url=f"{self.url}/{self.gold_id}/{raw_id}/{raw_reads}",
                        data_object_type="Metagenome Raw Reads",
                        type="nmdc:DataObject",
                        id=dobj,
                        md5_checksum=md5, 
                        description=f"Metagenome Raw Reads for {self.gold_id}"
                ))
        return objects

    def sequencing_mapper(self):
        raw_id = mint_id('wfraw') + '.1'
        print(raw_id)
        raw_dir = f'{self.root_dir}/{self.gold_id}/{raw_id}'
        print(raw_dir)
        # hash_raw_id = hash_type_string(raw_id)
        
        self.nmdc_db.metagenome_sequencing_activity_set.append(
                    nmdc.MetagenomeSequencingActivity(
                        id=raw_id, #call minter for activity type
                        name=f"Sequencing Activity for {raw_id}",
                        git_url=self._raw_git_url,
                        version="v1.0.0",#get version
                        part_of=[raw_id],
                        execution_resource="JGI", #ask at sync
                        started_at_time=datetime.datetime.now(pytz.utc).isoformat(), #command to generate time now
                        has_input='None', #mapping to raw reads
                        has_output=output_objects, #nmdc: + md5sum of qc filter and qc report
                        type="nmdc:MetagenomeSequencing", #can keep this
                        ended_at_time=datetime.datetime.now(pytz.utc).isoformat(), #function to generate end time
                        was_informed_by=self.gold_id, #gold id
                    ))
                    
        return [dobj_raw]
        
    def read_qc_mapper(self,inputs):
        #set repeated variables
        rqc_id = mint_id('wfrqc') + '.1'
        # hash_rqc_id = hash_type_string(rqc_id)
        rqc_file_id = rqc_id.replace(':','_')
        rqc_directory = f'{self.root_dir}/{self.gold_id}/{rqc_id}'
        rqc_url = f'{self.url}/{self.gold_id}/{rqc_id}'
        
        self.nmdc_db.read_qc_analysis_activity_set.append(
                    nmdc.ReadQcAnalysisActivity(
                        id=rqc_id,
                        name=f"Read QC Activity for {rqc_id}",
                        git_url=self._rqc_git_url,
                        version=self._rqc_version,
                        part_of=[rqc_id], #can get rid of this
                        execution_resource="JGI",
                        started_at_time=datetime.datetime.now(pytz.utc).isoformat(), #command to generate time now
                        has_input=inputs, 
                        has_output=output_objects, 
                        type="nmdc:ReadQCAnalysisActivity", #can keep this
                        ended_at_time=datetime.datetime.now(pytz.utc).isoformat(), #function to generate end time
                        was_informed_by=self.gold_id, #omic
                    ))
        
        return [dobj_filter]
            
    def assembly_mapper(self,inputs):
        asm_id = mint_id('wfasm') + '.1'
        # hash_asm_id = hash_type_string(asm_id)
        asm_file_id = asm_id.replace(':','_')
        asm_directory = f'{self.root_dir}/{self.gold_id}/{asm_id}'
        asm_url = f'{self.url}/{self.gold_id}/{asm_id}'
        output_objects = []
                
        self.nmdc_db.metagenome_assembly_set.append(
                nmdc.MetagenomeAssembly(
                    id=asm_id,
                    name=f"Metagenome Assembly Activity for {asm_id}",
                    git_url=self._asm_git_url,#not sure about this
                    part_of=[f"{asm_id}"],
                    version=self._asm_version,
                    execution_resource="JGI", #ask at sync
                    started_at_time=datetime.datetime.now(pytz.utc).isoformat(), #command to generate time now
                    has_input=inputs, #filtered reads
                    has_output=output_objects, #nmdc: + md5sum of qc filter and qc report
                    type="nmdc:MetagenomeAssembly", #can keep this
                    ended_at_time=datetime.datetime.now(pytz.utc).isoformat(), #function to generate end time
                    was_informed_by=self.gold_id, #gold id
                ))
                
        return [dobj_contigs,dobj_bam]
                
                
    def annotation_mapper(self,inputs):
        ann_id = mint_id('wfann') + '.1'
        # hash_ann_id = hash_type_string(ann_id)
        ann_file_id = ann_id.replace(':','_')
        ann_directory = f'{self.root_dir}/{self.gold_id}/{ann_id}'
        ann_url = f'{self.url}/{self.gold_id}/{ann_id}'
                
        self.nmdc_db.metagenome_annotation_activity_set.append(
                nmdc.MetagenomeAnnotationActivity(
                    id=ann_id,
                    name=f"Annotation Activity for {ann_id}",
                    git_url=self._ann_git_url,#not sure about this
                    version=self._ann_version,
                    part_of=[ann_id],
                    execution_resource="JGI", #ask at sync
                    started_at_time=datetime.datetime.now(pytz.utc).isoformat(), #command to generate time now
                    has_input=inputs, #assembly contigs
                    has_output=output_objects, #nmdc: + md5sum of qc filter and qc report
                    type="nmdc:MetagenomeAnnotationActivity", #can keep this
                    ended_at_time=datetime.datetime.now(pytz.utc).isoformat(), #function to generate end time
                    was_informed_by=self.gold_id, #gold id
                ))
                
        return [dobj_functional_gff]
                
    def mags_mapper(self,inputs):
        mag_id = mint_id('wfmag') + '.1'
        # hash_mag_id = hash_type_string(mag_id)
        mag_file_id = mag_id.replace(':','_')
        dobj_bin = mint_id('dobj')
        mag_directory = f'{self.root_dir}/{self.gold_id}/{mag_id}'
        mag_url = f'{self.url}/{self.gold_id}/{mag_id}'
        output_objects = []
        bins_list = []
        for file in self.file_list:
            if re.search('_[0-9].tar.gz', file, re.IGNORECASE) and not re.search('chaff.tar.gz',file, re.IGNORECASE):
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
                    was_informed_by=self.gold_id,
                ))
                
        return self.nmdc_db
    
    def file_handler(self,original_file, updated_file, destination_dir):
        try:
            os.makedirs(destination_dir)
        except FileExistsError:
            logger.debug(f'{destination_dir} already exists')
        # try:
        #     shutil.copy(os.path.join(self.project_dir,original_file), os.path.join(self.project_dir,updated_file))
        # except shutil.SameFileError:
        #     pass
            
        original_path = os.path.join(self.project_dir,original_file)
        linked_path = os.path.join(destination_dir,updated_file)
        try:
            os.link(original_path, linked_path)
        except FileExistsError:
            logger.info(f'{linked_path} already exists')
    
    
def mint_id(type_code):
    if type_code == 'wfraw':
        return runtime.call_minter("nmdc:MetagenomeSequencingActivity")
    elif type_code == 'wfrqc':
        return runtime.call_minter("nmdc:ReadQcAnalysisActivity")
    elif type_code == 'wfrba':
        return runtime.call_minter("nmdc:ReadBasedTaxonomyAnalysisActivity")
    elif type_code == 'wfasm':
        return runtime.call_minter("nmdc:MetagenomeAssembly")
    elif type_code == 'wfann':
        return runtime.call_minter("nmdc:MetagenomeAnnotationActivity")
    elif type_code == 'wfmag':
        return runtime.call_minter("nmdc:MagsAnalysisActivity")
    elif type_code == 'dobj':
        return runtime.call_minter("nmdc:DataObject")
        
def hash_type_string(minted_id):
    return hashlib.md5(minted_id.encode('utf-8')).hexdigest() 
    
    
if __name__=='__main__':
    #go through all the file, create an instance of each activity 
    #go through edge cases. 
    # Submit to endpoint
    if len(sys.argv) < 2:
        print("Usage: mapper.py <input.tsv>")
        sys.exit()
    input_tsv = sys.argv[1]
    
    logging.basicConfig(filename='processingGROW.log',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)
    
    destination_root_dir = '/global/cfs/cdirs/m3408/ficus/pipeline_products'
    exclude_list = []
    
    
    with open(input_tsv) as bioscales_file:
        mappings = csv.reader(bioscales_file, delimiter='\t')
        for line in mappings:
            if line[0].startswith("biosample"):
                continue
            if '(' and ')' in line[3]:
                logging.info(f'{line[3]} is being passed over due to duplicates')
                pass
            elif os.path.exists(os.path.join(destination_root_dir,line[2])):
                print(f'{line[2]} already has been processed')
                pass
            elif line[3] in exclude_list:
                pass   
            else:
                gold_biosample = line[0].split(':')[-1]
                omics_processing_id = line[2]
                ga_id = line[3]
                project_path = line[4]
                files_list = [os.path.join(project_path,f) for f in os.listdir(os.path.abspath(project_path)) if os.path.isfile(os.path.join(project_path, f))]
                logging.info(f'{gold_biosample},{ga_id}, {omics_processing_id} being processed')
                mapper = GoldMapper(files_list,omics_processing_id,destination_root_dir,project_path)
            
                reads_qc_inputs = mapper.sequencing_mapper()
                asm_inputs = mapper.read_qc_mapper(reads_qc_inputs)
                ann_inputs = mapper.assembly_mapper(asm_inputs)
                mags_inputs_og = mapper.annotation_mapper([ann_inputs[0]])
                mags_inputs = mags_inputs_og + ann_inputs
                nmdc_database_dump = mapper.mags_mapper(mags_inputs)
                nmdc_database_object = json_dumper.dumps(nmdc_database_dump,inject_type=False)
                res = runtime.post_objects(nmdc_database_object)
                print(res)
