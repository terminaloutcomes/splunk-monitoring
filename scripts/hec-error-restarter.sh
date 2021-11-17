#!/bin/bash

# This handles when the HEC server busy thing triggers a lot

# looks for:
# > 50 'server busy' events in splunkd.log
# Goes back 15 minutes
# Ignores the last 10 minutes
# And systemctl restart Splunkd

SCRIPT_DIR=$(dirname "$0")


RESULT=$("$SCRIPT_DIR/loghandler.py" --mins 15 --ignore_mins 5 \
    --component HttpInputDataHandler \
    --filename /opt/splunk/var/log/splunk/splunkd.log \
    --count)
if [ "$RESULT" -gt 500 ]; then
    echo "Restarting Splunkd, found ${RESULT} recent server busy events."
    /bin/systemctl restart Splunkd
fi