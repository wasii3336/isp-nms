"""Backend interface + a scenario-driven demo backend.

Real integrations (RouterOS API, OLT CLI, RADIUS/BNG, billing) implement
`Backend`. The diagnostics engine never talks to a device directly.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Protocol

from .models import Customer


class Backend(Protocol):
    def lookup(self, customer_id: str) -> Customer | None: ...
    def is_online(self, customer_id: str) -> bool: ...
    def billing_paid(self, customer_id: str) -> bool: ...
    def usage_mbps(self, customer_id: str) -> float: ...
    def fibre_rx_dbm(self, customer_id: str) -> float: ...
    def is_working(self, customer_id: str) -> bool: ...
    def restart_via_olt(self, customer_id: str) -> None: ...
    def redial(self, customer_id: str) -> None: ...


@dataclass(frozen=True)
class Scenario:
    description: str
    name: str
    plan_mbps: float = 100
    online: bool = True
    paid: bool = True
    usage_mbps: float = 20
    rx_dbm: float = -20
    stuck: bool = False                 # online but unusable/slow router
    fixed_by: str | None = None         # "restart" | "redial" | None
    rx_after_restart: float | None = None


SCENARIOS: dict[str, Scenario] = {
    "C1001": Scenario("Slow internet - using full allocated speed", "Ali Raza", usage_mbps=98),
    "C1002": Scenario("Offline - bill unpaid", "Sara Khan", online=False, paid=False),
    "C1003": Scenario("No internet - restart via OLT fixes it", "Bilal Ahmed",
                      online=False, fixed_by="restart"),
    "C1004": Scenario("Fibre signal bad - likely physical fault", "Hina Malik", rx_dbm=-31.5),
    "C1005": Scenario("Slow internet - stuck router, restart fixes it", "Usman Tariq",
                      stuck=True, fixed_by="restart"),
    "C1006": Scenario("Restart does not help, redial fixes it", "Zainab Noor",
                      online=False, fixed_by="redial"),
    "C1007": Scenario("Nothing wrong anywhere (no fault found)", "Omar Farooq"),
    "C1008": Scenario("Signal degrades after restart - visit", "Ayesha Siddiqui",
                      online=False, rx_after_restart=-30.2),
    "C1009": Scenario("Offline, nothing remote fixes it - visit", "Hamza Sheikh", online=False),
}


class DemoBackend:
    """Simulates a network from SCENARIOS. No devices touched."""

    def __init__(self, scenarios: dict[str, Scenario] | None = None):
        self._s = dict(scenarios or SCENARIOS)

    def _get(self, cid: str) -> Scenario:
        return self._s[cid]

    def _set(self, cid: str, **kw) -> None:
        self._s[cid] = replace(self._s[cid], **kw)

    def lookup(self, customer_id):
        s = self._s.get(customer_id)
        return Customer(customer_id, s.name, s.plan_mbps) if s else None

    def is_online(self, customer_id):
        return self._get(customer_id).online

    def billing_paid(self, customer_id):
        return self._get(customer_id).paid

    def usage_mbps(self, customer_id):
        return self._get(customer_id).usage_mbps

    def fibre_rx_dbm(self, customer_id):
        return self._get(customer_id).rx_dbm

    def is_working(self, customer_id):
        s = self._get(customer_id)
        return s.online and not s.stuck

    def restart_via_olt(self, customer_id):
        s = self._get(customer_id)
        kw = {}
        if s.rx_after_restart is not None:
            kw["rx_dbm"] = s.rx_after_restart
        if s.fixed_by == "restart":
            kw.update(online=True, stuck=False)
        self._set(customer_id, **kw)

    def redial(self, customer_id):
        if self._get(customer_id).fixed_by == "redial":
            self._set(customer_id, online=True, stuck=False)
