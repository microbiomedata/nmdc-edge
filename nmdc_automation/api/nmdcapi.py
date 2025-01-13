#!/usr/bin/env python

import json
import sys
import os
import urllib
from os.path import join, dirname
from urllib.parse import urlencode

from pydantic import BaseModel
import requests
import hashlib
import mimetypes
from pathlib import Path
from time import time
from typing import Union, List
from datetime import datetime, timedelta, timezone
from nmdc_automation.config import SiteConfig, UserConfig
import logging
from tenacity import retry, wait_exponential, stop_after_attempt


logging_level = os.getenv("NMDC_LOG_LEVEL", logging.DEBUG)
logging.basicConfig(
    level=logging_level, format="%(asctime)s %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

SECONDS_IN_DAY = 86400

def _get_sha256(fn: Union[str, Path]) -> str:
    """
    Helper function to get the sha256 hash of a file if it exists.
    """
    shahash = hashlib.sha256()
    if isinstance(fn, str):
        fn = Path(fn)
    hash_fn = fn.with_suffix(".sha256")
    if hash_fn.exists():
        with hash_fn.open() as f:
            sha = f.read().rstrip()
    else:
        logging.info(f"hashing {fn}")
        with fn.open("rb") as f:
            for byte_block in iter(lambda: f.read(1048576), b""):
                shahash.update(byte_block)
        sha = shahash.hexdigest()
        with hash_fn.open("w") as f:
            f.write(sha)
            f.write("\n")
    return sha

def expiry_dt_from_now(days=0, hours=0, minutes=0, seconds=0):
    return datetime.now(timezone.utc) + timedelta(days=days, hours=hours,
                                          minutes=minutes,
                              seconds=seconds)

class NmdcRuntimeApi:
    token = None
    expires_at = 0
    _base_url = None
    client_id = None
    client_secret = None

    def __init__(self, site_configuration: Union[str, Path, SiteConfig]):
        if isinstance(site_configuration, str) or isinstance(site_configuration, Path):
            site_configuration = SiteConfig(site_configuration)
        self.config = site_configuration
        self._base_url = self.config.api_url
        self.client_id = self.config.client_id
        self.client_secret = self.config.client_secret
        if self._base_url[-1] != "/":
            self._base_url += "/"

    def refresh_token(func):
        def _get_token(self, *args, **kwargs):
            # If it expires in 60 seconds, refresh
            if not self.token or self.expires_at < time() + 60:
                self.get_token()
            return func(self, *args, **kwargs)

        return _get_token

    @retry(wait=wait_exponential(multiplier=4, min=8, max=120), stop=stop_after_attempt(6), reraise=True)
    def get_token(self):
        """
        Get a token using a client id/secret.
        Retries up to 6 times with exponential backoff.
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

        resp = requests.post(url, headers=h, data=data)
        if not resp.ok:
            logging.error(f"Failed to get token: {resp.text}")
            resp.raise_for_status()
        response_body = resp.json()

        # Expires can be in days, hours, minutes, seconds - sum them up and convert to seconds
        expires = 0
        if "days" in response_body["expires"]:
            expires += int(response_body["expires"]["days"]) * SECONDS_IN_DAY
        if "hours" in response_body["expires"]:
            expires += int(response_body["expires"]["hours"]) * 3600
        if "minutes" in response_body["expires"]:
            expires += int(response_body["expires"]["minutes"]) * 60
        if "seconds" in response_body["expires"]:
            expires += int(response_body["expires"]["seconds"])

        self.expires_at = time() + expires

        self.token = response_body["access_token"]
        self.header = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer %s" % (self.token),
        }
        logging.debug(f"New token expires at {self.expires_at}")
        return response_body

    def get_header(self):
        return self.header

    @retry(wait=wait_exponential(multiplier=4, min=8, max=120), stop=stop_after_attempt(6), reraise=True)
    @refresh_token
    def minter(self, id_type, informed_by=None):
        url = f"{self._base_url}pids/mint"
        data = {"schema_class": {"id": id_type}, "how_many": 1}
        resp = requests.post(url, data=json.dumps(data), headers=self.header)
        if not resp.ok:
            logging.error(f"Response failed for: url: {url}, data: {data}, header: {self.header}")
            raise ValueError(f"Failed to mint ID of type {id_type} HTTP status: {resp.status_code} / ({resp.reason})")
        id = resp.json()[0]
        if informed_by:
            url = f"{self._base_url}pids/bind"
            data = {"id_name": id, "metadata_record": {"informed_by": informed_by}}
            resp = requests.post(url, data=json.dumps(data), headers=self.header)
            if not resp.ok:
                raise ValueError("Failed to bind metadata to pid")
        return id

    @retry(wait=wait_exponential(multiplier=4, min=8, max=120), stop=stop_after_attempt(6), reraise=True)
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
        if not resp.ok:
            resp.raise_for_status()
        return resp.json()

    @retry(wait=wait_exponential(multiplier=4, min=8, max=120), stop=stop_after_attempt(6), reraise=True)
    @refresh_token
    def get_object(self, obj, decode=False):
        """
        Helper function to get object info
        """
        url = "%sobjects/%s" % (self._base_url, obj)
        resp = requests.get(url, headers=self.header)
        if not resp.ok:
            resp.raise_for_status()
        data = resp.json()
        if decode and "description" in data:
            try:
                data["metadata"] = json.loads(data["description"])
            except Exception:
                data["metadata"] = None

        return data


    @retry(wait=wait_exponential(multiplier=4, min=8, max=120), stop=stop_after_attempt(6), reraise=True)
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
        if not resp.ok:
            resp.raise_for_status()
        return resp.json()

    @retry(wait=wait_exponential(multiplier=4, min=8, max=120), stop=stop_after_attempt(6), reraise=True)
    @refresh_token
    def post_objects(self, obj_data):
        url = self._base_url + "workflows/workflow_executions"

        resp = requests.post(url, headers=self.header, data=json.dumps(obj_data))
        if not resp.ok:
            resp.raise_for_status()
        return resp.json()

    @retry(wait=wait_exponential(multiplier=4, min=8, max=120), stop=stop_after_attempt(6), reraise=True)
    @refresh_token
    def set_type(self, obj, typ):
        url = "%sobjects/%s/types" % (self._base_url, obj)
        d = [typ]
        resp = requests.put(url, headers=self.header, data=json.dumps(d))
        if not resp.ok:
            resp.raise_for_status()
        return resp.json()

    @retry(wait=wait_exponential(multiplier=4, min=8, max=120), stop=stop_after_attempt(6), reraise=True)
    @refresh_token
    def bump_time(self, obj):
        url = "%sobjects/%s" % (self._base_url, obj)
        now = datetime.today().isoformat()
        d = {"created_time": now}
        resp = requests.patch(url, headers=self.header, data=json.dumps(d))
        if not resp.ok:
            resp.raise_for_status()
        return resp.json()

    # TODO test that this concatenates multi-page results
    @retry(wait=wait_exponential(multiplier=4, min=8, max=120), stop=stop_after_attempt(6), reraise=True)
    @refresh_token
    def list_jobs(self, filt=None, max=100) -> List[dict]:
        url = "%sjobs?max_page_size=%s" % (self._base_url, max)
        d = {}
        if filt:
            url += "&filter=%s" % (json.dumps(filt))
        orig_url = url
        results = []
        while True:
            resp = requests.get(url, data=json.dumps(d), headers=self.header)
            if resp.status_code != 200:
                resp.raise_for_status()
            try:
                response_json = resp.json()
            except Exception as e:
                logging.error(f"Failed to parse response: {resp.text}")
                raise e
            if "resources" not in response_json:
                logging.warning(str(response_json))
                break
            results.extend(response_json["resources"])
            if "next_page_token" not in response_json or not response_json["next_page_token"]:
                break
            url = orig_url + "&page_token=%s" % (response_json["next_page_token"])
        return results

    @retry(wait=wait_exponential(multiplier=4, min=8, max=120), stop=stop_after_attempt(6), reraise=True)
    @refresh_token
    def get_job(self, job_id: str):
        url = "%sjobs/%s" % (self._base_url, job_id)
        resp = requests.get(url, headers=self.header)
        if not resp.ok:
            resp.raise_for_status
        return resp.json()

    @retry(wait=wait_exponential(multiplier=4, min=8, max=120), stop=stop_after_attempt(6), reraise=True)
    @refresh_token
    def claim_job(self, job_id: str):
        url = "%sjobs/%s:claim" % (self._base_url, job_id)
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

    @retry(wait=wait_exponential(multiplier=4, min=8, max=120), stop=stop_after_attempt(6), reraise=True)
    @refresh_token
    def list_objs(self, filt=None, max_page_size=40):
        url = "%sobjects?max_page_size=%d" % (self._base_url, max_page_size)
        if filt:
            url += "&filter=%s" % (json.dumps(filt))
        results = self._page_query(url)
        return results

    @retry(wait=wait_exponential(multiplier=4, min=8, max=120), stop=stop_after_attempt(6), reraise=True)
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

    @retry(wait=wait_exponential(multiplier=4, min=8, max=120), stop=stop_after_attempt(6), reraise=True)
    @refresh_token
    def get_op(self, opid):
        url = "%soperations/%s" % (self._base_url, opid)
        resp = requests.get(url, headers=self.header)
        if not resp.ok:
            resp.raise_for_status()
        return resp.json()

    @retry(wait=wait_exponential(multiplier=4, min=8, max=120), stop=stop_after_attempt(6), reraise=True)
    @refresh_token
    def update_op(self, opid, done=None, results=None, meta=None):
        """
        Update an operation with the given ID with the specified parameters.
        Returns the updated operation.
        """
        url = "%soperations/%s" % (self._base_url, opid)
        d = dict()
        if done is not None:
            d["done"] = done
        if results:
            d["result"] = results
        if meta:
            # Need to preserve the existing metadata
            cur = self.get_op(opid)
            if not cur.get("metadata"):
                # this means we messed up the record before.
                # This can't be fixed so just return
                return None
            d["metadata"] = cur["metadata"]
            d["metadata"]["extra"] = meta
        resp = requests.patch(url, headers=self.header, data=json.dumps(d))
        if not resp.ok:
            resp.raise_for_status()
        return resp.json()

    @retry(wait=wait_exponential(multiplier=4, min=8, max=120), stop=stop_after_attempt(6), reraise=True)
    @refresh_token
    def run_query(self, query):
        url = "%squeries:run" % self._base_url
        resp = requests.post(url, headers=self.header, data=json.dumps(query))
        if not resp.ok:
            resp.raise_for_status()
        return resp.json()

    @retry(wait=wait_exponential(multiplier=4, min=8, max=120), stop=stop_after_attempt(6), reraise=True)
    @refresh_token
    def find_planned_processes(self, filter: dict):
        # construct filter params
        filter_parts = []
        for k, v in filter.items():
            filter_parts.append(f"{k}:{v}")
        filter_terms = ",".join(filter_parts)
        params = {
            "filter": filter_terms,
            "per_page": 100,
        }
        encoded_params = urllib.parse.urlencode(params)
        url = f"{self._base_url}planned_processes?{encoded_params}"
        logger.info(url)
        resp = requests.get(url, headers=self.header)
        if not resp.ok:
            resp.raise_for_status()
        return resp.json()

def jprint(obj):
    print(json.dumps(obj, indent=2))


def usage():
    print("usage: ....")
