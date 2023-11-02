#!/usr/bin/env python
import os
import sys
import re
import yaml
import datetime
import pytz
from pymongo import MongoClient
import json
from nmdc_automation.api import NmdcRuntimeApi
from re_id_file_operations import *
import nmdc_schema.nmdc as nmdc
from linkml_runtime.dumpers import json_dumper
import shutil 

###GLOBAL######
nmdc_db = nmdc.Database()
runtime_api = NmdcRuntimeApi("../../configs/napa_config.toml")
base = "https://data.microbiomedata.org/data"
base_dir = "/global/cfs/cdirs/m3408/results"


sets = [
        "read_qc_analysis_activity_set",
        "metagenome_assembly_set",
        "read_based_taxonomy_analysis_activity_set"
        ]


mapping_log = open("mapping.log", "a")

def read_workflows_config(config_file):
    with open(config_file, "r") as file:
        workflow_data = yaml.safe_load(file)
        
    return workflow_data["Workflows"]

def log_mapping(idtype, old, new):
    """
    Logs the mapping information.
    
    Parameters:
    - idtype: The type of the ID (e.g., 'data', 'activity')
    - old: The old ID value
    - new: The new ID value
    """
    mapping_log.write(f"{idtype}\t{old}\t{new}\n")


def read_map():
    """
    Reads a mapping list from a file and returns it as a dictionary.
    
    Returns:
    - omap: A dictionary with old ID as key and new ID as value.
    """
    omap = {}
    with open("map.lst") as f:
        for line in f:
            (k, v) = line.rstrip().split("\t")
            omap[k] = v
    return omap


def minter(shoulder):
    """
    Creates a new ID based on the provided shoulder.
    
    Parameters:
    - shoulder: The base string for creating the new ID
    
    Returns:
    - A new ID string
    """
    
    return runtime_api.minter(shoulder)


def compute_new_paths(old_url, new_base_dir, omic_id, act_id):
    """
    Use the url to compute the new file name path and url
    """
    file_name = old_url.split("/")[-1]
    suffix = old_url.split("https://data.microbiomedata.org/data/")[1]
    old_file_path = base_dir + "/" + suffix
    file_extenstion = file_name.lstrip("nmdc_").split("_", maxsplit=1)[-1]
    new_file_name = f"{act_id}_{file_extenstion}"
    modified_new_file_name = new_file_name.replace(":", "_")
    destination = os.path.join(new_base_dir, modified_new_file_name)
    
    try:
        os.link(old_file_path, destination)
        print(f"Successfully created link between {old_file_path} and {destination}")
    except OSError as e:
        print(f"An error occurred while linking the file: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    
    new_url = f"{base}/{omic_id}/{act_id}/{new_file_name}"
    return new_url, destination, new_file_name


def find_type(obj):
    """
    Determine the data type of an object based on its URL extension.
    
    Args:
    - obj (dict): Dictionary containing the 'url' key which will be inspected to determine the data type.
    
    Returns:
    - str: The determined data type or None if the type could not be determined.
    """
    if "data_object_type" in obj:
        return obj["data_object_type"]
    url = obj["url"]
    if url.endswith("_covstats.txt"):
        return "Assembly Coverage Stats"
    elif url.endswith("_gottcha2_report.tsv"):
        return "GOTTCHA2 Classification Report"
    elif url.endswith("_gottcha2_report_full.tsv"):
        return "GOTTCHA2 Report Full"
    else:
        sys.stderr.write(f"Missing type: {url}")
        return None


def make_activity_set(omics_id, activity_id, has_input, has_output, started_time, ended_time, workflow_record_template):
    #look at activity range
    database_activity_set = getattr(nmdc_db, workflow_record_template["Collection"])
    # Lookup the nmdc schema range class
    database_activity_range = getattr(nmdc, workflow_record_template["ActivityRange"])
    
    database_activity_set.append(
        database_activity_range(
            id=activity_id,
            name=workflow_record_template["Activity"]["name"].replace("{id}", activity_id),
            git_url=workflow_record_template["Git_repo"],
            version=workflow_record_template["Version"],
            part_of=[omics_id],
            execution_resource="NERSC - Perlmutter",
            started_at_time=started_time,
            has_input=has_input,
            has_output=has_output,
            type=workflow_record_template["Type"],
            ended_at_time=ended_time,
            was_informed_by=omics_id,
        )
    )

def make_data_object(data_object_record, new_do_id, new_url, updated_name, updated_description):

    nmdc_db.data_object_set.append(
        nmdc.DataObject(
            file_size_bytes=data_object_record["file_size_bytes"],
            name=updated_name,
            url=new_url,
            data_object_type=data_object_record["data_object_type"],
            type="nmdc:DataObject",
            id=new_do_id,
            md5_checksum=data_object_record["md5_checksum"],
            description=updated_description
            ),
        )

def post_database_object_to_runtime(datase_object):
    
    nmdc_database_object = json.loads(
            json_dumper.dumps(datase_object, inject_type=False)
        )
    res = runtime_api.post_objects(nmdc_database_object)
    return res

def get_omics_id(omics_record):
    for rec in omics_record["omics_processing_set"]:
        return rec["id"]

def get_record_by_type(related_omic_records, record_type):
    """
    Returns the record that matches the given type.

    Parameters:
    - related_omic_records (dict): records for an omics processing record.
    - record_type (str): The desired type value to match.

    Returns:
    - dict: The first record that matches the given type, or None if not found.
    """
    
    return related_omic_records[record_type]

def get_data_object_by_type(related_omic_records, old_activity_record):
    
    data_object_list = []
    
    for act_record in old_activity_record:
        has_output_list = act_record["has_output"]
    for do_record in related_omic_records["data_object_set"]:
        if do_record["id"] in has_output_list:
            data_object_list.append(do_record)
            
    return data_object_list
        
def get_associate_data_object_template(data_object_type,data_object_templates):
    for data_object in data_object_templates:
        if data_object_type == data_object["data_object_type"]:
            return data_object
    return None
    
def reads_qc_update(omics_record, template_file, omic_id):
    """Extracts relevant information from omics record and template file, update data objects for reads qc
        and the analysis activity set record. Performs necessary file operation as well

    Args:
        omics_record (dict): omics record corresponding to downstream workflows
        template_file (file): template yaml file for relavant worklfows metadata
        omic_id (str): string identifier of omics id

    Returns:
        nmdc_database_object: dump of nmdc object
    """
    
    workflow_type = "read_qc_analysis_activity_set"
    #extract needed metaadata
    reads_qc_record = get_record_by_type(omics_record, workflow_type)
    reads_qc_data_objects = get_data_object_by_type(omics_record, reads_qc_record)
    for template in read_workflows_config(template_file):
        if template['Type'] == "nmdc:ReadQcAnalysisActivity":
            reads_qc_template = template
            
    #set up needed variables       
    new_act_id = minter(reads_qc_template["Type"])
    new_qc_base_dir = os.path.join(base_dir, omic_id, new_act_id)
    os.makedirs(new_qc_base_dir,exist_ok=True)
    updated_has_output_list = []
    
    #hold input to downstream workflows
    input_to_downstream_workflows = []
    #make new data objects
    for data_object in reads_qc_data_objects:
        dobj_tmpl = get_associate_data_object_template(data_object["data_object_type"],reads_qc_template["Outputs"])
        new_do_id = minter("nmdc:DataObject")
        #save filtered reads
        if data_object["data_object_type"] == "Filtered Sequencing Reads":
            input_to_downstream_workflows.append(new_do_id)
        new_description = re.sub('[^ ]+$', f"{omic_id}", data_object["description"])
        new_url, destination, _ = compute_new_paths(data_object["url"], new_qc_base_dir, omic_id, new_act_id)
        make_data_object(data_object, new_do_id, new_url, dobj_tmpl["name"], new_description)
        updated_has_output_list.append(new_do_id)
    
    #make updated activity record
    for rec in reads_qc_record:
        has_input = rec["has_input"]
        started_time = rec["started_at_time"]
        ended_time = rec["ended_at_time"]
    #need to change has input to be updated as well, 
    make_activity_set(omic_id, new_act_id, has_input, updated_has_output_list, started_time, ended_time, reads_qc_template)
        
    
    nmdc_database_object = json.loads(
            json_dumper.dumps(nmdc_db, inject_type=False)
        )
        
    print(nmdc_database_object)
    
    return input_to_downstream_workflows, destination

def assembly_update(omics_record, template_file, omic_id, workflow_inputs):
    """Extracts relevant information from omics record and template file, update data objects for assembly
        and the analysis activity set record. Performs necessary file operation as well

    Args:
        omics_record (dict): omics record corresponding to downstream workflows
        template_file (file): template yaml file for relavant worklfows metadata
        omic_id (str): string identifier of omics id

    Returns:
        nmdc_database_object: dump of nmdc object
    """
    
    workflow_type = "metagenome_assembly_set"
    #extract needed metaadata
    reads_qc_record = get_record_by_type(omics_record, workflow_type)
    reads_qc_data_objects = get_data_object_by_type(omics_record, reads_qc_record)
    for template in read_workflows_config(template_file):
        if template['Type'] == "nmdc:MetagenomeAssembly":
            reads_qc_template = template
            
    #set up needed variables       
    new_act_id = minter(reads_qc_template["Type"])
    new_qc_base_dir = os.path.join(base_dir, omic_id, new_act_id)
    os.makedirs(new_qc_base_dir,exist_ok=True)
    updated_has_output_list = []
    
    #make new data objects
    for data_object in reads_qc_data_objects:
        dobj_tmpl = get_associate_data_object_template(data_object["data_object_type"],reads_qc_template["Outputs"])
        new_do_id = minter("nmdc:DataObject")
        new_description = re.sub('[^ ]+$', f"{omic_id}", data_object["description"])
        new_url, destination, _ = compute_new_paths(data_object["url"], new_qc_base_dir, omic_id, new_act_id)
        make_data_object(data_object, new_do_id, new_url, dobj_tmpl["name"], new_description)
        updated_has_output_list.append(new_do_id)
    
    for rec in reads_qc_record:
        started_time = rec["started_at_time"]
        ended_time = rec["ended_at_time"]
    #need to change has input to be updated as well, 
    make_activity_set(omic_id, new_act_id, workflow_inputs, updated_has_output_list, started_time, ended_time, reads_qc_template)
        
    
    nmdc_database_object = json.loads(
            json_dumper.dumps(nmdc_db, inject_type=False)
        )
        
    print(nmdc_database_object)
    
    return destination
    
    
def process_analysis_sets(study_records, template_file,dry_run=False):
    
    count = 0
    for omic_record in study_records:
        omics_id = get_omics_id(omic_record)
        print(omics_id)
        downstream_input, destination = reads_qc_update(omic_record, template_file, omics_id)
        if dry_run == True:
            count += 1
        dir_path = os.path.dirname(destination)
        parent_dir_path = os.path.dirname(dir_path)
        try:
            shutil.rmtree(parent_dir_path)
            print(f"Directory {parent_dir_path} and all its contents removed successfully!")
        except OSError as e:
            print(f"Error: {e}")
        if count == 1:
            break
    
    

def main():
    #TODO
    #1. Read in json dump of analysis records 
    #2. Process records for reads qc - generate new metadata, make new records and data objects (this will include file copies and renaming)
    #3. save data of updated reads qc records
    #4. Fetch old records for readbased analysis and assembly, generate new metadata, make new records and data objects (this will include file copies and renaming files and ids in files)
    #5. Validate new records, submit them via runtime api
    #6. Write seperate process to delete old records once we have
    pass

if __name__ == "__main__":
    test_file = "scripts/nmdc:sty-11-aygzgv51_assocated_record_dump.json"
    template_file = "/global/cfs/cdirs/m3408/aim2/dev/reiding_scripts/nmdc_automation/configs/re_iding_worklfows.yaml"
    stegen_data = read_json_file(test_file)
    process_analysis_sets(stegen_data, template_file, dry_run=True)