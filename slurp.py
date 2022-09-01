import json
import os
from pymongo import MongoClient
import sys
from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


def init_nmdc_mongo():
    url = os.environ['MONGO_URL']
    client = MongoClient(url)
    nmdc = client.nmdc
    return nmdc

_sets = ['metagenome_annotation_activity_set',
         'metagenome_assembly_set',
         'mags_activity_set',
         'read_QC_analysis_activity_set']

if __name__ == "__main__":

    nmdc = init_nmdc_mongo()
    ids = ["gold:Gp0213371"]
    dos = []
    sets_out = dict()
    for s in _sets:
        sets_out[s] = []
        for gid in ids:
            q = {"was_informed_by": gid}
            for d in nmdc[s].find(q):
                sets_out[s].append(d)
                d.pop("_id")
                dos.extend(d['has_input'])
                dos.extend(d['has_output'])
    done = dict()
    s = "data_object_set"
    sets_out[s] = []
    for do in dos:
        if do in done:
            continue
        doc = nmdc.data_object_set.find_one({"id": do})
        doc.pop("_id")
        sets_out[s].append(doc)
        done[do] = 1
    for s, docs in sets_out.items():
        json.dump(docs, open("%s.json" % (s), "w"), indent=2)
