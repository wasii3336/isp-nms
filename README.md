# ISP NMS

An open network monitoring system for ISP support and NOC teams, built from real
support-desk experience. Designed around one idea: **most "slow/no internet" visits
are for diagnosis, not for the fix**, so do the diagnosis from the office, in a fixed
order, and dispatch an engineer only as the last resort.

> Independent project, written from scratch. Not affiliated with or derived from any
> employer's or vendor's code.

## Module 1 - Remote fault diagnostics (this release)

Ordered flow, one customer at a time, every step logged:

1. Is the user online? (offline + unpaid = billing, not a fault)
2. Are they using their full allocated speed? (then: no fault)
3. Fibre signal check (bad signal = prepare a visit)
4. Restart the router remotely via the OLT
5. Re-check signal/connection
6. Redial the user from the server
7. Dispatch a visit, with everything already ruled out attached

Verdicts: `resolved_remotely`, `customer_at_full_usage`, `offline_billing`,
`no_fault_found`, `visit_needed`.

## Quick start

```bash
pip install -e ".[dev]"
nms list                  # demo customers
nms diagnose C1006        # human-readable flow
nms diagnose C1009 --json # machine-readable
pytest
```

## Architecture

- `nms/diagnostics.py` - the flow engine (no device code inside)
- `nms/backends.py` - `Backend` protocol + `DemoBackend` (scenario simulator)
- `nms/models.py` - `Customer`, `StepResult`, `Report`, `Verdict`

Plug in real devices by implementing `Backend` (MikroTik RouterOS API, OLT CLI/SNMP,
BNG/RADIUS, billing). Thresholds (full-usage ratio, fibre dBm range) live in
`Thresholds` and are placeholders until tuned to your network.

## Roadmap

- [ ] Real backends: RouterOS API, OLT, billing
- [ ] Module 3 - per-user encrypted SSH credentials
- [ ] Module 2 - AI operations console with full command/raw-output audit view
- [ ] Module 4 - one-click VLAN/interface probes
- [ ] Module 5 - config-diff audit + WhatsApp reporting
