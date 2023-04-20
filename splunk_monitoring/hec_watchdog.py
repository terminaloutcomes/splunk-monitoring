#!/usr/bin/env python3
#pylint: disable=invalid-name

""" sends a ping to splunk to say hello """

import sys
from socket import gethostname
import time
from typing import List, Optional

import click
import schedule # type: ignore

from .utils import config_loader, send_hec, ConfigFileType, setup_logging


def check_config(config_dict: ConfigFileType) -> None:
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

def send_ping(config_dict: ConfigFileType) -> None:
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
    config_dict: ConfigFileType,
    ) -> None:
    """ loops and tings """
    schedule.every(int(config_dict["seconds"])).seconds.do(
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
@click.option("--debug", is_flag=True, default=False, help="Turn on debug logging")
@click.option("--seconds", "-s", type=int, help="If in daemon mode, how many seconds between runs. Can be specified in config as 'seconds' which this overrides, default is 300.")
@click.option("--print-ping", "-p", is_flag=True, help="Prints ping/pong when sending/succesfully sent.")
def cli(
    daemon: bool=False,
    seconds: Optional[int]=None,
    print_ping: bool=False,
    debug: bool=False,
    ) -> None:
    """ Sends a ping to your Splunk instance over the HTTP Event Collector to say hello. """
    setup_logging(debug)
    config = config_loader()
    check_config(config)

    if seconds is not None:
        config["seconds"] = seconds
    elif "seconds" not in config:
        config["seconds"] = 300

    config["print_ping"] = print_ping

    # we're sending a ping to start with either way.
    send_ping(config)

    if daemon:
        loop(config)
