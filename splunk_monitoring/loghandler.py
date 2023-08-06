#!/usr/bin/env python3

""" Splunk log parser, you can filter by component, time etc. """

from datetime import datetime, timedelta
from io import TextIOWrapper
from json import dumps
from pathlib import Path
import re
import sys
from typing import Any, Dict, Optional

import click
from loguru import logger

from .utils import setup_logging


def regex_kv_pairs(
    text: str, item_sep: str = r"\s", value_sep: str = "="
) -> Dict[str, Any]:
    """
    Parse key-value pairs from a shell-like text with regex.
    This approach is ~ 25 times faster than the shlex approach.
    Returns a dict with the keys and values from the text input
    """

    split_regex = r"""
        (?P<key>[\w\-]+)=       # Key consists of only alphanumerics and '-' character
        (?P<quote>["']?)        # Optional quote character.
        (?P<value>[\S\s]*?)     # Value is a non greedy match
        (?P=quote)              # Closing quote equals the first.
        (,|$|\s)                # Entry ends with comma or end of string
    """.replace(
        "=", value_sep
    ).replace(
        r"|\s)", f"|{item_sep})"
    )
    kv_regex = re.compile(split_regex, re.VERBOSE)

    return {
        match.group("key"): match.group("value") for match in kv_regex.finditer(text)
    }


# pylint: disable=line-too-long
# example_log = '10-03-2021 08:48:24.792 +1000 ERROR HttpInputDataHandler [2394001 HttpInputServerDataThread] - Failed processing http input, token name=test, channel=n/a, source_IP=10.0.0.123, reply=9, events_processed=0, http_input_body_size=183414, parsing_err="Server is busy"' #noqa: E501

# pylint: disable=line-too-long
regex = re.compile(
    r"^(?P<timestamp>(?P<date>\S+) (?P<time_hour>\d+):(?P<time_minute>\d+):(?P<time_second>[\d\.]+) (?P<time_zone_offset>\S+)) (?P<log_level>\w+)\s+(?P<component>\S+)\s+(?P<event>.*)"
)


# pylint: disable=too-many-arguments,too-many-locals,too-many-branches
@click.command()
@click.option("--mins", default=5, help="Look back this many minutes")
@click.option("--ignore_mins", default=0, help="Ignore the last x minutes")
@click.option("--component")
@click.option("--debug", is_flag=True, default=False)
@click.option("--count", is_flag=True, default=False)
@click.option("--json", is_flag=True, default=False)
@click.option("--filename", type=click.File("r"), default=False)
def cli(
    mins: int = 5,
    ignore_mins: int = 0,
    component: Optional[str] = None,
    debug: bool = False,
    count: bool = False,
    filename: Optional[str] = None,
    json: bool = False,
    # **kwargs, Dict[str, Any],
) -> None:
    """Splunk log parser, either pipe splunkd.log into it or pass --filename and you can look for things.

    Example:

    loghandler.py --mins 180 --component HttpInputDataHandler --filename /opt/splunk/var/log/splunk/splunkd.log --count

    """
    setup_logging(debug)
    # events after this are what we want
    min_time = datetime.now() - timedelta(minutes=mins)
    # if we want to ignore the last five minutes (for example, for startup reasons), then we set that
    max_time = datetime.now() - timedelta(minutes=ignore_mins)

    result_events = []

    if filename is not None:
        input_handle = Path(filename).open("r", encoding="utf-8")
    else:
        input_handle = TextIOWrapper(sys.stdin.buffer)

    for line in input_handle:
        result = regex.match(line)
        if not result:
            logger.error("Failed to parse line: {}", line)
            continue

        data: Dict[str, Any] = result.groupdict()
        if component:
            if not data.get("component") == component:
                logger.debug("component skip {}", line)
                continue

        if "event" not in data:
            logger.debug("Couldn't find event?")
            continue
        event = data["event"]
        # print(data.get('timestamp'))
        line_timestamp = datetime.strptime(data["timestamp"], "%m-%d-%Y %H:%M:%S.%f %z")
        if line_timestamp < min_time.astimezone():
            logger.debug("Before mins window, skipping")
            continue
        if line_timestamp > max_time.astimezone():
            logger.debug("Inside ignore_time window, skipping {}", line_timestamp)
            continue

        parsed = regex_kv_pairs(event)
        if not parsed:
            logger.debug("Couldn't kv parse line, skipping: {}", line)
            continue
        data["event_parsed"] = regex_kv_pairs(event)
        # print(f"event: {json.dumps(regex_kv_pairs(event), indent=4)}")
        result_events.append(data)
    if count:
        print(len(result_events), end="")
    elif result_events:
        if json:
            print(dumps(result_events))
        else:
            for result_event in result_events:
                print(result_event)


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    cli()
