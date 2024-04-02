"""
Python client for Ex Libris Alma
"""
__author__ = "Steve Pelkey (spelkey@ucdavis.edu)"
__version__ = "0.0.9"

import os

from .client import Client
from .bibs import SubClientBibs
from .analytics import SubClientAnalytics
from . import utils


class AlmaCnxn(Client):
    """"Interface with Alma APIs.

    Various Apis are namespaced beneath this object according to documentation
    at https://developers.exlibrisgroup.com/alma/apis.

    E.g.
    > connection = AlmaCnxn(your_api_key)
    > connection.bibs.catalog.get_record(bib_id) # returns bibliographic records

    Args:
        api_key (str): Your Api Key
        Location (str): Geographic location of library.
        data_format (str): Format of returned data. json or xml.
            If xml is selected, data will be returned as python xml ElementTree.
    """

    def __init__(self, apikey, location='America', data_format='json'):

        super(AlmaCnxn, self).__init__()

        # determine base uri based on location
        locations = {'America': 'https://api-na.hosted.exlibrisgroup.com',
                     'Europe': 'https://api-eu.hosted.exlibrisgroup.com',
                     'Asia Pacific': 'https://api-ap.hosted.exlibrisgroup.com',
                     'Canada': 'https://api-ca.hosted.exlibrisgroup.com',
                     'China': 'https://api-cn.hosted.exlibrisgroup.com'}
        if location != 'America':
            if location not in locations.keys():
                message = "Valid location arguments are "
                message += ", ".join(locations.keys())
                raise utils.ArgError(message=message)
        self.cnxn_params['location'] = location
        self.cnxn_params['base_uri'] = locations[location]

        # handle preferred format
        if data_format not in ['json', 'xml']:
            message = "Format argument must be either 'json' or 'xml'"
            raise utils.ArgError(message)
        self.cnxn_params['format'] = data_format
        ns = {'header': 'http://com/exlibris/urm/general/xmlbeans'}
        self.cnxn_params['xml_ns'] = ns

        # TODO: validate api key. return list of accessible endpoints
        # call __validate_key__
        self.cnxn_params['api_key'] = apikey

        # Hook in the various Alma APIs based on what API key can access
        self.bibs = SubClientBibs(self.cnxn_params)
        self.analytics = SubClientAnalytics(self.cnxn_params)

    def __validate_key__(self, apikey):
        # loop through each api and access the /test endpoint.
        # return list of accessible apis.
        pass