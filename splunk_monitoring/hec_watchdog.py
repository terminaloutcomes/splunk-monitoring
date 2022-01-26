#!/usr/bin/env python3
#pylint: disable=invalid-name

""" sends a ping to splunk to say hello """

import sys
from socket import gethostname
import time
from typing import Dict, List, Optional, Union

import click
import schedule

from .utils import config_loader, send_hec


def check_config(config_dict: Dict[str, str]) -> None:
    """ checks config options """
    missing_options: List[str] = []
    for key in [
        "hec_index",
        "hec_host",
        "hec_token",
    ]:
        if key not in config_dict:
            missing_options.append(key)

    if missing_options:
        raise ValueError(f"The following keys are missing from the config: {','.join(missing_options)}")

def send_ping(config_dict: Dict[str, str]):
    """ does the sendy bit"""


    params = {
        "time": time.time(),
        "host": gethostname(),
        "index": config_dict["hec_index"],
        "sourcetype": config_dict.get("hec_sourcetype", "monitoring:watchdog"),
        "event": "ping",
    }

    if config_dict["print_ping"]:
        print("ping")
    send_hec(config=config_dict, payload=params)
    if config_dict["print_ping"]:
        print("pong")

def loop(
    config_dict: Dict[str,Union[int, str]],
    ):
    """ loops and tings """
    schedule.every(config_dict["seconds"]).seconds.do(
        send_ping,
        config_dict=config_dict,
        )
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        sys.exit()

@click.command()
@click.option("--daemon", is_flag=True, default=False, help="Runs on a loop")
@click.option("--seconds", "-s", type=int, help="If in daemon mode, how many seconds between runs. Can be specified in config as 'seconds' which this overrides, default is 300.")
@click.option("--print-ping", "-p", is_flag=True, help="Prints ping/pong when sending/succesfully sent.")
def cli(daemon: bool, seconds: Optional[int], print_ping: bool):
    """ Sends a ping to your Splunk instance over the HTTP Event Collector to say hello. """
    config = config_loader()
    check_config(config)

    if seconds:
        config["seconds"] = seconds
    elif "seconds" not in config:
        config["seconds"] = 300

    config["print_ping"] = print_ping

    # we're sending a ping to start with either way.
    send_ping(config)

    if daemon:
        loop(config)
