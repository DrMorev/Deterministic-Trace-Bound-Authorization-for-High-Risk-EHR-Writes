# AGENTS.md — EBAC-T4 Repository Operating Rules

## Purpose

This repository is a narrow deterministic reference artifact for EBAC-T4:

Deterministic Trace-Bound Authorization for High-Risk EHR Writes.

The current reference scope is one high-risk action:

`ehr.submit_order`

Agents working in this repository must preserve the narrow scope, deterministic behavior, and alignment between README, spec, reference implementation, tests, examples, and docs.

## Current Scope

EBAC-T4 demonstrates a deterministic pre-execution authorization gate for one high-risk EHR state-changing action.

The gate evaluates structured evidence before execution:

- required traces
- trace freshness at gateway receive time
- future-dated trace integrity violations
- cross-trace identity consistency
- HITL binding to the exact action context
- retry ceiling
- post-downgrade execution-lineage invalidation
- deterministic allergy conflict invariant

The repository does not evaluate clinical correctness.

## Non-Goals

Do not turn this repository into:

- a generic agent framework
- a universal governance platform
- a broad authorization control plane
- a replacement for RBAC
- a replacement for CDS
- a replacement for OPA
- a production security system
- an inter-agent runtime enforcement platform
- an AAF/CVG umbrella project

Roadmap language may exist as context only. It must not be presented as current implemented scope.

## Agent Rules

Before making changes:

1. Inspect current branch and HEAD.
2. Run the existing tests.
3. Identify whether the requested change is runtime, spec, docs, tests, examples, or hygiene.
4. Preserve narrow scope unless the PI explicitly approves a versioned scope expansion.
5. Do not make unrelated improvements.

Before committing:

1. Run:

   `python -m pytest tests/ -v`

2. Check:

   `git status --short`

3. Review:

   `git diff`

4. Confirm that generated artifacts are not staged.

Generated artifacts must not be committed, including:

- `__pycache__/`
- `.pytest_cache/`
- `.DS_Store`
- local virtual environments
- editor metadata
- temporary logs

## Required Receipt Format

After any commit or push, return:

```text
RECEIPT

Repo:
Branch:
Base HEAD:
Final commit:
Files changed:
Test command:
Test result:
git status --short after commit/push:
Scope check:
Notes:

A claim of “done” without a commit hash, changed-file list, and test result is not sufficient.

Scope Check

Every change must answer:

* Did this alter runtime authorization semantics?
* Did this alter spec semantics?
* Did this expand beyond ehr.submit_order?
* Did this introduce broad framework/platform language?
* Did this keep README/spec/ref/tests/examples/docs aligned?

If the answer indicates scope expansion, stop and ask for explicit PI approval.

Safe Changes

Usually safe:

* typo fixes
* Markdown formatting fixes
* README/spec alignment with existing implementation
* example/test alignment
* CI/test hygiene
* generated-artifact exclusion
* explicit documentation of existing limits

Not safe without explicit approval:

* new action types
* new autonomy levels as implemented scope
* new gates as implemented scope
* runtime semantic changes
* new clinical-correctness claims
* production-security claims
* broad agent-governance claims

Canonical Project Sentence

EBAC-T4 is a narrow deterministic state machine for deciding whether a high-risk EHR write may execute, based on a complete and fresh evidence cycle.

Canonical Boundary Sentence

EBAC-T4 assumes a gateway-mediated execution boundary. Without that boundary, the mechanism degrades into advisory middleware.

Agent Instruction

When in doubt, narrow the change.

Prefer one verified, tested, scoped patch over broad conceptual expansion.
