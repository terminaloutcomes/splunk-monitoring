"""
utilities for splunk-monitoring

copyright James Hodgkinson 2021
"""

import json
import os
import sys

CONFIG_FILES = [
    "/etc/splunk-monitoring/config.json",
    "./config.json"
]

def config_loader():
    """ find and load the config, returns a dict of config """
    for config_file in CONFIG_FILES:
        if os.path.exists(config_file):
            with open(config_file, 'r') as filehandle:
                return json.load(filehandle)

    sys.exit(f"Failed to find config file, quitting (tried: {CONFIG_FILES}")

def url(config):
    """ makes a url """
    return (
        f"https://{config.get('hec_host')}:{config.get('hec_port', 443)}/services/collector"
    )
