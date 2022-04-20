"""
utilities for splunk-monitoring

copyright James Hodgkinson 2021
"""

import json
import sys
from typing import Any, Dict
from pathlib import Path

import urllib.request
import urllib.error


CONFIG_FILES = [
    "/etc/splunk-monitoring/config.json",
    "~/.config/splunk-monitoring.json",
    "./config.json"
]

def config_loader() -> Dict:
    """ find and load the config, returns a dict of config """
    for config_file in CONFIG_FILES:
        filepath = Path(config_file)
        if filepath.exists():
            with filepath.open(encoding="utf8") as filehandle:
                return json.load(filehandle)

    sys.exit(f"Failed to find config file, quitting (tried: {CONFIG_FILES}")

def url(config):
    """ makes a url """
    return (
        f"https://{config.get('hec_host')}:{config.get('hec_port', 443)}/services/collector"
    )



def send_hec(config: Dict[str, Any], payload: Dict[str, Any]):
    """ sends a thing to the HEC endpoint """

    data = json.dumps(payload, default=str, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(url=url(config), data=data)
    req.add_header("Authorization", f"Splunk {config.get('hec_token')}")

    try:
        with urllib.request.urlopen(req) as response:
            if '--debug' in sys.argv:
                print(response.read())
    except urllib.error.HTTPError as error_message:
        print(f"HTTPError raised: {error_message}", file=sys.stderr)
        print(dir(error_message), file=sys.stderr)
        if hasattr(error_message, "headers"):
            print(error_message.headers, file=sys.stderr)
        sys.exit(1)