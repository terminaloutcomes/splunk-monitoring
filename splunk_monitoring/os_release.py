#!/usr/bin/env python3
#pylint: disable=invalid-name

""" sends the os-release information to splunk """

import json
from pathlib import Path
import sys
from socket import gethostname
import time
from typing import Any, Dict

from .utils import config_loader, send_hec


def cli() -> None:
    """CLI Interface"""
    config = config_loader()


    osrel = Path("/etc/os-release")
    # get the data
    if not osrel.exists():
        print(f"Can't find {osrel.as_posix()}, quitting.", file=sys.stderr)
        sys.exit(1)

    with osrel.open(encoding="utf8") as file_handle:
        lines = [ line.strip() for line in file_handle.readlines() if not line.strip().startswith("#") ]

    data: Dict[str, Any] = {}

    for line in lines:
        key, value = line.split("=")
        key = key.replace("\"", "")
        value = value.replace("\"", "")
        if key in data:
            print(f"Key {key} already found in data, old={data['key']} new={value}")
        data[key] = value

    payload = {
        "time": time.time(),
        "host": gethostname(),
        "index": config.get("hec_index"),
        "sourcetype": config.get("hec_sourcetype_os_release", "monitoring:osrelease"),
        "event": data,
    }

    if '--debug' in sys.argv:
        print(json.dumps(payload, indent=4, default=str))

    send_hec(config=config, payload=payload)

if __name__ == "__main__":
    cli()
