"""
utilities for splunk-monitoring

copyright James Hodgkinson 2021
"""

import json
import sys
from typing import Any, Dict, Union
from pathlib import Path

import urllib.request
import urllib.error
import backoff
from loguru import logger

CONFIG_FILES = [
    "/etc/splunk-monitoring/config.json",
    "~/.config/splunk-monitoring.json",
    "./config.json",
]

ConfigFileType = Dict[str, Union[str, int]]


def config_loader() -> ConfigFileType:
    """find and load the config, returns a dict of config"""
    for config_file in CONFIG_FILES:
        filepath = Path(config_file)
        if filepath.exists():
            with filepath.open(encoding="utf8") as filehandle:
                result: Dict[str, Union[str, int]] = json.load(filehandle)
                return result

    sys.exit(f"Failed to find config file, quitting (tried: {CONFIG_FILES}")


def url(config: ConfigFileType) -> str:
    """makes a url"""
    if "hec_host" not in config:
        raise ValueError("hec_host missing in config file")

    return (
        f"https://{config['hec_host']}:{config.get('hec_port', 443)}/services/collector"
    )


@backoff.on_exception(backoff.expo, (urllib.error.HTTPError, urllib.error.URLError))
def send_hec(
    config: ConfigFileType, payload: Dict[str, Any], debug: bool = False
) -> None:
    """sends a thing to the HEC endpoint"""

    data = json.dumps(payload, default=str, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(url=url(config), data=data)
    req.add_header("Authorization", f"Splunk {config.get('hec_token')}")

    with urllib.request.urlopen(req) as response:
        if debug:
            print(response.read())


def setup_logging(debug: bool = False) -> None:
    """sets up loguru"""
    if not debug:
        logger.remove()
        logger.add(sink=sys.stderr, level="INFO")
