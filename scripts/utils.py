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
            return json.load(open(config_file, 'r'))

    sys.exit("Failed to find config file, quitting")
