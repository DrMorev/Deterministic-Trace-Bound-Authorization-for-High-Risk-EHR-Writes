# Claim Chart v0.3

**Project:** EBAC-T4  
**Scope:** Deterministic trace-bound authorization for a single high-risk EHR state-changing action (`ehr.submit_order`)  
**Purpose:** Clarify overlap with adjacent systems and isolate the narrow execution-control delta demonstrated by this repository.

---

## Working Claim

EBAC-T4 demonstrates a **deterministic pre-execution authorization gate** for a high-risk EHR state-changing action, where execution authority is granted **per evidence cycle**, not by role alone.

The demonstrated mechanism requires:

1. mandatory independent traces
2. freshness evaluated at gateway receive time
3. cross-trace identity invariants
4. HITL approval bound to the exact action context
5. deterministic downgrade / halt semantics
6. no probabilistic inference in authorization logic

This is a narrow, domain-specific claim. It is **not** a claim to a generic policy engine or universal agent governance framework.

---

## Comparison Matrix

| System Class | What It Does | Overlap with EBAC-T4 | Narrow Delta in EBAC-T4 |
|---|---|---|---|
| **RBAC** | Grants permissions based on role or identity | Both deal with authorization and access boundaries | RBAC answers **who may act in principle**; EBAC-T4 answers **whether a specific high-risk state change may execute now**, given a fresh evidence cycle |
| **OPA / Policy Engines** | Evaluates structured input against declarative policy rules | Strong overlap: external policy evaluation on structured data | EBAC-T4 narrows this into a domain-specific deterministic state machine with mandatory trace completeness, gateway-receive-time freshness, and execution-lineage invalidation after downgrade |
| **CDS / Order Validation** | Checks clinical correctness (allergy, dosing, interaction, reminders) | Strong overlap in medical action context | CDS addresses **clinical correctness**; EBAC-T4 addresses **execution authority for agent-generated state change**, independent of clinical recommendation logic |
| **Schema Validation** | Validates types, required fields, and payload structure | Overlap in structured payload validation | EBAC-T4 extends beyond shape validation to trace-bound authorization, cross-trace invariants, and HITL binding |
| **Generic Agent Guardrails** | Adds content restrictions, prompt controls, or output filtering | Partial overlap in runtime safety intent | EBAC-T4 does not filter outputs; it determines whether a **state-changing tool action** is authorized to execute at all |
| **API Gateway / Middleware** | Intercepts requests before execution | Overlap in pre-execution positioning | EBAC-T4 defines a **deterministic evidence-bound decision model** for a specific high-risk action rather than generic request interception |

---

## Narrow Engineering Delta

The narrow demonstrated delta is not “policy evaluation” or “authorization” in general.

It is:

- **authorization per evidence cycle**
- **mandatory independent traces**
- **freshness enforced at gateway receive time**
- **cross-trace identity consistency**
- **HITL approval bound to the exact action context**
- **downgrade invalidates the execution lineage**

A simplified restatement:

> EBAC-T4 is a deterministic state machine for deciding whether a high-risk EHR write may execute, based on a complete and fresh evidence cycle.

---

## What This Repository Does **Not** Claim

This repository does **not** claim:

- a generic authorization framework for all agents
- a replacement for RBAC
- a replacement for CDS
- a replacement for OPA
- a novel generic policy engine
- a complete production-grade security architecture
- a proof of clinical correctness

The scope is intentionally narrow and demonstrative.

---

## Why Broad Claims Would Fail

Broad claims such as:

- “authorization framework for agentic systems”
- “generic runtime governance”
- “novel policy engine for AI”
- “control plane for all high-risk actions”

would likely collapse into existing prior-art classes:

- RBAC
- OPA / policy engines
- API gateways
- CDS / order validation
- guardrails

The defensible position is narrower:

> deterministic trace-bound authorization for a high-risk EHR state-changing action with downgrade semantics tied to evidence completeness and integrity.

---

## Working Narrow Claim Shape

If the demonstrated mechanism survives scrutiny, the surviving shape is likely to be:

1. **single operation scope**
2. **high-risk write**
3. **mandatory trace completeness**
4. **freshness at gateway receive time**
5. **cross-trace invariant enforcement**
6. **bound HITL approval**
7. **deterministic downgrade / halt logic**
8. **no probabilistic authorization inference**

That is the working boundary for v0.3.

---

## Reviewer Notes

### Strongest differentiators
- **Authority is granted per evidence cycle, not by role alone**
- **Downgrade invalidates the execution lineage**
- **Natural-language claims do not count as evidence**

### Most vulnerable points
- OPA can be configured to approximate parts of this behavior
- CDS already occupies the medical safety surface
- middleware + validation can look similar unless the deterministic state machine is explicit

### Practical implication
This repository should be positioned as a **narrow execution-control artifact**, not as a broad framework.

---

## Status
The model assumes a gateway-mediated execution path; without that architectural boundary, the mechanism degrades into advisory middleware.
Claim chart status: **v0.3 draft**  
Use: **positioning, hostile review, novelty review before publication**
