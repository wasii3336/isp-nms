import pytest
from nms import Diagnostics, Verdict
from nms.backends import DemoBackend
from nms.diagnostics import CustomerNotFound

CASES = {
    "C1001": Verdict.FULL_USAGE,
    "C1002": Verdict.OFFLINE_BILLING,
    "C1003": Verdict.RESOLVED_REMOTELY,
    "C1004": Verdict.VISIT_NEEDED,
    "C1005": Verdict.RESOLVED_REMOTELY,
    "C1006": Verdict.RESOLVED_REMOTELY,
    "C1007": Verdict.NO_FAULT_FOUND,
    "C1008": Verdict.VISIT_NEEDED,
    "C1009": Verdict.VISIT_NEEDED,
}


@pytest.mark.parametrize("cid,expected", CASES.items())
def test_verdicts(cid, expected):
    assert Diagnostics(DemoBackend()).run(cid).verdict == expected


def test_steps_run_in_order_without_skipping():
    r = Diagnostics(DemoBackend()).run("C1006")
    assert [s.step for s in r.steps] == [1, 2, 3, 4, 5, 6]


def test_visit_report_lists_ruled_out_checks():
    r = Diagnostics(DemoBackend()).run("C1009")
    assert "Restart via OLT" in r.summary and "Redial" in r.summary


def test_unknown_customer():
    with pytest.raises(CustomerNotFound):
        Diagnostics(DemoBackend()).run("nope")
