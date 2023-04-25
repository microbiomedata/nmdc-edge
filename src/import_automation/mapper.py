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
        self._raw_git_url = 'https://github.com/microbiomedata/RawSequencingData'
        self._rqc_version = 'b1.0.7'
        self._rqc_git_url = 'https://github.com/microbiomedata/ReadsQC'
        self._asm_version = 'v1.0.4-beta'
        self._asm_git_url = 'https://github.com/microbiomedata/metaAssembly'
        self._ann_version = 'v1.0.2-beta'
        self._ann_git_url = 'https://github.com/microbiomedata/mg_annotation'
        self._mags_version = 'v1.0.5-beta'
        self._mags_git_url = 'https://github.com/microbiomedata/metaMAGs'
        #my responsibility is to generate the activit ids with the minting service, ~ .1 for JGI
        
        
    def sequencing_mapper(self):
        output_objects = []
        raw_id = mint_id('wfraw') + '.1'
        print(raw_id)
        raw_dir = f'{self.root_dir}/{self.gold_id}/{raw_id}'
        print(raw_dir)
        # hash_raw_id = hash_type_string(raw_id)
        for file in self.file_list:
            if re.search('fastq.gz',file,re.IGNORECASE) and not re.search('filter-METAGENOME.fastq.gz',file, re.IGNORECASE) and not re.search('input.corr.fastq.gz',file,re.IGNORECASE):
                raw_reads = os.path.basename(file)
                filemeta = os.stat(file)
                md5_raw = get_md5(file)
                dobj_raw = mint_id('dobj')
                os.makedirs(raw_dir,exist_ok=True)
                shutil.copy(file, os.path.join(raw_dir, raw_reads))
                output_objects.append(dobj_raw)
                self.nmdc_db.data_object_set.append(
                    nmdc.DataObject(
                        file_size_bytes=filemeta.st_size,
                        name="Raw sequencer read data",
                        url=f"{self.url}/{self.gold_id}/{raw_id}/{raw_reads}",
                        data_object_type="Metagenome Raw Reads",
                        type="nmdc:DataObject",
                        id=dobj_raw, #call dataobject type through minter
                        md5_checksum=md5_raw, 
                        description=f"Metagenome Raw Reads for {self.gold_id}"
                ))
        
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
                        has_output=output_objects,
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
        output_objects = []
        for file in self.file_list:
            if re.search('filter-METAGENOME.fastq.gz', file, re.IGNORECASE):
                nmdc_rqc_filtered = rqc_file_id + '_filtered.fastq.gz'
                filemeta = os.stat(file)
                md5_filter = get_md5(file)
                dobj_filter = mint_id('dobj')
                self.file_handler(file,nmdc_rqc_filtered, rqc_directory)
                output_objects.append(dobj_filter)
                self.nmdc_db.data_object_set.append(
                    nmdc.DataObject(
                        file_size_bytes=filemeta.st_size,
                        name="Reads QC result fastq (clean data)",
                        url=f"{rqc_url}/{nmdc_rqc_filtered}",
                        data_object_type="Filtered Sequencing Reads",
                        type="nmdc:DataObject",
                        id=dobj_filter, 
                        md5_checksum=md5_filter, 
                        description=f"Reads QC for {rqc_id}"
                ))
                    
            elif re.search('filtered-report.txt', file, re.IGNORECASE):
                nmdc_rqc_report =  rqc_file_id + '_filterStats.txt'
                filemeta = os.stat(file)
                md5_report = get_md5(file)
                dobj_report = mint_id('dobj')
                self.file_handler(file, nmdc_rqc_report, rqc_directory)
                output_objects.append(dobj_report)
                self.nmdc_db.data_object_set.append(
                    nmdc.DataObject(
                        file_size_bytes=filemeta.st_size,
                        name="Reads QC summary statistics",
                        url=f"{rqc_url}/{nmdc_rqc_report}",
                        data_object_type="QC Statistics",
                        type="nmdc:DataObject",
                        id=dobj_report,
                        md5_checksum=md5_report, 
                        description=f"Reads QC summary for {rqc_id}"
                    ))
                    
            else:
                #add logger
                logger.debug(f'{file} does match readsqc schema compliant file_enum translation')
        
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
        for file in self.file_list:
            if re.search('assembly.contigs.fasta', file, re.IGNORECASE):
                nmdc_asm_contigs = asm_file_id + '_contigs.fna'
                filemeta = os.stat(file)
                md5_contigs = get_md5(file)
                dobj_contigs = mint_id('dobj')
                self.file_handler(file, nmdc_asm_contigs, asm_directory)
                output_objects.append(dobj_contigs)
                self.nmdc_db.data_object_set.append(
                    nmdc.DataObject(
                        file_size_bytes=filemeta.st_size,
                        name="Final assembly contigs fasta",
                        url=f"{asm_url}/{nmdc_asm_contigs}",
                        data_object_type="Assembly Contigs",
                        type="nmdc:DataObject",
                        id=dobj_contigs, 
                        md5_checksum=md5_contigs, 
                        description=f"Assembly contigs for {asm_id}"
                ))
                    
            elif re.search('pairedMapped_sorted.bam.cov', file, re.IGNORECASE):
                nmdc_asm_cov_info =  asm_file_id + '_covstats.txt'
                filemeta = os.stat(file)
                md5_cov_info = get_md5(file)
                dobj_cov_info = mint_id('dobj')
                self.file_handler(file, nmdc_asm_cov_info, asm_directory)
                output_objects.append(dobj_cov_info)
                self.nmdc_db.data_object_set.append(
                    nmdc.DataObject(
                        file_size_bytes=filemeta.st_size,
                        name="Assembled contigs coverage information",
                        url=f"{asm_url}/{nmdc_asm_cov_info}",
                        data_object_type="Assembly Coverage Stats",
                        type="nmdc:DataObject",
                        id=dobj_cov_info,
                        md5_checksum=md5_cov_info, 
                        description=f"Coverage Stats for {asm_id}"
                    ))
            
            elif re.search('pairedMapped.sam.gz', file, re.IGNORECASE):
                nmdc_asm_bam =  asm_file_id + '_pairedMapped_sorted.sam.gz'
                filemeta = os.stat(file)
                md5_bam = get_md5(file)
                dobj_bam = mint_id('dobj')
                self.file_handler(file, nmdc_asm_bam, asm_directory)
                output_objects.append(dobj_bam)
                self.nmdc_db.data_object_set.append(
                    nmdc.DataObject(
                        file_size_bytes=filemeta.st_size,
                        name="Sorted bam file of reads mapping back to the final assembly",
                        url=f"{asm_url}/{nmdc_asm_bam}",
                        data_object_type="Assembly Coverage BAM",
                        type="nmdc:DataObject",
                        id=dobj_bam,
                        md5_checksum=md5_bam, 
                        description=f"Sorted Bam for {asm_id}"
                    ))
                
            elif re.search('input.corr.fastq.gz', file, re.IGNORECASE):
                nmdc_asm_corr =  asm_file_id + '_input.corr.fastq.gz'
                filemeta = os.stat(file)
                md5_corr = get_md5(file)
                dobj_corr = mint_id('dobj')
                self.file_handler(file, nmdc_asm_corr, asm_directory)
                output_objects.append(dobj_corr)
                self.nmdc_db.data_object_set.append(
                    nmdc.DataObject(
                        file_size_bytes=filemeta.st_size,
                        name="Error corrected reads fastq",
                        url=f"{asm_url}/{nmdc_asm_corr}",
                        data_object_type="Error Corrected Reads",
                        type="nmdc:DataObject",
                        id=dobj_corr,
                        md5_checksum=md5_corr, 
                        description=f"Error Corrected Reads for {asm_id}"
                    ))
                
                
            elif re.search('README.txt', file, re.IGNORECASE):
                nmdc_asm_info =  asm_file_id + '_assembly.info'
                filemeta = os.stat(file)
                md5_info = get_md5(file)
                dobj_info = mint_id('dobj')
                self.file_handler(file, nmdc_asm_info, asm_directory)
                output_objects.append(dobj_info)
                self.nmdc_db.data_object_set.append(
                    nmdc.DataObject(
                        file_size_bytes=filemeta.st_size,
                        name="Assemly Info File",
                        url=f"{asm_url}/{nmdc_asm_info}",
                        data_object_type="Assembly Info File",
                        type="nmdc:DataObject",
                        id=dobj_info,
                        md5_checksum=md5_info, 
                        description=f"Assembly Info for {asm_id}"
                    ))
                    
            else:
                logger.debug(f'{file} not compliant to metagenome_assembly translation')
                
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
        output_objects = []
        for file in self.file_list:
            if re.search('structural_annotation.gff', file, re.IGNORECASE):
                nmdc_structural_gff = ann_file_id + '_structural_annotation.gff'
                filemeta = os.stat(file)
                md5_structural = get_md5(file)
                dobj_structural_gff = mint_id('dobj')
                self.file_handler(file, nmdc_structural_gff, ann_directory)
                output_objects.append(dobj_structural_gff)
                self.nmdc_db.data_object_set.append(
                    nmdc.DataObject(
                        file_size_bytes=filemeta.st_size,
                        name="GFF3 format file with structural annotations",
                        url=f"{ann_url}/{nmdc_structural_gff}",
                        data_object_type="Structural Annotation GFF",
                        type="nmdc:DataObject",
                        id=dobj_structural_gff, 
                        md5_checksum=md5_structural, 
                        description=f"Structural Annotation for {ann_id}"
                ))
                
            elif re.search('functional_annotation.gff', file, re.IGNORECASE):
                nmdc_functional_gff = ann_file_id + '_functional_annotation.gff'
                filemeta = os.stat(file)
                md5_functional = get_md5(file)
                dobj_functional_gff = mint_id('dobj')
                self.file_handler(file, nmdc_functional_gff, ann_directory)
                output_objects.append(dobj_functional_gff)
                self.nmdc_db.data_object_set.append(
                    nmdc.DataObject(
                        file_size_bytes=filemeta.st_size,
                        name="GFF3 format file with functional annotations",
                        url=f"{ann_url}/{nmdc_functional_gff}",
                        data_object_type="Functional Annotation GFF",
                        type="nmdc:DataObject",
                        id=dobj_functional_gff, 
                        md5_checksum=md5_functional, 
                        description=f"Functional Annotation for {ann_id}"
                ))
            
            elif re.search('ko.tsv', file, re.IGNORECASE):
                nmdc_ko_tsv = ann_file_id + '_ko.tsv'
                filemeta = os.stat(file)
                md5_ko_tsv = get_md5(file)
                dobj_ko_tsv = mint_id('dobj')
                self.file_handler(file, nmdc_ko_tsv, ann_directory)
                output_objects.append(dobj_ko_tsv)
                self.nmdc_db.data_object_set.append(
                    nmdc.DataObject(
                        file_size_bytes=filemeta.st_size,
                        name="Tab delimited file for KO annotation",
                        url=f"{ann_url}/{nmdc_ko_tsv}",
                        data_object_type="Annotation KEGG Orthology",
                        type="nmdc:DataObject",
                        id=dobj_ko_tsv, 
                        md5_checksum=md5_ko_tsv, 
                        description=f"KEGG Orthology for {ann_id}"
                ))
                
            elif re.search('ec.tsv', file, re.IGNORECASE):
                nmdc_ec_tsv = ann_file_id + '_ec.tsv'
                filemeta = os.stat(file)
                md5_ec_tsv = get_md5(file)
                dobj_ec_tsv = mint_id('dobj')
                self.file_handler(file, nmdc_ec_tsv, ann_directory)
                output_objects.append(dobj_ec_tsv)
                self.nmdc_db.data_object_set.append(
                    nmdc.DataObject(
                        file_size_bytes=filemeta.st_size,
                        name="Tab delimited file for EC annotation",
                        url=f"{ann_url}/{nmdc_ec_tsv}",
                        data_object_type="Annotation Enzyme Commission",
                        type="nmdc:DataObject",
                        id=dobj_ec_tsv, 
                        md5_checksum=md5_ec_tsv, 
                        description=f"EC Annotations for {ann_id}"
                ))
                
            elif re.search('contig_names_mapping.tsv', file, re.IGNORECASE):
                nmdc_asm_map =  ann_file_id + '_contig_names_mapping.tsv'
                filemeta = os.stat(file)
                md5_map = get_md5(file)
                dobj_map = mint_id('dobj')
                self.file_handler(file, nmdc_asm_map, ann_directory)
                output_objects.append(dobj_map)
                self.nmdc_db.data_object_set.append(
                    nmdc.DataObject(
                        file_size_bytes=filemeta.st_size,
                        name="Contig mappings between contigs and scaffolds",
                        url=f"{ann_url}/{nmdc_asm_map}",
                        data_object_type="Contig Mapping File",
                        type="nmdc:DataObject",
                        id=dobj_map,
                        md5_checksum=md5_map, 
                        description=f"Contig Mapping File for {ann_id}"
                    ))
                
                
            elif re.search('cog.gff', file, re.IGNORECASE):
                nmdc_cog_gff = ann_file_id + '_cog.gff'
                filemeta = os.stat(file)
                md5_cog_gff = get_md5(file)
                dobj_cog_gff = mint_id('dobj')
                self.file_handler(file, nmdc_cog_gff, ann_directory)
                output_objects.append(dobj_cog_gff)
                self.nmdc_db.data_object_set.append(
                    nmdc.DataObject(
                        file_size_bytes=filemeta.st_size,
                        name="GFF3 format file with COGs",
                        url=f"{ann_url}/{nmdc_cog_gff}",
                        data_object_type="Clusters of Orthologous Groups (COG) Annotation GFF",
                        type="nmdc:DataObject",
                        id=dobj_cog_gff, 
                        md5_checksum=md5_cog_gff, 
                        description=f"COGs for {ann_id}"
                ))
                
            elif re.search('pfam.gff', file, re.IGNORECASE):
                nmdc_pfam_gff = ann_file_id + '_pfam.gff'
                filemeta = os.stat(file)
                md5_pfam_gff = get_md5(file)
                dobj_pfam_gff = mint_id('dobj')
                self.file_handler(file, nmdc_pfam_gff, ann_directory)
                output_objects.append(dobj_pfam_gff)
                self.nmdc_db.data_object_set.append(
                    nmdc.DataObject(
                        file_size_bytes=filemeta.st_size,
                        name="GFF3 format file with Pfam",
                        url=f"{ann_url}/{nmdc_pfam_gff}",
                        data_object_type="Pfam Annotation GFF",
                        type="nmdc:DataObject",
                        id=dobj_pfam_gff, 
                        md5_checksum=md5_pfam_gff, 
                        description=f"Pfam Annotation for {ann_id}"
                ))
                
            elif re.search('tigrfam.gff', file, re.IGNORECASE):
                nmdc_tigrfam_gff = ann_file_id + '_tigrfam.gff'
                filemeta = os.stat(file)
                md5_tigrfam_gff = get_md5(file)
                dobj_tigrfam_gff = mint_id('dobj')
                self.file_handler(file, nmdc_tigrfam_gff, ann_directory)
                output_objects.append(dobj_tigrfam_gff)
                self.nmdc_db.data_object_set.append(
                    nmdc.DataObject(
                        file_size_bytes=filemeta.st_size,
                        name="GFF3 format file with TIGRfam",
                        url=f"{ann_url}/{nmdc_tigrfam_gff}",
                        data_object_type="TIGRFam Annotation GFF",
                        type="nmdc:DataObject",
                        id=dobj_tigrfam_gff, 
                        md5_checksum=md5_tigrfam_gff, 
                        description=f"TIGRFam for {ann_id}"
                ))
                
                
            elif re.search('smart.gff', file, re.IGNORECASE):
                nmdc_smart_gff = ann_file_id + '_smart.gff'
                filemeta = os.stat(file)
                md5_smart_gff = get_md5(file)
                dobj_smart_gff = mint_id('dobj')
                self.file_handler(file, nmdc_smart_gff, ann_directory)
                output_objects.append(dobj_smart_gff)
                self.nmdc_db.data_object_set.append(
                    nmdc.DataObject(
                        file_size_bytes=filemeta.st_size,
                        name="GFF3 format file with SMART",
                        url=f"{ann_url}/{nmdc_smart_gff}",
                        data_object_type="SMART Annotation GFF",
                        type="nmdc:DataObject",
                        id=dobj_smart_gff, 
                        md5_checksum=md5_smart_gff, 
                        description=f"SMART Annotations for {ann_id}"
                ))
                
                
            elif re.search('supfam.gff', file, re.IGNORECASE):
                nmdc_supfam_gff = ann_file_id + '_supfam.gff'
                filemeta = os.stat(file)
                md5_supfam_gff = get_md5(file)
                dobj_supfam_gff = mint_id('dobj')
                self.file_handler(file, nmdc_supfam_gff, ann_directory)
                output_objects.append(dobj_supfam_gff)
                self.nmdc_db.data_object_set.append(
                    nmdc.DataObject(
                        file_size_bytes=filemeta.st_size,
                        name="GFF3 format file with SUPERFam",
                        url=f"{ann_url}/{nmdc_supfam_gff}",
                        data_object_type="SUPERFam Annotation GFF",
                        type="nmdc:DataObject",
                        id=dobj_supfam_gff, 
                        md5_checksum=md5_supfam_gff, 
                        description=f"SUPERFam Annotations for {ann_id}"
                ))
                
                
            elif re.search('cath_funfam.gff', file, re.IGNORECASE):
                nmdc_catfun_gff = ann_file_id + '_cath_funfam.gff'
                filemeta = os.stat(file)
                md5_catfun_gff = get_md5(file)
                dobj_catfun_gff = mint_id('dobj')
                self.file_handler(file, nmdc_catfun_gff, ann_directory)
                output_objects.append(dobj_catfun_gff)
                self.nmdc_db.data_object_set.append(
                    nmdc.DataObject(
                        file_size_bytes=filemeta.st_size,
                        name="GFF3 format file with CATH FunFams",
                        url=f"{ann_url}/{nmdc_catfun_gff}",
                        data_object_type="CATH FunFams (Functional Families) Annotation GFF",
                        type="nmdc:DataObject",
                        id=dobj_catfun_gff, 
                        md5_checksum=md5_catfun_gff, 
                        description=f"CATH FunFams for {ann_id}"
                ))
                
                
            elif re.search('crt.gff', file, re.IGNORECASE):
                nmdc_crt_gff = ann_file_id + '_crt.gff'
                filemeta = os.stat(file)
                md5_crt_gff = get_md5(file)
                dobj_crt_gff = mint_id('dobj')
                self.file_handler(file, nmdc_crt_gff, ann_directory)
                output_objects.append(dobj_crt_gff)
                self.nmdc_db.data_object_set.append(
                    nmdc.DataObject(
                        file_size_bytes=filemeta.st_size,
                        name="GFF3 format file with CRT",
                        url=f"{ann_url}/{nmdc_crt_gff}",
                        data_object_type="CRT Annotation GFF",
                        type="nmdc:DataObject",
                        id=dobj_crt_gff, 
                        md5_checksum=md5_crt_gff, 
                        description=f"CRT Annotations for {ann_id}"
                ))
                
            elif re.search('genemark.gff', file, re.IGNORECASE):
                    nmdc_genemark_gff = ann_file_id + '_genemark.gff'
                    filemeta = os.stat(file)
                    md5_genemark_gff = get_md5(file)
                    dobj_genemark_gff = mint_id('dobj')
                    self.file_handler(file, nmdc_genemark_gff, ann_directory)
                    output_objects.append(dobj_genemark_gff)
                    self.nmdc_db.data_object_set.append(
                        nmdc.DataObject(
                            file_size_bytes=filemeta.st_size,
                            name="GFF3 format file with Genemark",
                            url=f"{ann_url}/{nmdc_genemark_gff}",
                            data_object_type="Genemark Annotation GFF",
                            type="nmdc:DataObject",
                            id=dobj_genemark_gff, 
                            md5_checksum=md5_genemark_gff, 
                            description=f"Genemark Annotations for {ann_id}"
                    ))
                
            elif re.search('prodigal.gff', file, re.IGNORECASE):
                nmdc_prodigal_gff = ann_file_id + '_prodigal.gff'
                filemeta = os.stat(file)
                md5_prodigal_gff = get_md5(file)
                dobj_prodigal_gff = mint_id('dobj')
                self.file_handler(file,nmdc_prodigal_gff, ann_directory)
                output_objects.append(dobj_prodigal_gff)
                self.nmdc_db.data_object_set.append(
                    nmdc.DataObject(
                        file_size_bytes=filemeta.st_size,
                        name="GFF3 format file with Prodigal",
                        url=f"{ann_url}/{nmdc_prodigal_gff}",
                        data_object_type="Prodigal Annotation GFF",
                        type="nmdc:DataObject",
                        id=dobj_prodigal_gff, 
                        md5_checksum=md5_prodigal_gff, 
                        description=f"Prodigal Annotations for {ann_id}"
                ))
                
            elif re.search('trna.gff', file, re.IGNORECASE):
                nmdc_trna_gff = ann_file_id + '_trna.gff'
                filemeta = os.stat(file)
                md5_trna_gff = get_md5(file)
                dobj_trna_gff = mint_id('dobj')
                self.file_handler(file, nmdc_trna_gff, ann_directory)
                output_objects.append(dobj_trna_gff)
                self.nmdc_db.data_object_set.append(
                    nmdc.DataObject(
                        file_size_bytes=filemeta.st_size,
                        name="GFF3 format file with TRNA",
                        url=f"{ann_url}/{nmdc_trna_gff}",
                        data_object_type="TRNA Annotation GFF",
                        type="nmdc:DataObject",
                        id=dobj_trna_gff, 
                        md5_checksum=md5_trna_gff, 
                        description=f"TRNA Annotations for {ann_id}"
                ))
                
            elif re.search('rfam_misc_bind_misc_feature_regulatory.gff', file, re.IGNORECASE):
                nmdc_misc_gff = ann_file_id + '_rfam_misc_bind_misc_feature_regulatory.gff'
                filemeta = os.stat(file)
                md5_misc_gff = get_md5(file)
                dobj_misc_gff = mint_id('dobj')
                self.file_handler(file, nmdc_misc_gff, ann_directory)
                output_objects.append(dobj_misc_gff)
                self.nmdc_db.data_object_set.append(
                    nmdc.DataObject(
                        file_size_bytes=filemeta.st_size,
                        name="GFF3 format file with Misc",
                        url=f"{ann_url}/{nmdc_misc_gff}",
                        data_object_type="Misc Annotation GFF",
                        type="nmdc:DataObject",
                        id=dobj_misc_gff, 
                        md5_checksum=md5_misc_gff, 
                        description=f"Misc Annotations for {ann_id}"
                ))
                
            elif re.search('rfam_rrna.gff', file, re.IGNORECASE):
                nmdc_rfam_gff = ann_file_id + '_rfam_rrna.gff'
                filemeta = os.stat(file)
                md5_rfam_gff = get_md5(file)
                dobj_rfam_gff = mint_id('dobj')
                self.file_handler(file, nmdc_rfam_gff, ann_directory)
                output_objects.append(dobj_rfam_gff)
                self.nmdc_db.data_object_set.append(
                    nmdc.DataObject(
                        file_size_bytes=filemeta.st_size,
                        name="GFF3 format file with RFAM",
                        url=f"{ann_url}/{nmdc_rfam_gff}",
                        data_object_type="RFAM Annotation GFF",
                        type="nmdc:DataObject",
                        id=dobj_rfam_gff, 
                        md5_checksum=md5_rfam_gff, 
                        description=f"RFAM Annotations for {ann_id}"
                ))
                
                
            elif re.search('rfam_ncrna_tmrna.gff', file, re.IGNORECASE):
                nmdc_tmrna_gff = ann_file_id + '_rfam_ncrna_tmrna.gff'
                filemeta = os.stat(file)
                md5_tmrna_gff = get_md5(file)
                dobj_tmrna_gff = mint_id('dobj')
                self.file_handler(file, nmdc_tmrna_gff, ann_directory)
                output_objects.append(dobj_tmrna_gff)
                self.nmdc_db.data_object_set.append(
                    nmdc.DataObject(
                        file_size_bytes=filemeta.st_size,
                        name="GFF3 format file with TMRNA",
                        url=f"{ann_url}/{nmdc_tmrna_gff}",
                        data_object_type="TMRNA Annotation GFF",
                        type="nmdc:DataObject",
                        id=dobj_tmrna_gff, 
                        md5_checksum=md5_tmrna_gff, 
                        description=f"TMRNA Annotations for {ann_id}"
                ))
                    
            elif re.search('ko_ec.gff', file, re.IGNORECASE):
                nmdc_ko_ec_gff = ann_file_id + '_ko_ec.gff'
                filemeta = os.stat(file)
                md5_ko_ec_gff = get_md5(file)
                dobj_ko_ec_gff = mint_id('dobj')
                self.file_handler(file, nmdc_ko_ec_gff, ann_directory)
                output_objects.append(dobj_ko_ec_gff)
                self.nmdc_db.data_object_set.append(
                    nmdc.DataObject(
                        file_size_bytes=filemeta.st_size,
                        name="GFF3 format file with KO_EC",
                        url=f"{ann_url}/{nmdc_ko_ec_gff}",
                        data_object_type="KO_EC Annotation GFF",
                        type="nmdc:DataObject",
                        id=dobj_ko_ec_gff, 
                        md5_checksum=md5_ko_ec_gff, 
                        description=f"KO_EC Annotations for {ann_id}"
                ))
                    
            elif re.search('product_names.tsv', file, re.IGNORECASE):
                nmdc_product_tsv = ann_file_id + '_product_names.tsv'
                filemeta = os.stat(file)
                md5_product_tsv = get_md5(file)
                dobj_product_tsv = mint_id('dobj')
                self.file_handler(file, nmdc_product_tsv, ann_directory)
                output_objects.append(dobj_product_tsv)
                self.nmdc_db.data_object_set.append(
                    nmdc.DataObject(
                        file_size_bytes=filemeta.st_size,
                        name="Product names file",
                        url=f"{ann_url}/{nmdc_product_tsv}",
                        data_object_type="Product Names",
                        type="nmdc:DataObject",
                        id=dobj_product_tsv, 
                        md5_checksum=md5_product_tsv, 
                        description=f"Product names for {ann_id}"
                ))
                    
            elif re.search('gene_phylogeny.tsv', file, re.IGNORECASE):
                nmdc_phylo_tsv = ann_file_id + '_gene_phylogeny.tsv'
                filemeta = os.stat(file)
                md5_phylo_tsv = get_md5(file)
                dobj_phylo_tsv = mint_id('dobj')
                self.file_handler(file, nmdc_phylo_tsv, ann_directory)
                output_objects.append(dobj_phylo_tsv)
                self.nmdc_db.data_object_set.append(
                    nmdc.DataObject(
                        file_size_bytes=filemeta.st_size,
                        name="Gene Phylogeny tsv",
                        url=f"{ann_url}/{nmdc_phylo_tsv}",
                        data_object_type="Gene Phylogeny tsv",
                        type="nmdc:DataObject",
                        id=dobj_phylo_tsv, 
                        md5_checksum=md5_phylo_tsv, 
                        description=f"Gene Phylogeny tsv for {ann_id}"
                ))
                    
                    
            elif re.search('crt.crisprs', file, re.IGNORECASE):
                nmdc_crisprs = ann_file_id + '_crt.crisprs'
                filemeta = os.stat(file)
                md5_crisprs = get_md5(file)
                dobj_crisprs = mint_id('dobj')
                self.file_handler(file, nmdc_crisprs, ann_directory)
                output_objects.append(dobj_crisprs)
                self.nmdc_db.data_object_set.append(
                    nmdc.DataObject(
                        file_size_bytes=filemeta.st_size,
                        name="Crispr Terms",
                        url=f"{ann_url}/{nmdc_crisprs}",
                        data_object_type="Crispr Terms",
                        type="nmdc:DataObject",
                        id=dobj_crisprs, 
                        md5_checksum=md5_crisprs, 
                        description=f"Crispr Terms for {ann_id}"
                ))
                        
            elif re.search('structural_annotation_stats.tsv', file, re.IGNORECASE):
                nmdc_ano_stats = ann_file_id + '_stats.tsv'
                filemeta = os.stat(file)
                md5_ano_stats = get_md5(file)
                dobj_ano_stats = mint_id('dobj')
                self.file_handler(file, nmdc_ano_stats, ann_directory)
                output_objects.append(dobj_ano_stats)
                self.nmdc_db.data_object_set.append(
                    nmdc.DataObject(
                        file_size_bytes=filemeta.st_size,
                        name="Annotation statistics report",
                        url=f"{ann_url}/{nmdc_ano_stats}",
                        data_object_type="Annotation Statistics",
                        type="nmdc:DataObject",
                        id=dobj_ano_stats, 
                        md5_checksum=md5_ano_stats, 
                        description=f"Annotation Stats for {ann_id}"
                ))
                
            elif re.search('structural_annotation_stats.json', file, re.IGNORECASE):
                nmdc_ano_stats_json = ann_file_id + '_stats.json'
                filemeta = os.stat(file)
                md5_ano_stats_json = get_md5(file)
                dobj_ano_json = mint_id('dobj')
                self.file_handler(file, nmdc_ano_stats_json, ann_directory)
                output_objects.append(dobj_ano_json)
                self.nmdc_db.data_object_set.append(
                    nmdc.DataObject(
                        file_size_bytes=filemeta.st_size,
                        name="Structural annotation stats json",
                        url=f"{ann_url}/{nmdc_ano_stats_json}",
                        data_object_type="Structural Annotation Stats Json",
                        type="nmdc:DataObject",
                        id=dobj_ano_json, 
                        md5_checksum=md5_ano_stats_json, 
                        description=f"Structural Annotation Stats Json for {ann_id}"
                ))
                
            elif re.search('imgap.info', file, re.IGNORECASE):
                nmdc_ano_info = ann_file_id + '_annotation.info'
                filemeta = os.stat(file)
                md5_ano_info = get_md5(file)
                dobj_ano_info = mint_id('dobj')
                self.file_handler(file, nmdc_ano_info, ann_directory)
                output_objects.append(dobj_ano_info)
                self.nmdc_db.data_object_set.append(
                    nmdc.DataObject(
                        file_size_bytes=filemeta.st_size,
                        name="File containing annotation info",
                        url=f"{ann_url}/{nmdc_ano_info}",
                        data_object_type="Annotation Info File",
                        type="nmdc:DataObject",
                        id=dobj_ano_info, 
                        md5_checksum=md5_ano_info, 
                        description=f"Annotation Info File for {ann_id}"
                ))
                        
            elif re.search('proteins.faa', file, re.IGNORECASE) and not re.search('_genemark_proteins.faa',file, re.IGNORECASE) and not re.search('_prodigal_proteins.faa',file,re.IGNORECASE):
                nmdc_ano_proteins = ann_file_id + '_proteins.faa'
                filemeta = os.stat(file)
                md5_ano_proteins = get_md5(file)
                dobj_ano_proteins = mint_id('dobj')
                self.file_handler(file, nmdc_ano_proteins, ann_directory)
                output_objects.append(dobj_ano_proteins)
                self.nmdc_db.data_object_set.append(
                    nmdc.DataObject(
                        file_size_bytes=filemeta.st_size,
                        name="FASTA amino acid file for annotated proteins",
                        url=f"{ann_url}/{nmdc_ano_proteins}",
                        data_object_type="Annotation Amino Acid FASTA",
                        type="nmdc:DataObject",
                        id=dobj_ano_proteins, 
                        md5_checksum=md5_ano_proteins, 
                        description=f"FASTA Amino Acid File for {ann_id}"
                ))
                        
            else:
                logger.debug(f'{file} not an instance of acceptable nmdc annotation file')
                
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
                name=f"Metagenome bin contigs fasta",
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
        # shutil.copy(os.path.join(self.project_dir, updated_file), destination_dir)
    
    # def file_handler(self, original_file, updated_file, destination_dir):
    #     try:
    #         os.makedirs(destination_dir)
    #     except FileExistsError:
    #         logger.info(f'{destination_dir} already exists')
            
    #     os.link(os.path.join(os.path.join(self.project_dir,original_file), os.path.join(destination_dir,updated_file)))
    
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
            else:
                gold_biosample = line[0].split(':')[-1]
                omics_processing_id = line[2]
                ga_id = line[3]
                project_path = line[4]
                files_list = [os.path.join(project_path,f) for f in os.listdir(os.path.abspath(project_path)) if os.path.isfile(os.path.join(project_path, f))]
                for file in files_list:
                    if not re.search('filter-METAGENOME.fastq.gz', file, re.IGNORECASE):
                        pass
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



#TODO:
#/global/cfs/cdirs/m3408/ficus/pipeline_products/nmdc:omprc-11-pbv30519/
#/global/cfs/cdirs/m3408/ficus/pipeline_products/nmdc:omprc-11-k7wfx458/