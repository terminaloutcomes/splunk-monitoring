""" tests that click loads """

from click.testing import CliRunner

from splunk_monitoring.hec_watchdog import cli

def test_click() -> None:
    """ tests it loads at least """

    result = CliRunner().invoke(cli, "--help")
    assert result
