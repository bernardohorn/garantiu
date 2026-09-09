import pytest

from garantiu import test_reports
from garantiu.test_reports import parse_junit_report

SAMPLE_XML = """<?xml version="1.0" encoding="utf-8"?>
<testsuites>
  <testsuite name="pagamentos" tests="3">
    <testcase classname="checkout.test_gateway" name="test_pagamento_aprovado" time="0.01"/>
    <testcase classname="checkout.test_gateway" name="test_pagamento_recusado" time="0.02">
      <failure message="AssertionError">expected True, got False</failure>
    </testcase>
    <testcase classname="auth.test_sessao" name="test_expira_token" time="0.03"/>
  </testsuite>
</testsuites>
"""


@pytest.fixture
def sample_junit_file(tmp_path):
    path = tmp_path / "report.xml"
    path.write_text(SAMPLE_XML)
    return str(path)


def test_parse_junit_report_reads_status(sample_junit_file):
    results = parse_junit_report(sample_junit_file)
    assert len(results) == 3
    statuses = {r["name"]: r["status"] for r in results}
    assert statuses["test_pagamento_aprovado"] == "passed"
    assert statuses["test_pagamento_recusado"] == "failed"
    assert statuses["test_expira_token"] == "passed"


def test_health_by_module_computes_pass_rate(sample_junit_file):
    results = parse_junit_report(sample_junit_file)
    health = test_reports.test_health_by_module(results)
    assert health["checkout"] == 50.0
    assert health["auth"] == 100.0


@pytest.mark.parametrize("xml", ["<broken", "<document/>"])
def test_invalid_junit_is_reported(tmp_path, xml):
    path = tmp_path / "bad.xml"
    path.write_text(xml, encoding="utf-8")
    with pytest.raises(ValueError):
        parse_junit_report(str(path))


def test_single_suite_with_missing_classname_error_and_skipped(tmp_path):
    path = tmp_path / "suite.xml"
    path.write_text(
        '<testsuite name="suite">'
        '<testcase name="a"><error message="broken"/></testcase>'
        '<testcase name="b"><skipped/></testcase>'
        '</testsuite>', encoding="utf-8",
    )
    results = parse_junit_report(str(path))
    assert [r["status"] for r in results] == ["failed", "skipped"]
    assert test_reports.test_health_by_module(results) == {"sem_modulo": 0.0}
