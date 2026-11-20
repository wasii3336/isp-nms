"""Module 1 - the ordered remote flow. Checks never skip ahead; every step is logged."""
from __future__ import annotations

from dataclasses import dataclass

from .backends import Backend
from .models import Report, Verdict


class CustomerNotFound(Exception):
    pass


@dataclass(frozen=True)
class Thresholds:
    # Defaults are placeholders - "what fibre signal counts as bad" is an
    # open question for your network. Tune to your OLT/ONU specs.
    full_usage_ratio: float = 0.95
    fibre_rx_min_dbm: float = -27.0
    fibre_rx_max_dbm: float = -8.0


class Diagnostics:
    def __init__(self, backend: Backend, thresholds: Thresholds | None = None):
        self.b = backend
        self.t = thresholds or Thresholds()

    def _signal_ok(self, rx: float) -> bool:
        return self.t.fibre_rx_min_dbm <= rx <= self.t.fibre_rx_max_dbm

    def _visit(self, r: Report, why: str) -> Report:
        ruled_out = "; ".join(f"{s.step}. {s.name}: {s.detail}" for s in r.steps)
        return r.finish(Verdict.VISIT_NEEDED, f"{why} Already checked remotely -> {ruled_out}")

    def run(self, customer_id: str) -> Report:
        b, t = self.b, self.t
        customer = b.lookup(customer_id)
        if customer is None:
            raise CustomerNotFound(customer_id)
        r = Report(customer)

        # 1 - online?
        online = b.is_online(customer_id)
        if online:
            r.log(1, "Online status", "next", "Customer is online.")
        elif not b.billing_paid(customer_id):
            r.log(1, "Online status", "resolved", "Offline; account unpaid.")
            return r.finish(Verdict.OFFLINE_BILLING,
                            "Customer is offline because of billing, not a technical fault.")
        else:
            r.log(1, "Online status", "next", "Offline, account in good standing - treat as fault.")

        # 2 - full speed?
        if online:
            used = b.usage_mbps(customer_id)
            ratio = used / customer.plan_mbps
            if ratio >= t.full_usage_ratio:
                r.log(2, "Speed usage", "resolved",
                      f"{used:.0f}/{customer.plan_mbps:.0f} Mbps ({ratio:.0%}).")
                return r.finish(Verdict.FULL_USAGE,
                                "Customer is using their full allocated speed. No fault.")
            r.log(2, "Speed usage", "next", f"{used:.0f}/{customer.plan_mbps:.0f} Mbps ({ratio:.0%}).")
        else:
            r.log(2, "Speed usage", "skipped", "Customer offline - no usage to read.")

        # 3 - fibre signal
        rx = b.fibre_rx_dbm(customer_id)
        if not self._signal_ok(rx):
            r.log(3, "Fibre signal", "visit",
                  f"{rx} dBm outside [{t.fibre_rx_min_dbm}, {t.fibre_rx_max_dbm}].")
            return self._visit(r, "Fibre signal problem - likely physical fault.")
        r.log(3, "Fibre signal", "next", f"{rx} dBm - normal.")

        # 4 - restart via OLT
        was_working = b.is_working(customer_id)
        b.restart_via_olt(customer_id)
        if b.is_working(customer_id):
            r.log(4, "Restart via OLT", "resolved", "Working after restart.")
            if was_working:
                return r.finish(Verdict.NO_FAULT_FOUND,
                                "Everything checked normal; restart changed nothing. No fault found.")
            return r.finish(Verdict.RESOLVED_REMOTELY, "Fixed by remote router restart.")
        r.log(4, "Restart via OLT", "next", "Restarted; still not working.")

        # 5 - re-check
        rx2 = b.fibre_rx_dbm(customer_id)
        if not self._signal_ok(rx2):
            r.log(5, "Re-check signal", "visit", f"{rx2} dBm after restart - now out of range.")
            return self._visit(r, "Fault became visible after restart.")
        r.log(5, "Re-check signal", "next", f"{rx2} dBm - still normal.")

        # 6 - redial
        b.redial(customer_id)
        if b.is_working(customer_id):
            r.log(6, "Redial from server", "resolved", "Working after redial.")
            return r.finish(Verdict.RESOLVED_REMOTELY, "Fixed by redialling the user from the server.")
        r.log(6, "Redial from server", "visit", "Still not working.")

        # 7 - last resort
        return self._visit(r, "All remote steps exhausted.")
