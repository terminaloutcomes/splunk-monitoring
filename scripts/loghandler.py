#!/usr/bin/env python3

""" Splunk log parser, you can filter by component, time etc. """

import sys
from json import dumps
import re
from datetime import datetime, timedelta

try:
    import click
except ImportError:
    print("Please install the click library: python3 -m pip install click", file=sys.stderr)
    sys.exit(1)

def regex_kv_pairs(text, item_sep=r"\s", value_sep="="):
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
    """.replace("=", value_sep).replace(r"|\s)", f"|{item_sep})")
    kv_regex = re.compile(split_regex, re.VERBOSE)

    return {match.group("key"): match.group("value") for match in kv_regex.finditer(text)}

# pylint: disable=line-too-long
#example_log = '10-03-2021 08:48:24.792 +1000 ERROR HttpInputDataHandler [2394001 HttpInputServerDataThread] - Failed processing http input, token name=test, channel=n/a, source_IP=10.0.0.123, reply=9, events_processed=0, http_input_body_size=183414, parsing_err="Server is busy"'

# pylint: disable=line-too-long
regex = re.compile(r"^(?P<timestamp>(?P<date>\S+) (?P<time_hour>\d+):(?P<time_minute>\d+):(?P<time_second>[\d\.]+) (?P<time_zone_offset>\S+)) (?P<log_level>\w+)\s+(?P<component>\S+)\s+(?P<event>.*)")

@click.command()
@click.option('--mins', default=5)
@click.option('--component')
@click.option('--debug', is_flag=True)
@click.option('--count', is_flag=True)
@click.option('--json', is_flag=True)
@click.option('--filename', type=click.File('r'), default=False)
def cli(mins, component, debug, count, filename, json):
    """ Splunk log parser, either pipe splunkd.log into it or pass --filename and you can look for things.

Example:

./scripts/log-handler.py --mins 180 --component HttpInputDataHandler --filename /opt/splunk/var/log/splunk/splunkd.log --count

    """
    # events after this are what we want
    min_time = datetime.now() - timedelta(minutes=mins)

    result_events = []

    if filename:
        input_handle = filename
    else:
        input_handle = sys.stdin

    for line in input_handle:
        result = regex.match(line)
        if not result:
            print(f"Failed to parse line: {line}")
            continue


        data = result.groupdict()
        if component:
            if not data.get('component') == component:
                if debug:
                    print(f"component skip {line}")
                continue


        event = data.get('event')


        if not event:
            if debug:
                print("Couldn't find event?", file=sys.stderr)
            continue
        else:
            #print(data.get('timestamp'))
            line_timestamp = datetime.strptime(
                data.get('timestamp'),
                '%m-%d-%Y %H:%M:%S.%f %z'
            )
            if line_timestamp < min_time.astimezone():
                continue

            parsed = regex_kv_pairs(event)
            if not parsed:
                if debug:
                    print(f"Couldn't kv parse line, skipping: {line}", file=sys.stderr)
                continue
            data['event_parsed'] = regex_kv_pairs(event)
            # print(f"event: {json.dumps(regex_kv_pairs(event), indent=4)}")
            result_events.append(data)
    if count:
        print(len(result_events), end='')
    elif result_events:
        if json:
            print(dumps(result_events))
        else:
            for event in result_events:
                print(event)

if __name__ == '__main__':
    # pylint: disable=no-value-for-parameter
    cli()
