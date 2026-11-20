from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum


class Verdict(str, Enum):
    RESOLVED_REMOTELY = "resolved_remotely"
    FULL_USAGE = "customer_at_full_usage"
    OFFLINE_BILLING = "offline_billing"
    NO_FAULT_FOUND = "no_fault_found"
    VISIT_NEEDED = "visit_needed"


@dataclass(frozen=True)
class Customer:
    id: str
    name: str
    plan_mbps: float


@dataclass
class StepResult:
    step: int
    name: str
    outcome: str  # "next" | "resolved" | "visit" | "skipped"
    detail: str
    at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))


@dataclass
class Report:
    customer: Customer
    steps: list[StepResult] = field(default_factory=list)
    verdict: Verdict | None = None
    summary: str = ""

    def log(self, step: int, name: str, outcome: str, detail: str) -> None:
        self.steps.append(StepResult(step, name, outcome, detail))

    def finish(self, verdict: Verdict, summary: str) -> "Report":
        self.verdict, self.summary = verdict, summary
        return self

    def to_dict(self) -> dict:
        d = asdict(self)
        d["verdict"] = self.verdict.value if self.verdict else None
        return d
