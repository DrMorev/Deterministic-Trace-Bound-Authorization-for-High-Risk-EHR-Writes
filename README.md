# EBAC-T4
**Deterministic Trace-Bound Authorization for High-Risk EHR Writes**

Reference implementation and specification of a deterministic authorization gate for high-risk EHR state-changing actions.

The project demonstrates a narrow execution control mechanism where **execution authority is granted per evidence cycle, not by role alone**.

---

## Problem

Modern agentic systems can generate valid API payloads for state-changing operations (e.g., `ehr.submit_order`).

Existing control layers typically operate at different levels:

- **RBAC** — who is allowed in principle
- **CDS** — clinical correctness checks
- **Policy engines (OPA)** — structured policy evaluation
- **Schema validation** — payload structure validation

These layers address adjacent problems, but typically do not enforce a strict runtime contract that ties **execution authority** to a **fresh, complete, independent evidence cycle**.

For high-risk medical writes, this gap matters.

---

## What This Repository Demonstrates

EBAC-T4 implements a **deterministic pre-execution authorization gate** for a single high-risk action: `ehr.submit_order`.

The gate allows execution only if:

- required traces exist
- traces are fresh
- cross-trace invariants hold
- HITL approval matches the exact action context

Otherwise, the action is downgraded or halted.

This repository contains:

- Mini specification (v0.2)
- Minimal reference authorizer
- Test suite
- Prior-art positioning
- Hostile review notes

---

## Repository Structure

```text
ebac-t4/
├── spec/
│   └── ebac-t4-mini-spec-v0.2.md
├── ref/
│   └── authorizer.py
├── tests/
│   └── test_authorizer.py
├── docs/
│   ├── claim-chart-v0.3.md
│   ├── prior-art-notes.md
│   ├── cto-capsule.md
│   └── hostile-review-notes.md
├── examples/
│   ├── good_submit.json
│   ├── stale_trace.json
│   ├── missing_hitl.json
│   └── identity_mismatch.json


⸻

Decision Model

The authorization gate returns one of three deterministic outcomes:

Decision	Meaning
ALLOW	State-changing action permitted
DOWNGRADE	Context incomplete or insufficient for T4 execution
HALT	Integrity violation or blocked execution path

Reason codes distinguish between incomplete context, integrity violations, replay attempts, and post-downgrade bypass.

Note: downgrade invalidates the execution lineage for the attempted action.

⸻

Minimal Evidence Contract

For ehr.submit_order, the following traces are required:
	•	read_patient
	•	read_allergies
	•	read_current_medications

Conditions:
	•	traces must be fresh (TTL enforced at gateway receive time)
	•	patient identity must match across traces
	•	HITL approval must be bound to the exact payload + trace identifiers

Natural-language explanations from the agent are ignored.

⸻

Reference Implementation

ref/authorizer.py implements a deterministic state machine with the following checks:
	1.	post-downgrade lock
	2.	retry ceiling
	3.	schema validation
	4.	identity invariants
	5.	trace completeness
	6.	trace freshness
	7.	HITL binding
	8.	allergy conflict detection

The implementation is intentionally narrow and designed to demonstrate the authorization semantics defined in the specification.

⸻

Running the Tests

pytest tests/

All tests should pass.

The test suite includes scenarios such as:
	•	valid T4 submit
	•	stale trace downgrade
	•	missing HITL downgrade
	•	identity mismatch halt
	•	downgrade replay attempt

⸻

Full Pipeline Architecture (roadmap)

The broader gate model includes five authorization stages:
	•	Gate 0: Tier Sanity
	•	Gate 1: Privilege Check
	•	Gate 2: Evidence Check
	•	Gate 3: Execution Graph Governance (planned)
	•	Gate 4: Zero-Trust Inter-Agent (planned)

v0.2 implements Gates 0–2 for a single high-risk medical action.

Autonomy Levels (A0–A4): agent autonomy graduation determining available tier ceiling — planned.

⸻

Non-Goals

This project does not:
	•	replace RBAC
	•	replace clinical decision support
	•	validate clinical correctness
	•	act as a generic policy engine
	•	provide production-grade cryptographic guarantees

The goal is a deterministic authorization artifact for high-risk state changes.

⸻

Prior Art and Positioning

See:
	•	docs/prior-art-notes.md
	•	docs/claim-chart-v0.3.md

These documents explicitly compare EBAC-T4 with:
	•	RBAC
	•	OPA / policy engines
	•	CDS
	•	schema validation
	•	agent runtime guardrails

The repository intentionally documents overlap and limits of novelty.

⸻

Current Status

Mini-Spec: v0.2 (frozen)
Reference implementation: complete
Hostile review: initial round completed
Tests: passing

Next steps:
	•	feedback collection and iteration

⸻

License

MIT

