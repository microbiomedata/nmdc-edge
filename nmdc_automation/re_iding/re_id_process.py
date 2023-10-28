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

###GLOBAL######
nmdc_db = nmdc.Database()
runtime_api = NmdcRuntimeApi("../../configs/site_configuration.toml")
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
        
    return workflow_data

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


def find_dir(db, old_id):
    """
    Finds and returns the directory name associated with the given ID.
    
    Parameters:
    - db: Database connection object
    - old_id: The old ID for which the directory name is required
    """
    query_by_omics_id = {"was_informed_by": old_id}
    activity_record = db.read_qc_analysis_activity_set.find_one(query_by_omics_id)
    query_by_id = {"id": activity_record['has_output'][0]}
    data_object_record = db.data_object_set.find_one(query_by_id)
    return data_object_record['url'].split('/')[4]


def process(db, old_id, new_id):
    """
    Process the given old ID and returns the associated data.
    
    Parameters:
    - db: Database connection object
    - old_id: The old ID to be processed
    - new_id: The new ID to be used
    
    Returns:
    - out: A dictionary containing processed data.
    """
    directory_name = find_dir(db, old_id)
    assocaited_data_object = {"data_object_set": []}
    for col in sets:
        query_by_old_id = {"was_informed_by": old_id}
        res = db[col].find(query_by_old_id)
        count = 0
        for doc in res:
            count += 1
        if count != 1:
            raise ValueError("Too many matches.  Failing")
        doc.pop("_id")
        atype = doc['type']
        func_name = atype.lower().replace("nmdc:", "")
        func = globals()[func_name]
        activity_records, data_object_records = func(db, doc, new_id)
        assocaited_data_object[col] =[activity_records]
        assocaited_data_object["data_object_set"].extend(data_object_records)
    json.dump(assocaited_data_object, open(f"{new_id}.json", "w"), indent=2)
    return assocaited_data_object


def minter(config,shoulder):
    """
    Creates a new ID based on the provided shoulder.
    
    Parameters:
    - shoulder: The base string for creating the new ID
    
    Returns:
    - A new ID string
    """
    
    runtime_api = NmdcRuntimeApi(config)
    
    return runtime_api.minter(shoulder)


def compute_new_paths(old_url, new_base_dir, omic_id, act_id):
    """
    Use the url to compute the new file name path and url
    """
    file_name = old_url.split("/")[-1]
    file_extenstion = file_name.lstrip("nmdc_").split("_", maxsplit=1)[-1]
    new_file_name = f"{act_id}_{file_extenstion}"
    destination = os.path.join(new_base_dir, new_file_name)
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


def copy_outputs(db, outputs, omic_id, act_id):
    """
    Copy output data objects and generate new metadata for them.
    
    Args:
    - db (MongoClient): MongoDB client instance to fetch data.
    - outputs (list): List of output object IDs.
    - omic_id (str): ID of the omics process.
    - act_id (str): ID of the activity.
    
    Returns:
    - tuple: List of new object IDs and the new objects themselves.
    """
    new_data_objects = []
    new_ids = []
    new_base_dir = os.path.join(base_dir, omic_id, act_id)
    os.makedirs(new_base_dir, exist_ok=True)
    for data_obj_id in outputs:
        data_obj = db.data_object_set.find_one({"id": data_obj_id})
        old_url = data_obj["url"]
        new_url, dst, new_fn = compute_new_paths(old_url, new_base_dir, omic_id, act_id)
        new_id = minter("dobj")
        log_mapping("data", data_obj["id"], new_id)

        # Create new obj
        data_obj.pop("_id")
        desc = data_obj["description"]
        data_obj["description"] = re.sub('[^ ]+$', f"{omic_id}", desc)
        data_obj["url"] = new_url
        data_obj["id"] = new_id
        data_obj["name"] = new_fn
        data_type = find_type(data_obj)
        data_obj["data_object_type"] = data_type

        # Link the file
        src = old_url.replace(base, base_dir)
        func_name = "bogus"
        if data_type:
            func_name = data_type.replace(" ", "_").lower()
        if func_name in globals():
            sys.stderr.write(f"Using func {func_name}\n")
            func = globals()[func_name]
            md5, size = func(src, dst, omic_id, act_id)
            data_obj["file_size_bytes"] = size
            data_obj["md5_checksum"] = md5
        else:
            os.link(src, dst)

        # Add to the lists
        new_ids.append(new_id)
        new_data_objects.append(data_obj)
    return new_ids, new_data_objects


def make_activity_set(nmdc_db, omics_id, has_input, has_output,workflow_record):
    database_activity_set = getattr(nmdc_db, workflow_record["Collection"])
    # Lookup the nmdc schema range class
    database_activity_range = getattr(nmdc_db, workflow_record["ActivityRange"])
    # Mint an ID
    new_id = minter(workflow_record["Type"])
    
    activity_id = new_id
    database_activity_set.append(
        database_activity_range(
            id=activity_id,
            name=workflow_record["Activity"]["name"].replace("{id}", activity_id),
            git_url=workflow_record["Git_repo"],
            version=workflow_record["Version"],
            part_of=[omics_id],
            execution_resource="Perlmutter - Nersc",
            started_at_time=datetime.datetime.now(pytz.utc).isoformat(),
            has_input=has_input,
            has_output=has_output,
            type=workflow_record["Type"],
            ended_at_time=datetime.datetime.now(pytz.utc).isoformat(),
            was_informed_by=omics_id,
        )
    )

def make_data_object(data_object_record, omics_id):

    nmdc_db.data_object_set.append(
        nmdc.DataObject(
            file_size_bytes=data_object_record["file_size"],
            name=data_object_record["data_object_name"],
            url=data_object_record["data_object_url"],
            data_object_type=["data_object_type"],
            type="nmdc:DataObject",
            id=minter("nmdc:DataObject"),
            md5_checksum=data_object_record["md5_checksum"],
            description=data_object_record["description"].replace(
                "{id}",omics_id
            ),
        )
    )

def post_database_object_to_runtime(datase_object):
    
    nmdc_database_object = json.loads(
            json_dumper.dumps(datase_object, inject_type=False)
        )
    res = runtime_api.post_objects(nmdc_database_object)
    return res

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
    mongo_url = os.environ["MONGO_URL"]
    client = MongoClient(mongo_url, directConnection=True)
    db = client.nmdc
    # Read mapping list
    # This should have:
    # was_informed_by_old\twas_informed_by_new
    # e.g.
    # nmdc:mga0xxxxx    nmdc:omprc-11-xxxxx
    omic_map = read_map()
    for omic in omic_map:
        process(db, omic, omic_map[omic])
    # for each omics process
    #     for act in [
