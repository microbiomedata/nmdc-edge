import os
import requests
from pymongo import MongoClient


_base_url = "https://data.microbiomedata.org/data"
_base_fn = "/global/cfs/cdirs/m3408/results"


def init_nmdc_mongo():
    url = os.environ["MONGO_URL"]
    client = MongoClient(url)
    nmdc = client.nmdc
    return nmdc


def do_line(line, cts):
    if line.find("ko=") > 0:
        annotations = line.split("\t")[8]
        for anno in annotations.split(";"):
            if anno.startswith("ko="):
                ko = anno[3:].replace("KO:", "KEGG.ORTHOLOGY")
                if ko not in cts:
                    cts[ko] = 0
                cts[ko] += 1
    return None


def get_kegg_counts(id, url):
    # Yes: We could do a json load but that can be slow for these large
    # files.  So let's just grab what we need
    cts = {}
    rows = []
    fn = url.replace(_base_url, _base_fn)

    if os.path.exists(fn):
        with open(fn) as f:
            for line in f:
                do_line(line, cts)
    else:
        # It looks like some of the data objects have
        # an error
        s = requests.Session()
        with s.get(url, headers=None, stream=True) as resp:
            if not resp.ok:
                print(f"Failed: {url}")
                return []
            for line in resp.iter_lines():
                do_line(line.decode(), cts)
    for func, ct in cts.items():
        rec = {"metagenome_annotation_id": id, "gene_function_id": func, "count": ct}
        rows.append(rec)
    print(f" - {len(rows)} terms")
    return rows


def find_anno(nmdc, dos):
    for doid in dos:
        do = nmdc.data_object_set.find_one({"id": doid})
        if "data_object_type" not in do:
            continue
        if do["data_object_type"] == "Functional Annotation GFF":
            return do["url"]
    return None


if __name__ == "__main__":
    nmdc = init_nmdc_mongo()
    act_recs = {}
    acts = []
    for actrec in nmdc.metagenome_annotation_activity_set.find({}):
        # New annotations should have this
        if "part_of" not in actrec:
            continue
        act = actrec["part_of"][0]
        acts.append(act)
        act_recs[act] = actrec

    print("Getting list of indexed objects")
    done = nmdc.functional_annotation_agg.distinct("metagenome_annotation_id")

    for act in acts:
        f = {"metagenome_annotation_id": act}
        if act in done:
            continue
        url = find_anno(nmdc, act_recs[act]["has_output"])
        url = url.replace("data/nmdc_mta", "data/nmdc:mta", 1)
        print(f"{act}: {url}")
        rows = get_kegg_counts(act, url)

        if len(rows) > 0:
            print(" - %s" % (str(rows[0])))
            nmdc.functional_annotation_agg.insert_many(rows)
        else:
            print(f" - No rows for {act}")

# Schema
#
#        metagenome_annotation_id        |   gene_function_id    | count
# ---------------------------------------+-----------------------+-------
#  nmdc:006424afe19af3c36c50e2b2e68b9510 | KEGG.ORTHOLOGY:K00001 |   145
