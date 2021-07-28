# pylint: disable=missing-module-docstring,missing-class-docstring
from unittest import mock

from eze.plugins.tools.node_npmoutdated import NpmOutdatedTool
from eze.utils.io import create_tempfile_path
from tests.plugins.tools.tool_helper import ToolMetaTestBase


class TestNpmOutdatedTool(ToolMetaTestBase):
    ToolMetaClass = NpmOutdatedTool
    SNAPSHOT_PREFIX = "node-npmoutdated"

    def test_creation__no_config(self):
        # Given
        input_config = {}
        expected_config = {
            "REPORT_FILE": create_tempfile_path("tmp-npmoutdated-report.json"),
            "NEWER_MAJOR_SEMVERSION_SEVERITY": "high",
            "NEWER_MINOR_SEMVERSION_SEVERITY": "medium",
            "NEWER_PATCH_SEMVERSION_SEVERITY": "low",
            "SOURCE": None,
            #
            "ADDITIONAL_ARGUMENTS": "",
            "IGNORED_FILES": None,
            "IGNORED_VUNERABLITIES": None,
            "IGNORE_BELOW_SEVERITY": None,
            "DEFAULT_SEVERITY": None,
        }
        # When
        testee = NpmOutdatedTool(input_config)
        # Then
        assert testee.config == expected_config

    def test_creation__with_config(self):
        # Given
        input_config = {
            "SOURCE": "src",
        }
        expected_config = {
            "REPORT_FILE": create_tempfile_path("tmp-npmoutdated-report.json"),
            "NEWER_MAJOR_SEMVERSION_SEVERITY": "high",
            "NEWER_MINOR_SEMVERSION_SEVERITY": "medium",
            "NEWER_PATCH_SEMVERSION_SEVERITY": "low",
            "SOURCE": "src",
            #
            "ADDITIONAL_ARGUMENTS": "",
            "IGNORED_FILES": None,
            "IGNORED_VUNERABLITIES": None,
            "IGNORE_BELOW_SEVERITY": None,
            "DEFAULT_SEVERITY": None,
        }
        # When
        testee = NpmOutdatedTool(input_config)
        # Then
        assert testee.config == expected_config

    @mock.patch("eze.plugins.tools.node_npmoutdated.extract_cmd_version", mock.MagicMock(return_value="6.14.11"))
    def test_check_installed__success(self):
        # When
        expected_output = "6.14.11"
        output = NpmOutdatedTool.check_installed()
        # Then
        assert output == expected_output

    @mock.patch("eze.plugins.tools.node_npmoutdated.extract_cmd_version", mock.MagicMock(return_value="5.12.11"))
    def test_check_installed__failure_version_low(self):
        # When
        expected_output = ""
        output = NpmOutdatedTool.check_installed()
        # Then
        assert output == expected_output

    @mock.patch("eze.plugins.tools.node_npmoutdated.extract_cmd_version", mock.MagicMock(return_value=False))
    def test_check_installed__failure_unavailable(self):
        # When
        expected_output = False
        output = NpmOutdatedTool.check_installed()
        # Then
        assert output == expected_output

    def test_parse_report_snapshot(self, snapshot):
        # Test container fixture and snapshot
        self.assert_parse_report_snapshot_test(snapshot)