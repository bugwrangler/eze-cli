# pylint: disable=missing-module-docstring,missing-class-docstring
import json
from unittest import TestCase

import pytest
from click import ClickException

from eze.core.enums import VulnerabilityType, VulnerabilitySeverityEnum
from eze.core.tool import ToolManager, Vulnerability
from tests.__fixtures__.fixture_helper import assert_deep_equal
from tests.__test_helpers__.mock_helper import setup_mock, teardown_mock, DummySuccessTool, DummyFailureTool


class DummyPlugin1:
    def get_tools(self) -> dict:
        return {"success-tool": DummySuccessTool}


class DummyPlugin2:
    def get_tools(self) -> dict:
        return {"failure-tool": DummyFailureTool}


class TestToolManager(TestCase):
    def setUp(self) -> None:
        """Pre-Test Setup func"""
        teardown_mock()

    def tearDown(self) -> None:
        """Post-Test Tear Down func"""
        teardown_mock()

    def test_plugin_inject(self):
        # Given
        expected_tools = {"success-tool": DummySuccessTool, "failure-tool": DummyFailureTool}
        input_plugin = {
            "broken_plugin_with_no_get_tools": {},
            "test_plugin_1": DummyPlugin1(),
            "test_plugin_2": DummyPlugin2(),
        }
        # When
        tool_manager_instance = ToolManager(input_plugin)
        # Then
        assert tool_manager_instance.tools == expected_tools

    def test_get_tool__simple(self):
        # Given
        eze_config = {"success-tool": {"some-thing-for-tool": 123}}
        setup_mock(eze_config)
        expected_tool_config = {
            "some-thing-for-tool": 123,
            "DEFAULT_SEVERITY": "na",
            "IGNORED_VUNERABLITIES": [],
            "IGNORED_FILES": [],
            "IGNORE_BELOW_SEVERITY_INT": 5,
        }
        expected_tools = {"success-tool": DummySuccessTool, "failure-tool": DummyFailureTool}
        input_plugin = {
            "broken_plugin_with_no_get_tools": {},
            "test_plugin_1": DummyPlugin1(),
            "test_plugin_2": DummyPlugin2(),
        }
        tool_manager_instance = ToolManager(input_plugin)
        # When
        tool_instance = tool_manager_instance.get_tool("success-tool")
        # Then
        self.assertIsInstance(tool_instance, DummySuccessTool)
        assert tool_instance.config == expected_tool_config

    def test_get_tool__with_nested_run_type(self):
        # Given
        eze_config = {
            "success-tool": {"some-thing-for-tool": 123},
            "success-tool_dev-mode": {"some-thing-for-dev-mode": 456},
        }
        setup_mock(eze_config)
        expected_tool_config = {
            "some-thing-for-tool": 123,
            "some-thing-for-dev-mode": 456,
            "DEFAULT_SEVERITY": "na",
            "IGNORED_VUNERABLITIES": [],
            "IGNORED_FILES": [],
            "IGNORE_BELOW_SEVERITY_INT": 5,
        }
        input_plugin = {
            "broken_plugin_with_no_get_tools": {},
            "test_plugin_1": DummyPlugin1(),
            "test_plugin_2": DummyPlugin2(),
        }
        tool_manager_instance = ToolManager(input_plugin)
        # When
        tool_instance = tool_manager_instance.get_tool("success-tool:dev-mode")
        # Then
        self.assertIsInstance(tool_instance, DummySuccessTool)
        assert tool_instance.config == expected_tool_config

    def test_get_tool__failure_invalid_reporter(self):
        # Given
        setup_mock()
        expected_error_message = """The ./ezerc config references unknown tool plugin 'non-existant-tool', run 'eze tools list' to see available tools"""
        input_plugin = {
            "broken_plugin_with_no_get_tools": {},
            "test_plugin_1": DummyPlugin1(),
            "test_plugin_2": DummyPlugin2(),
        }
        testee = ToolManager(input_plugin)
        # When
        with pytest.raises(ClickException) as thrown_exception:
            testee.get_tool("non-existant-tool")
        # Then
        assert thrown_exception.value.message == expected_error_message

    def test_normalise_vulnerabilities(self):
        # Given
        fixed_low_vulnerability = Vulnerability(
            {"severity": "low", "is_ignored": False, "name": "corrupted_low_vulnerability"}
        )
        fixed_high_vulnerability = Vulnerability(
            {"severity": "high", "is_ignored": False, "name": "corrupted_high_vulnerability"}
        )
        fixed_missing_severity_vulnerability = Vulnerability(
            {"severity": "medium", "is_ignored": False, "name": "corrupted_missing_severity_vulnerability"}
        )
        fixed_ignored_high_vulnerability = Vulnerability(
            {"severity": "high", "is_ignored": True, "name": "corrupted_ignored_high_vulnerability"}
        )

        corrupted_low_vulnerability = Vulnerability(
            {"severity": "low", "is_ignored": "Not a Ignored Bool Value", "name": "corrupted_low_vulnerability"}
        )
        corrupted_low_vulnerability.severity = "LoW"
        corrupted_missing_severity_vulnerability = Vulnerability(
            {"is_ignored": False, "name": "corrupted_missing_severity_vulnerability"}
        )
        corrupted_high_vulnerability = Vulnerability(
            {"severity": "high", "is_ignored": False, "name": "corrupted_high_vulnerability"}
        )
        corrupted_ignored_high_vulnerability = Vulnerability(
            {"severity": "high", "is_ignored": True, "name": "corrupted_ignored_high_vulnerability"}
        )

        expected_output = [
            fixed_high_vulnerability,
            fixed_missing_severity_vulnerability,
            fixed_low_vulnerability,
            fixed_ignored_high_vulnerability,
        ]
        input_vulnerabilities = [
            corrupted_low_vulnerability,
            corrupted_ignored_high_vulnerability,
            corrupted_high_vulnerability,
            corrupted_missing_severity_vulnerability,
        ]
        input_config = {"DEFAULT_SEVERITY": "medium", "IGNORED_VUNERABLITIES": [], "IGNORE_BELOW_SEVERITY_INT": 9999}
        # When
        tool_manager_instance = ToolManager()
        # Then
        output = tool_manager_instance.normalise_vulnerabilities(input_vulnerabilities, input_config)

        output_object = json.loads(json.dumps(output, default=vars))
        expected_output_object = json.loads(json.dumps(expected_output, default=vars))
        assert output_object == expected_output_object

    def test_sort_vulnerabilities(self):
        # Given
        low_vulnerability = Vulnerability({"severity": "low", "is_ignored": False, "name": "foo"})
        med_vulnerability = Vulnerability({"severity": "medium", "is_ignored": False, "name": "foo"})
        high_vulnerability = Vulnerability({"severity": "high", "is_ignored": False, "name": "foo"})
        ignored_high_vulnerability = Vulnerability({"severity": "high", "is_ignored": True, "name": "foo"})

        expected_output = [high_vulnerability, med_vulnerability, low_vulnerability, ignored_high_vulnerability]
        input = [low_vulnerability, ignored_high_vulnerability, high_vulnerability, med_vulnerability]
        # When
        tool_manager_instance = ToolManager()
        # Then
        output = tool_manager_instance.sort_vulnerabilities(input)
        assert output == expected_output


class TestVulnerability(TestCase):
    def test_seralisation_test(self):
        old_vulnerability = Vulnerability(
            {
                "vulnerability_type": VulnerabilityType.dependancy.name,
                "severity": "low",
                "is_ignored": False,
                "name": "foo",
                "identifiers": {"CVE": "cve-something"},
            }
        )
        dehydrated_vulnerability_json = json.loads(json.dumps(old_vulnerability, default=vars))
        new_rehyrdated_vulnerability = Vulnerability(dehydrated_vulnerability_json)

        assert_deep_equal(old_vulnerability, new_rehyrdated_vulnerability)

    def test_update_ignored__false(self):
        # Given
        expected_ignored_status = False
        input_vulnerability = Vulnerability(
            {
                "name": "foo",
                "identifiers": {"CVE": "cve-xxxx"},
                "severity": VulnerabilitySeverityEnum.medium.name,
                "is_ignored": False,
            }
        )

        input_config = {
            "DEFAULT_SEVERITY": "medium",
            "IGNORED_VUNERABLITIES": [],
            "IGNORE_BELOW_SEVERITY_INT": VulnerabilitySeverityEnum.na.value,
        }

        # When
        input_vulnerability.update_ignored(input_config)
        # Then
        assert input_vulnerability.is_ignored == expected_ignored_status

    def test_update_ignored__by_severity(self):
        # Given
        expected_ignored_status = True
        input_vulnerability = Vulnerability(
            {
                "name": "foo",
                "identifiers": {"CVE": "cve-xxxx"},
                "severity": VulnerabilitySeverityEnum.medium.name,
                "is_ignored": False,
            }
        )

        input_config = {
            "DEFAULT_SEVERITY": "medium",
            "IGNORED_VUNERABLITIES": [],
            "IGNORE_BELOW_SEVERITY_INT": VulnerabilitySeverityEnum.high.value,
        }

        # When
        input_vulnerability.update_ignored(input_config)
        # Then
        assert input_vulnerability.is_ignored == expected_ignored_status

    def test_update_ignored__by_name(self):
        # Given
        expected_ignored_status = True
        input_vulnerability = Vulnerability(
            {
                "name": "foo",
                "identifiers": {"CVE": "cve-xxxx"},
                "severity": VulnerabilitySeverityEnum.medium.name,
                "is_ignored": False,
            }
        )

        input_config = {
            "DEFAULT_SEVERITY": "medium",
            "IGNORED_VUNERABLITIES": ["foo"],
            "IGNORE_BELOW_SEVERITY_INT": VulnerabilitySeverityEnum.na.value,
        }

        # When
        input_vulnerability.update_ignored(input_config)
        # Then
        assert input_vulnerability.is_ignored == expected_ignored_status

    def test_update_ignored__by_cve(self):
        # Given
        expected_ignored_status = True
        input_vulnerability = Vulnerability(
            {
                "name": "foo",
                "identifiers": {"CVE": "cve-xxxx"},
                "severity": VulnerabilitySeverityEnum.medium.name,
                "is_ignored": False,
            }
        )

        input_config = {
            "DEFAULT_SEVERITY": "medium",
            "IGNORED_VUNERABLITIES": ["cve-xxxx"],
            "IGNORE_BELOW_SEVERITY_INT": VulnerabilitySeverityEnum.na.value,
        }

        # When
        input_vulnerability.update_ignored(input_config)
        # Then
        assert input_vulnerability.is_ignored == expected_ignored_status