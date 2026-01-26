# 💸 Technical Debt & Architecture Trade-offs
**Status:** Active Tracking
**Last Updated:** 2026-01-26

> **Philosophy:** "We borrowed modularity to buy latency. This ledger tracks when we must pay it back."

## 1. Intentional Debt (The Strategic Gambles)
*Trade-offs consciously made to meet Thesis KPIs (Latency < 100ms).*

| ID | Item | The "Hack" | Why we did it | Repayment Trigger |
| :--- | :--- | :--- | :--- | :--- |
| **TD-01** | **The Monolithic Brain** | `core/officer.py` contains Ingestion, Normalization, AND Reasoning logic in one class. | **Latency.** Removing function call overhead and import layers saved ~15ms per cycle. | **Trigger:** When `officer.py` exceeds 1,000 LOC. **Fix:** Extract parsers to `core/parsers/`. |
| **TD-02** | **Hardcoded Topics** | MQTT topics (`thing/product`, `dronetag`) are string literals in `process_traffic()`. | **Speed.** Regex matching is slower than string containment checks. | **Trigger:** When we add a 4th Protocol (ADS-B). **Fix:** Move to `config/schema.json`. |
| **TD-03** | **Synchronous MQTT** | The Loop uses blocking `paho-mqtt` callbacks rather than `asyncio`. | **Simplicity.** Debugging race conditions in async Python is a nightmare during field tests. | **Trigger:** When Ingestion > 50 msg/sec (ADS-B flood). **Fix:** Rewrite Main Loop with `asyncio`. |

## 2. Accidental Debt (Cleanup Tasks)
*Code that needs refactoring but isn't critical yet.*

| ID | Item | Description | Severity | Planned Fix |
| :--- | :--- | :--- | :--- | :--- |
| **TD-04** | **Magic Numbers** | KPI thresholds (e.g., `latency > 5.0`) are hardcoded in `auditor.py`. | Low | Move to `config/thresholds.yaml`. |
| **TD-05** | **Zombie Drivers** | The `securingskies/drivers/` folder was deleted, but some imports might linger in tests. | Low | Run `grep -r "drivers." .` and purge. |
| **TD-06** | **Regex Guardrails** | "Constitutional Guardrails" are hardcoded lists in `officer.py`. | Medium | Externalize to `config/guardrails.json` for easier updating. |

## 3. Future Scalability Risks (Thesis Limitations)
*These are out of scope for v1.0 but acknowledge limitations.*
* **Database:** Using flat JSONL files (`logs/`) instead of Time-Series DB (InfluxDB). Good for thesis portability, bad for production query speed.
* **Authentication:** Hardcoded credentials in `.env`. Needs OAuth/Keycloak for "Locked Shields" scenario.
