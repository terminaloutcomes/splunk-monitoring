#!/usr/bin/env python3
#pylint: disable=invalid-name

""" sends the os-release information to splunk """

import os
from json import dumps
import sys
from socket import getfqdn
import time
import urllib.request
import urllib.error

from utils import config_loader, url

config = config_loader()


# get the data
if not os.path.exists("/etc/os-release"):
    print("Can't find /etc/os-release, quitting.", file=sys.stderr)
    sys.exit(1)

with open("/etc/os-release", "r") as file_handle:
    lines = [ line.strip() for line in file_handle.readlines() if not line.strip().startswith("#") ]

data = {}

for line in lines:
    key, value = line.split("=")
    key = key.replace("\"", "")
    value = value.replace("\"", "")
    if key in data:
        print(f"Key {key} already found in data, old={data['key']} new={value}")
    data[key] = value

params = {
    "time": time.time(),
    "host": getfqdn(),
    "index": config.get("hec_index"),
    "sourcetype": config.get("hec_sourcetype_os_release", "monitoring:osrelease"),
    "event": data,
}

# json is good
payload = dumps(params).encode("utf8")
if '--debug' in sys.argv:
    print(payload)

# build the request
req = urllib.request.Request(url=url(config), data=payload)
req.add_header("Authorization", f"Splunk {config.get('hec_token')}")

try:
    with urllib.request.urlopen(req) as response:
        if '--debug' in sys.argv:
            print(response.read())
except urllib.error.HTTPError as error_message:
    print(f"HTTPError raised: {error_message}", file=sys.stderr)
    print(dir(error_message), file=sys.stderr)
    print(error_message.hdrs, file=sys.stderr)
    print(error_message.headers, file=sys.stderr)
    sys.exit(1)
