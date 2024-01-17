# -*- coding: utf-8 -*-
"""Client for the NMDC API."""
# TODO: move all of this to a separate project nmdc-common. But for now, just
# copy it here.

import logging
import requests
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NmdcApi:
    """
    Basic API Client for GET requests.
    """

    def __init__(self, api_base_url):
        if not api_base_url.endswith("/"):
            api_base_url += "/"
        self.base_url = api_base_url
        self.headers = {'accept': 'application/json', 'Content-Type': 'application/json'}


    def get_biosamples_part_of_study(self, study_id: str) -> list[dict]:
        """
        Get the biosamples that are part of a study.
        """
        biosample_records = []
        params = {
            'filter': '{"part_of": "'+study_id+'"}',
            'max_page_size': '1000',
        }
        url = self.base_url + "nmdcschema/biosample_set"
        response = requests.get(url, params=params, headers=self.headers)
        response.raise_for_status()
        biosample_records.extend(response.json()["resources"])
        # Get the next page of results, if any
        while response.json().get("next_page_token") is not None:
            params['page_token'] = response.json()["next_page_token"]
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            biosample_records.extend(response.json()["resources"])


        return biosample_records

    def get_omics_processing_records_part_of_study(self, study_id: str) -> list[dict]:
        """
        Get the OmicsProcessing records that are part of a study.
        """
        omics_processing_records = []
        params = {
            'filter': '{"part_of": "'+study_id+'"}',
            'max_page_size': '1000',
        }
        url = self.base_url + "nmdcschema/omics_processing_set"
        response = requests.get(url, params=params, headers=self.headers)
        response.raise_for_status()
        omics_processing_records.extend(response.json()["resources"])
        # Get the next page of results, if any
        while response.json().get("next_page_token") is not None:
            params['page_token'] = response.json()["next_page_token"]
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            omics_processing_records.extend(response.json()["resources"])
        return omics_processing_records

    def get_workflow_activities_informed_by(self, workflow_activity_set: str,
                                            informed_by_id: str) -> list[dict]:
            """
            Retrieve workflow activity record(s) for the given workflow
            activity set and informed by a given OmicsProcessing ID.
            """
            params = {
                'filter': '{"was_informed_by": "'+informed_by_id+'"}',
            }
            url = self.base_url + "nmdcschema/" + workflow_activity_set
            response = requests.get(url, params=params, headers=self.headers)
            logger.info(response.url)
            response.raise_for_status()
            workflow_activity_record = response.json()["resources"]
            return workflow_activity_record

    def get_data_object(self, data_object_id: str) -> Optional[dict]:
        """
        Retrieve a data object record by ID.
        """
        url = self.base_url + "nmdcschema/data_object_set/" + data_object_id
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data_object_record = response.json()
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 404:
                return None
            else:
                raise
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        data_object_record = response.json()
        return data_object_record

    def get_data_objects_by_description(self, description: str):
        """
        Retrieve data object records by description.
        """
        params = {
            'filter': '{"description.search": "'+description+'"}',
        }
        url = self.base_url + "data_objects"
        response = requests.get(url, params=params, headers=self.headers)
        response.raise_for_status()
        data_object_records = response.json()["results"]
        return data_object_records
