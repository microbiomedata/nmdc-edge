#!/usr/bin/env python

import json
import sys
import os
from os.path import join, dirname
import requests
import hashlib
import mimetypes
from time import time
from datetime import datetime
from nmdc_automation.config import Config
import logging


def _get_sha256(fn):
    hashfn = fn + ".sha256"
    if os.path.exists(hashfn):
        with open(hashfn) as f:
            sha = f.read().rstrip()
    else:
        logging.info("hashing %s" % (fn))
        shahash = hashlib.sha256()
        with open(fn, "rb") as f:
            # Read and update hash string value in blocks of 4K
            for byte_block in iter(lambda: f.read(1048576), b""):
                shahash.update(byte_block)
        sha = shahash.hexdigest()
        with open(hashfn, "w") as f:
            f.write(sha)
            f.write("\n")
    return sha


class NmdcRuntimeApi:
    token = None
    expires = 0
    _base_url = None
    client_id = None
    client_secret = None

    def __init__(self, site_configuration):
        self.config = Config(site_configuration)
        self._base_url = self.config.api_url
        self.client_id = self.config.client_id
        self.client_secret = self.config.client_secret
        if self._base_url[-1] != "/":
            self._base_url += "/"

    def refresh_token(func):
        def _get_token(self, *args, **kwargs):
            # If it expires in 60 seconds, refresh
            if not self.token or self.expires + 60 > time():
                self.get_token()
            return func(self, *args, **kwargs)

        return _get_token

    def get_token(self):
        """
        Get a token using a client id/secret.
        """
        h = {
            "accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        url = self._base_url + "token"
        resp = requests.post(url, headers=h, data=data).json()
        expt = resp["expires"]
        self.expires = time() + expt["minutes"] * 60

        self.token = resp["access_token"]
        self.header = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer %s" % (self.token),
        }
        return resp

    def get_header(self):
        return self.header

    @refresh_token
    def minter(self, id_type, informed_by=None):
        url = f"{self._base_url}pids/mint"
        data = {"schema_class": {"id": id_type}, "how_many": 1}
        resp = requests.post(url, data=json.dumps(data), headers=self.header)
        if not resp.ok:
            raise ValueError("Failed to mint ID")
        id = resp.json()[0]
        if informed_by:
            url = f"{self._base_url}pids/bind"
            data = {"id_name": id, "metadata_record": {"informed_by": informed_by}}
            resp = requests.post(url, data=json.dumps(data), headers=self.header)
            if not resp.ok:
                raise ValueError("Failed to bind metadata to pid")
        return id

    @refresh_token
    def mint(self, ns, typ, ct):
        """
        Mint a new ID.
        Inputs: token (obtained using get_token)
                namespace (e.g. nmdc)
                type/shoulder (e.g. mga0, mta0)
                count/number of IDs to generate
        """
        url = self._base_url + "ids/mint"
        d = {"populator": "", "naa": ns, "shoulder": typ, "number": ct}
        resp = requests.post(url, headers=self.header, data=json.dumps(d))
        return resp.json()

    @refresh_token
    def get_object(self, obj, decode=False):
        """
        Helper function to get object info
        """
        url = "%sobjects/%s" % (self._base_url, obj)
        resp = requests.get(url, headers=self.header)
        data = resp.json()
        if decode and "description" in data:
            try:
                data["metadata"] = json.loads(data["description"])
            except Exception:
                data["metadata"] = None

        return data

    @refresh_token
    def create_object(self, fn, description, dataurl):
        """
        Helper function to create an object.
        """
        url = self._base_url + "objects"
        fmeta = os.stat(fn)
        name = os.path.split(fn)[-1]
        mtypes = mimetypes.MimeTypes().guess_type(fn)
        if mtypes[1] is None:
            mt = mtypes[0]
        else:
            mt = "application/%s" % (mtypes[1])

        sha = _get_sha256(fn)
        now = datetime.today().isoformat()
        d = {
            "aliases": None,
            "description": description,
            "mime_type": mt,
            "name": name,
            "access_methods": [
                {
                    "access_id": None,
                    "access_url": {
                        "url": dataurl,
                    },
                    "region": None,
                    "type": "https",
                }
            ],
            "checksums": [{"checksum": sha, "type": "sha256"}],
            "contents": None,
            "created_time": now,
            "size": fmeta.st_size,
            "updated_time": None,
            "version": None,
            "id": sha,
            "self_uri": "todo",
        }
        resp = requests.post(url, headers=self.header, data=json.dumps(d))
        return resp.json()

    @refresh_token
    def post_objects(self, obj_data, json_obj=None):
        url = self._base_url + "v1/workflows/activities"

        # objects_file = open(json_obj)
        # obj_data = json.load(objects_file)

        resp = requests.post(url, headers=self.header, data=json.dumps(obj_data))
        return resp.json()

    @refresh_token
    def set_type(self, obj, typ):
        url = "%sobjects/%s/types" % (self._base_url, obj)
        d = [typ]
        resp = requests.put(url, headers=self.header, data=json.dumps(d))
        return resp.json()

    @refresh_token
    def bump_time(self, obj):
        url = "%sobjects/%s" % (self._base_url, obj)
        now = datetime.today().isoformat()

        d = {"created_time": now}
        resp = requests.patch(url, headers=self.header, data=json.dumps(d))
        return resp.json()

    @refresh_token
    def list_jobs(self, filt=None, max=20):
        url = "%sjobs?max_page_size=%s" % (self._base_url, max)
        d = {}
        if filt:
            url += "&filter=%s" % (json.dumps(filt))
        orig_url = url
        results = []
        while True:
            resp = requests.get(url, data=json.dumps(d), headers=self.header).json()
            if "resources" not in resp:
                logging.warning(str(resp))
                break
            results.extend(resp["resources"])
            if "next_page_token" not in resp or not resp["next_page_token"]:
                break
            url = orig_url + "&page_token=%s" % (resp["next_page_token"])
        return results

    @refresh_token
    def get_job(self, job):
        url = "%sjobs/%s" % (self._base_url, job)
        resp = requests.get(url, headers=self.header)
        return resp.json()

    @refresh_token
    def claim_job(self, job):
        url = "%sjobs/%s:claim" % (self._base_url, job)
        resp = requests.post(url, headers=self.header)
        if resp.status_code == 409:
            claimed = True
        else:
            claimed = False
        data = resp.json()
        data["claimed"] = claimed
        return data

    def _page_query(self, url):
        orig_url = url
        results = []
        while True:
            resp = requests.get(url, headers=self.header).json()
            if "resources" not in resp:
                logging.warning(str(resp))
                break
            results.extend(resp["resources"])
            if "next_page_token" not in resp or not resp["next_page_token"]:
                break
            url = orig_url + "&page_token=%s" % (resp["next_page_token"])
        return results

    @refresh_token
    def list_objs(self, filt=None, max_page_size=40):
        url = "%sobjects?max_page_size=%d" % (self._base_url, max_page_size)
        if filt:
            url += "&filter=%s" % (json.dumps(filt))
        results = self._page_query(url)
        return results

    @refresh_token
    def list_ops(self, filt=None, max_page_size=40):
        url = "%soperations?max_page_size=%d" % (self._base_url, max_page_size)
        d = {}
        if filt:
            url += "&filter=%s" % (json.dumps(filt))
        orig_url = url
        results = []
        while True:
            resp = requests.get(url, data=json.dumps(d), headers=self.header).json()
            if "resources" not in resp:
                logging.warning(str(resp))
                break
            results.extend(resp["resources"])
            if "next_page_token" not in resp or not resp["next_page_token"]:
                break
            url = orig_url + "&page_token=%s" % (resp["next_page_token"])
        return results

    @refresh_token
    def get_op(self, opid):
        url = "%soperations/%s" % (self._base_url, opid)
        resp = requests.get(url, headers=self.header)
        return resp.json()

    @refresh_token
    def update_op(self, opid, done=None, results=None, meta=None):
        url = "%soperations/%s" % (self._base_url, opid)
        d = dict()
        if done is not None:
            d["done"] = done
        if results:
            d["result"] = results
        if meta:
            # Need to preserve the existing metadata
            cur = self.get_op(opid)
            if not cur["metadata"]:
                # this means we messed up the record before.
                # This can't be fixed so just return
                return None
            d["metadata"] = cur["metadata"]
            d["metadata"]["extra"] = meta
        resp = requests.patch(url, headers=self.header, data=json.dumps(d))
        return resp.json()

    @refresh_token
    def run_query(self, query):
        url = "%squeries:run" % self._base_url
        resp = requests.post(url, headers=self.header, data=json.dumps(query))
        return resp.json()


def jprint(obj):
    print(json.dumps(obj, indent=2))


def usage():
    print("usage: ....")
