#!/usr/bin/env python3

""" sends a ping to splunk to say hello """

from json import dumps, loads
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

params = {
    "time": time.time(),
    "host": gethostname(),
    "index": config.get("hec_index"),
    "sourcetype": config.get("hec_sourcetype", "monitoring:watchdog"),
    "event": "ping",
}

# json is good
data = dumps(params).encode("utf8")

# build the request
req = urllib.request.Request(url=url, data=data)
req.add_header("Authorization", f"Splunk {config.get('hec_token')}")

try:
    response = urllib.request.urlopen(req)
except urllib.error.HTTPError as error_message:
    print(f"HTTPError raised: {error_message}")
    print(dir(error_message))
    print(error_message.hdrs)
    print(error_message.headers)
    sys.exit()
#response_data = loads(response.read())
#if response_data.get('text') != "Success" or response_data.get('code', False) == 0:
#    print(response_data)
#    sys.exit(1)
