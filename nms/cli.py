from __future__ import annotations

import argparse
import json
import sys

from .backends import SCENARIOS, DemoBackend
from .diagnostics import CustomerNotFound, Diagnostics

ICON = {"next": "->", "resolved": "OK", "visit": "!!", "skipped": "--"}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="nms", description="ISP NMS - remote fault diagnostics")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="list demo customers")
    d = sub.add_parser("diagnose", help="run the remote flow for a customer")
    d.add_argument("customer_id")
    d.add_argument("--json", action="store_true", help="machine-readable output")
    a = p.parse_args(argv)

    if a.cmd == "list":
        for cid, s in SCENARIOS.items():
            print(f"{cid}  {s.name:<18} {s.description}")
        return 0

    try:
        rep = Diagnostics(DemoBackend()).run(a.customer_id)
    except CustomerNotFound:
        print(f"Unknown customer: {a.customer_id}", file=sys.stderr)
        return 2

    if a.json:
        print(json.dumps(rep.to_dict(), indent=2))
        return 0
    print(f"Customer {rep.customer.id} - {rep.customer.name} ({rep.customer.plan_mbps:.0f} Mbps plan)\n")
    for s in rep.steps:
        print(f"  [{ICON[s.outcome]}] {s.step}. {s.name}: {s.detail}")
    print(f"\nVERDICT: {rep.verdict.value}\n{rep.summary}")
    return 0
