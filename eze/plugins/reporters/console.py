"""Console reporter class implementation"""

from pydash import py_

from eze import __version__
from eze.core.enums import VulnerabilityType, VulnerabilitySeverityEnum
from eze.core.reporter import ReporterMeta
from eze.core.tool import ScanResult, Vulnerability
from eze.utils.scan_result import (
    vulnerabilities_short_summary,
    bom_short_summary,
    name_and_time_summary,
    get_bom_license,
)


class ConsoleReporter(ReporterMeta):
    """Python report class for echoing all output into the console"""

    REPORTER_NAME: str = "console"
    SHORT_DESCRIPTION: str = "standard command line reporter"
    INSTALL_HELP: str = """inbuilt"""
    MORE_INFO: str = """inbuilt"""
    LICENSE: str = """inbuilt"""
    EZE_CONFIG: dict = {
        "PRINT_SUMMARY_ONLY": {
            "type": bool,
            "default": False,
            "help_text": """Whether or not to only print the summary (not bom or vulnerabilities)
defaults to false""",
        },
        "PRINT_IGNORED": {
            "type": bool,
            "default": False,
            "help_text": """Whether or not to print out ignored vulnerablities
defaults to false""",
        },
    }

    @staticmethod
    def check_installed() -> str:
        """Method for detecting if reporter installed and ready to run report, returns version installed"""
        return __version__

    def print_to_console(self, text):
        """Wrapper around printing to console"""
        # TODO: plumb colourisation as optional arg
        print(text)

    async def run_report(self, scan_results: list):
        """Method for taking scans and turning then into report output"""
        self.print_to_console("Eze report results:\n")
        scan_results_with_vulnerabilities = []
        scan_results_with_sboms = []
        scan_results_with_warnings = []
        for scan_result in scan_results:
            self.print_scan_summary_title(scan_result)
            if self._has_printable_vulnerabilities(scan_result):
                scan_results_with_vulnerabilities.append(scan_result)
            if scan_result.bom:
                scan_results_with_sboms.append(scan_result)
            if len(scan_result.warnings) > 0:
                scan_results_with_warnings.append(scan_result)

        if self.config["PRINT_SUMMARY_ONLY"]:
            return

        self._print_scan_report_vulnerabilities(scan_results_with_vulnerabilities)
        self._print_scan_report_sbom(scan_results_with_sboms)
        self._print_scan_report_warnings(scan_results_with_warnings)

    def print_scan_summary_title(self, scan_result: ScanResult) -> str:
        """Title of scan summary title"""

        scan_summary = f"""TOOL REPORT: {name_and_time_summary(scan_result, "")}\n"""

        # bom count if exists
        if scan_result.bom:
            scan_summary += bom_short_summary(scan_result)

        # if bom only scan, do not print vulnerability count
        if len(scan_result.vulnerabilities) > 0 or not scan_result.bom:
            scan_summary += vulnerabilities_short_summary(scan_result)
        self.print_to_console(scan_summary)

    def _has_printable_vulnerabilities(self, scan_result: ScanResult) -> bool:
        """Method for taking scan vulnerabilities return True if anything to print"""
        if len(scan_result.vulnerabilities) <= 0:
            return False
        if not self.config["PRINT_IGNORED"] and scan_result.summary["totals"]["total"] == 0:
            return False
        return True

    def _print_scan_report_vulnerabilities(self, scan_results_with_vulnerabilities: list):
        """Method for taking scan vulnerabilities and printing them"""

        if len(scan_results_with_vulnerabilities) <= 0:
            return
        self.print_to_console(
            f"""
Vulnerabilities
================================="""
        )
        for scan_result in scan_results_with_vulnerabilities:
            run_details = scan_result.run_details
            tool_name = py_.get(run_details, "tool_name", "unknown")
            small_indent = "    "
            indent = "        "
            self.print_to_console(
                f"""
{small_indent}[{tool_name}] Vulnerabilities
{small_indent}================================="""
            )
            vulnerability: Vulnerability = None
            for vulnerability in scan_result.vulnerabilities:
                if vulnerability.is_ignored:
                    # INFO: By Default ignore "ignored vulnerabilities"
                    if self.config["PRINT_IGNORED"]:
                        self.print_to_console(f"""{indent}(ignored)""")
                    else:
                        continue

                severity = VulnerabilitySeverityEnum.normalise_name(vulnerability.severity).upper()
                vulnerability_type = VulnerabilityType.normalise_name(vulnerability.vulnerability_type).upper()
                first_line = f"""{indent}[{severity} {vulnerability_type}] : {vulnerability.name}"""
                if vulnerability.version:
                    first_line += f" ({vulnerability.version})"
                self.print_to_console(first_line)
                self.print_to_console(f"""{indent}overview: {vulnerability.overview}""")
                for identifer_key in vulnerability.identifiers:
                    identifer_value = vulnerability.identifiers[identifer_key]
                    self.print_to_console(f"""{indent}{identifer_key}: {identifer_value}""")

                if vulnerability.recommendation:
                    self.print_to_console(f"""{indent}recommendation: {vulnerability.recommendation}""")

                if vulnerability.file_location:
                    self.print_to_console(
                        f"""{indent}file: {vulnerability.file_location.get('path')} (line {vulnerability.file_location.get('line')})"""
                    )
                self.print_to_console("")

    def _print_scan_report_sbom(self, scan_results_with_sboms: list):
        """print scan sbom"""
        if len(scan_results_with_sboms) <= 0:
            return
        self.print_to_console(
            f"""
Bill of Materials
================================="""
        )
        for scan_result in scan_results_with_sboms:
            run_details = scan_result.run_details
            tool_name = py_.get(run_details, "tool_name", "unknown")
            small_indent = "    "
            self.print_to_console(
                f"""
{small_indent}[{tool_name}] SBOM
{small_indent}================================="""
            )
            for component in scan_result.bom["components"]:
                licenses = component.get("licenses", [])

                license_txt = "unknown"
                # manual parsing for name and id
                if licenses and len(licenses) > 0:
                    license_texts = []
                    for license_obj in licenses:
                        license_text = get_bom_license(license_obj)
                        if license_text:
                            license_texts.append(license_text)
                    license_txt = ", ".join(license_texts)

                component_name = component["name"]
                component_group = component.get("group")
                if component_group:
                    component_name = f"{component_group}.{component_name}"

                self.print_to_console(
                    f"""{small_indent}{component["type"].ljust(12)} {component_name.ljust(22)} {component["version"].ljust(12)} {license_txt.ljust(16)} {component.get("description", "").ljust(18)}"""
                )

    def _print_scan_report_warnings(self, scan_results_with_warnings: list):
        """print scan warnings"""
        if len(scan_results_with_warnings) <= 0:
            return

        self.print_to_console(
            f"""
Warnings
================================="""
        )
        for scan_result in scan_results_with_warnings:
            run_details = scan_result.run_details
            tool_name = py_.get(run_details, "tool_name", "unknown")
            small_indent = "    "
            indent = "        "
            self.print_to_console(
                f"""
{small_indent}[{tool_name}] Warnings
{small_indent}================================="""
            )
            for warning in scan_result.warnings:
                self.print_to_console(f"""{indent}{warning}""")