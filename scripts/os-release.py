#!/usr/bin/env python3

""" sends the os-release information to splunk """

import os
from json import dumps
import sys
from socket import gethostname
import time
import urllib.request
import urllib.error

from utils import config_loader

config = config_loader()

url = (
    f"https://{config.get('hec_host')}:{config.get('hec_port', 443)}/services/collector"
)

# get the data
if not os.path.exists("/etc/os-release"):
    print(f"Can't find /etc/os-release, quitting.", file=sys.stderr)
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
    "host": gethostname(),
    "index": config.get("hec_index"),
    "sourcetype": config.get("hec_sourcetype", "monitoring:osrelease"),
    "event": dumps(data),
}

# json is good
payload = dumps(params).encode("utf8")

# build the request
req = urllib.request.Request(url=url, data=payload)
req.add_header("Authorization", f"Splunk {config.get('hec_token')}")

try:
    response = urllib.request.urlopen(req)
    if '--debug' in sys.argv:
        print(response.text)
except urllib.error.HTTPError as error_message:
    print(f"HTTPError raised: {error_message}", file=sys.stderr)
    print(dir(error_message), file=sys.stderr)
    print(error_message.hdrs, file=sys.stderr)
    print(error_message.headers, file=sys.stderr)
    sys.exit(1)
