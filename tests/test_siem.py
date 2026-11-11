"""Tests for SIEM rule generation."""

import json

import pytest

from cybersec_nlp.siem.rules import (
    DetectionRule,
    to_kql,
    to_sentinel_analytics_rule,
    to_spl,
    to_splunk_savedsearch,
)

SHA = "a" * 64


def make_rule(**kw) -> DetectionRule:
    base = {"name": "C2 beacon", "description": "d", "technique": "T1071.001", "severity": "high",
            "allow_documentation": True}
    return DetectionRule(**{**base, **kw})


def test_spl_and_kql_contain_indicators() -> None:
    rule = make_rule(ips=["203.0.113.7"], domains=["evil.example.com"], sha256=[SHA])
    spl, kql = to_spl(rule), to_kql(rule)
    assert '"203.0.113.7"' in spl and '"evil.example.com"' in spl and SHA in spl
    assert "CommonSecurityLog" in kql and "DnsEvents" in kql and "DeviceFileEvents" in kql


def test_invalid_indicators_rejected_not_injected() -> None:
    rule = make_rule(ips=["203.0.113.7", '1.1.1.1") | delete'], domains=['x.com" OR 1=1'])
    assert rule.ips == ["203.0.113.7"] and rule.domains == [] and len(rule.rejected) == 2
    assert "delete" not in to_spl(rule)


def test_empty_rule_refused() -> None:
    with pytest.raises(ValueError, match="no valid indicator"):
        make_rule(ips=["not-an-ip"])


@pytest.mark.parametrize("field,value", [("severity", "urgent"), ("technique", "1071")])
def test_invalid_metadata(field: str, value: str) -> None:
    with pytest.raises(ValueError):
        make_rule(ips=["203.0.113.1"], **{field: value})


def test_deployment_artifacts() -> None:
    rule = make_rule(ips=["203.0.113.1"])
    stanza = to_splunk_savedsearch(rule)
    assert stanza.startswith("[C2 beacon]") and "search = index=*" in stanza
    payload = json.loads(to_sentinel_analytics_rule(rule))["properties"]
    assert payload["severity"] == "High" and payload["techniques"] == ["T1071"]


@pytest.mark.parametrize("ip", ["10.1.2.3", "192.168.0.10", "127.0.0.1", "172.20.1.1"])
def test_internal_ips_are_rejected(ip: str) -> None:
    rule = make_rule(ips=[ip, "203.0.113.9"])
    assert rule.ips == ["203.0.113.9"] and "non-routable" in rule.rejected[0]


def test_known_benign_resolvers_are_rejected() -> None:
    rule = make_rule(ips=["8.8.8.8", "1.1.1.1", "203.0.113.9"])
    assert rule.ips == ["203.0.113.9"] and all("benign" in r for r in rule.rejected)


def test_documentation_ranges_need_opt_in() -> None:
    rule = DetectionRule(name="n", description="d", technique="T1071", ips=["203.0.113.9", "89.62.172.13"])
    assert rule.ips == ["89.62.172.13"] and "documentation" in rule.rejected[0]
