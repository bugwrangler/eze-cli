# pylint: disable=missing-module-docstring,missing-class-docstring
from unittest import mock

import pytest

from eze.plugins.tools.semgrep import SemGrepTool
from eze.utils.io import create_tempfile_path
from tests.plugins.tools.tool_helper import ToolMetaTestBase


class TestSemGrepTool(ToolMetaTestBase):
    ToolMetaClass = SemGrepTool
    SNAPSHOT_PREFIX = "semgrep"

    def test_creation__no_config(self):
        # Given
        expected_config = {
            "CONFIGS": ["p/ci"],
            "EXCLUDE": [],
            "INCLUDE": [],
            "PRINT_TIMING_INFO": True,
            "REPORT_FILE": create_tempfile_path("tmp-semgrep-report.json"),
            "SOURCE": None,
            #
            "ADDITIONAL_ARGUMENTS": "",
            "IGNORED_FILES": None,
            "IGNORED_VULNERABILITIES": None,
            "IGNORE_BELOW_SEVERITY": None,
            "DEFAULT_SEVERITY": None,
        }
        # When
        testee = SemGrepTool()
        # Then
        assert testee.config == expected_config

    def test_creation__with_config(self):
        # Given
        input_config = {
            "ADDITIONAL_ARGUMENTS": "--something foo",
        }
        expected_config = {
            "CONFIGS": ["p/ci"],
            "EXCLUDE": [],
            "INCLUDE": [],
            "PRINT_TIMING_INFO": True,
            "REPORT_FILE": create_tempfile_path("tmp-semgrep-report.json"),
            "SOURCE": None,
            #
            "ADDITIONAL_ARGUMENTS": "--something foo",
            "IGNORED_FILES": None,
            "IGNORED_VULNERABILITIES": None,
            "IGNORE_BELOW_SEVERITY": None,
            "DEFAULT_SEVERITY": None,
        }
        # When
        testee = SemGrepTool(input_config)
        # Then
        assert testee.config == expected_config

    @mock.patch("eze.plugins.tools.semgrep.extract_cmd_version", mock.MagicMock(return_value="1.10.3"))
    def test_check_installed__success(self):
        # When
        expected_output = "1.10.3"
        output = SemGrepTool.check_installed()
        # Then
        assert output == expected_output

    @mock.patch("eze.plugins.tools.semgrep.extract_cmd_version", mock.MagicMock(return_value=False))
    def test_check_installed__failure_unavailable(self):
        # When
        expected_output = False
        output = SemGrepTool.check_installed()
        # Then
        assert output == expected_output

    def test_parse_report__snapshot(self, snapshot):
        # Test container fixture and snapshot
        self.assert_parse_report_snapshot_test(snapshot)

    @mock.patch("eze.utils.cli.subprocess.run")
    @mock.patch("eze.utils.cli.is_windows_os", mock.MagicMock(return_value=True))
    @pytest.mark.asyncio
    async def test_run_scan_command__std(self, mock_subprocess_run):
        # Given
        input_config = {"ADDITIONAL_ARGUMENTS": "--something foo", "REPORT_FILE": "foo_report.json"}

        expected_cmd = (
            "semgrep --optimizations all --json --time --disable-metrics -q -c p/ci -o foo_report.json --something foo"
        )

        # Test run calls correct program
        await self.assert_run_scan_command(input_config, expected_cmd, mock_subprocess_run)
