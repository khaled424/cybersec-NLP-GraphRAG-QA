"""Generate durable detection rules (Splunk SPL, Microsoft Sentinel KQL) from graph IOCs.

IOCs come from the knowledge graph, which can be poisoned, so they are treated as
untrusted input: every value is validated against a strict format before being placed in
a query, and strings are escaped. Invalid values are rejected, never "repaired".
"""

from __future__ import annotations

import ipaddress
import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field

_DOMAIN = re.compile(r"^(?=.{1,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$", re.IGNORECASE)
_SHA256 = re.compile(r"^[a-f0-9]{64}$", re.IGNORECASE)
_TECHNIQUE = re.compile(r"^T\d{4}(\.\d{3})?$")
SEVERITIES = ("low", "medium", "high", "critical")


class InvalidIndicatorError(ValueError):
    """Raised when an IOC does not match its expected format."""


def validate_ip(value: str) -> str:
    try:
        return str(ipaddress.ip_address(value.strip()))
    except ValueError as exc:
        raise InvalidIndicatorError(f"invalid IP address: {value!r}") from exc


def validate_domain(value: str) -> str:
    if not _DOMAIN.match(value.strip()):
        raise InvalidIndicatorError(f"invalid domain: {value!r}")
    return value.strip().lower()


def validate_sha256(value: str) -> str:
    if not _SHA256.match(value.strip()):
        raise InvalidIndicatorError(f"invalid SHA-256: {value!r}")
    return value.strip().lower()


@dataclass
class DetectionRule:
    """A threat-intelligence-driven detection (validated at construction)."""

    name: str
    description: str
    technique: str  # MITRE ATT&CK id, e.g. T1071.001
    severity: str = "medium"
    ips: list[str] = field(default_factory=list)
    domains: list[str] = field(default_factory=list)
    sha256: list[str] = field(default_factory=list)
    rejected: list[str] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        if self.severity not in SEVERITIES:
            raise ValueError(f"severity must be one of {SEVERITIES}")
        if not _TECHNIQUE.match(self.technique):
            raise ValueError(f"invalid ATT&CK technique id: {self.technique!r}")
        self.ips = self._keep(self.ips, validate_ip)
        self.domains = self._keep(self.domains, validate_domain)
        self.sha256 = self._keep(self.sha256, validate_sha256)
        if not (self.ips or self.domains or self.sha256):
            raise ValueError("no valid indicator left: refusing to build an empty rule")

    def _keep(self, values: list[str], validator: Callable[[str], str]) -> list[str]:
        kept = []
        for value in dict.fromkeys(values):
            try:
                kept.append(validator(value))
            except InvalidIndicatorError as exc:
                self.rejected.append(str(exc))
        return kept


def _quote(values: list[str]) -> str:
    return ", ".join('"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"' for v in values)


def to_spl(rule: DetectionRule, lookback: str = "-24h") -> str:
    """Splunk SPL search (one `tstats`-free, CIM-field query per indicator type)."""
    clauses = []
    if rule.ips:
        clauses.append(f"(src_ip IN ({_quote(rule.ips)}) OR dest_ip IN ({_quote(rule.ips)}))")
    if rule.domains:
        clauses.append(f"(query IN ({_quote(rule.domains)}) OR url_domain IN ({_quote(rule.domains)}))")
    if rule.sha256:
        clauses.append(f"file_hash IN ({_quote(rule.sha256)})")
    return (
        f"search index=* earliest={lookback} ({' OR '.join(clauses)})\n"
        "| stats count min(_time) as first_seen max(_time) as last_seen "
        "values(sourcetype) as sources by host, src_ip, dest_ip\n"
        "| convert ctime(first_seen) ctime(last_seen)"
    )


def to_kql(rule: DetectionRule, lookback: str = "24h") -> str:
    """Microsoft Sentinel KQL: union of per-table filters, one per indicator type."""
    parts = []
    if rule.ips:
        ips = _quote(rule.ips)
        parts.append(
            f"CommonSecurityLog\n| where TimeGenerated > ago({lookback})\n"
            f"| where SourceIP in ({ips}) or DestinationIP in ({ips})\n"
            "| project TimeGenerated, Computer, SourceIP, DestinationIP, Activity"
        )
    if rule.domains:
        parts.append(
            f"DnsEvents\n| where TimeGenerated > ago({lookback})\n"
            f"| where Name in~ ({_quote(rule.domains)})\n"
            "| project TimeGenerated, Computer, ClientIP, Name"
        )
    if rule.sha256:
        parts.append(
            f"DeviceFileEvents\n| where TimeGenerated > ago({lookback})\n"
            f"| where SHA256 in~ ({_quote(rule.sha256)})\n"
            "| project TimeGenerated, DeviceName, FileName, SHA256"
        )
    if len(parts) == 1:
        return parts[0]
    return "union\n(" + "),\n(".join(parts) + ")"


def to_splunk_savedsearch(rule: DetectionRule) -> str:
    """`savedsearches.conf` stanza so the rule can be deployed as code."""
    spl = to_spl(rule).removeprefix("search ").replace("\n", " \\\n")
    # `search = ` already is the SPL "search" command inside a saved-search stanza.
    return (
        f"[{rule.name}]\nsearch = {spl}\ncron_schedule = */15 * * * *\nenableSched = 1\n"
        f"description = {rule.description} ({rule.technique})\n"
        f"alert.severity = {SEVERITIES.index(rule.severity) + 1}\n"
        "alert_type = number of events\nalert_comparator = greater than\nalert_threshold = 0\n"
    )


def to_sentinel_analytics_rule(rule: DetectionRule) -> str:
    """Sentinel scheduled analytics rule (JSON properties, ready for ARM/REST deployment)."""
    return json.dumps(
        {
            "kind": "Scheduled",
            "properties": {
                "displayName": rule.name,
                "description": rule.description,
                "severity": rule.severity.capitalize(),
                "enabled": True,
                "query": to_kql(rule),
                "queryFrequency": "PT15M",
                "queryPeriod": "PT24H",
                "triggerOperator": "GreaterThan",
                "triggerThreshold": 0,
                "techniques": [rule.technique.split(".")[0]],
            },
        },
        indent=2,
    )
