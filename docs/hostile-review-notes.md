# Hostile Review Notes

**Project:** EBAC-T4  
**Scope:** Deterministic trace-bound authorization for a single high-risk EHR state-changing action (`ehr.submit_order`)  
**Status:** Initial hostile review completed

---

## Purpose

This document records the main hostile-review questions raised against EBAC-T4 and the corresponding design clarifications.

The goal is not to claim that all objections are resolved permanently.  
The goal is to expose the strongest points of attack early and document how the current specification responds.

---

## Review Context

EBAC-T4 is intentionally narrow.

It does **not** claim to be:

- a universal authorization framework
- a generic policy engine
- a replacement for RBAC
- a replacement for CDS
- a complete production security architecture

Hostile review is therefore centered on one question:

> Does the repository demonstrate a coherent and enforceable deterministic execution-control artifact for a high-risk EHR write?

---

## Hostile Questions and Responses

### 1. “Is this just another strict order validator?”

**Attack:**  
Clinical systems already validate orders for allergy conflicts, identity consistency, and required fields.

**Response:**  
EBAC-T4 does not attempt to validate clinical correctness in general.  
It governs whether an **agent-generated state-changing action** is authorized to execute **at runtime**, given a fresh and complete evidence cycle.

The distinction is:

- order validation asks whether the order is clinically acceptable
- EBAC-T4 asks whether the agent is authorized to execute the write now

---

### 2. “Why is this not just OPA plus structured input?”

**Attack:**  
OPA and similar policy engines already evaluate structured input before execution.

**Response:**  
OPA overlaps strongly with the policy-evaluation surface.

The narrow delta demonstrated by EBAC-T4 is not “policy evaluation” in general, but a domain-specific deterministic state machine with:

- mandatory independent traces
- freshness evaluated at gateway receive time
- cross-trace identity invariants
- downgrade semantics tied to evidence incompleteness
- execution-lineage invalidation after downgrade

The repository does not claim that generic policy engines cannot approximate this behavior.  
It demonstrates the behavior explicitly as a narrow medical execution-control artifact.

---

### 3. “What if the agent bypasses the gateway entirely?”

**Attack:**  
If direct write access to the EHR remains possible, the authorization gate is advisory.

**Response:**  
EBAC-T4 assumes a **gateway-mediated execution path**.

For T4 operations:

- the gateway must be the sole execution path
- direct agent-to-EHR write calls must be disallowed by architecture

Without this boundary, the mechanism degrades into advisory middleware rather than an enforceable execution gate.

---

### 4. “How do you handle TOCTOU (time-of-check to time-of-use)?”

**Attack:**  
Traces may be fresh at evaluation time but stale by the time the write is dispatched.

**Response:**  
Freshness is evaluated using **gateway receive time** as the authoritative clock.

The current specification requires:

- trace freshness at gateway receive time
- dispatch within the same validity window

If freshness expires before dispatch, the action must be downgraded or halted.

This mitigates TOCTOU under the assumptions of the current reference architecture.  
It does not claim to eliminate all TOCTOU risk in a production-distributed environment.

---

### 5. “Allergy string matching is clinically incomplete.”

**Attack:**  
Exact ingredient matching is not sufficient for full clinical safety.  
Class-level relationships (e.g., amoxicillin → penicillin class) are not captured.

**Response:**  
Correct.  
Version v0.2 intentionally limits allergy conflict detection to exact deterministic matching.

The purpose of v0.2 is to demonstrate authorization semantics, not ontology completeness.

Class-level or ingredient-family matching is deferred to a future version and is not required to demonstrate the current execution-control pattern.

---

### 6. “Is downgrade just a UX pause, or a real safety mechanism?”

**Attack:**  
If an agent can retry immediately after downgrade, the mechanism may be decorative.

**Response:**  
In EBAC-T4, downgrade is part of the authorization state machine.

Current rules require:

- a downgrade invalidates the execution lineage for the attempted action
- a new attempt requires a new action identifier
- a new attempt requires a new evidence cycle

This prevents silent continuation using stale or previously incomplete context.

---

### 7. “What about audit integrity?”

**Attack:**  
If the gateway itself can be tampered with, how can its decisions be trusted?

**Response:**  
The current repository includes a **minimal audit contract**, not a full tamper-evident audit architecture.

v0.2 requires logging of:

- action identifier
- decision
- reason code
- gateway receive time
- trace identifiers and timestamps
- HITL presence

Tamper-evident persistence and stronger provenance guarantees are deferred.

The reference implementation is demonstrative, not production-hardended.

---

### 8. “Do retry ceilings create denial-of-service problems?”

**Attack:**  
A strict retry ceiling may block legitimate actions during transient infrastructure failures.

**Response:**  
EBAC-T4 distinguishes between:

- **authorization failures** (count toward retry limits)
- **infrastructure failures** (do not count toward retry limits)

Examples:

- missing trace → authorization failure
- stale trace → authorization failure
- EHR timeout → infrastructure failure
- network outage → infrastructure failure

This prevents retry ceilings from penalizing ordinary transport failures.

---

### 9. “What guarantees that traces are real and not fabricated?”

**Attack:**  
If traces can be injected directly by the agent, evidence binding is meaningless.

**Response:**  
The current design assumes **gateway-mediated trace acquisition** for required traces.

In other words:

- required traces should originate from gateway-mediated reads
- agent-supplied traces should not be treated as independently trusted evidence

The v0.2 reference implementation does not yet include full cryptographic provenance.  
That is part of the hardening roadmap.

---

### 10. “Is this security architecture, or just structured middleware?”

**Attack:**  
Without production cryptography, hardware trust anchors, and network enforcement, the mechanism may be dismissed as structured middleware.

**Response:**  
EBAC-T4 is intentionally presented as a **narrow deterministic authorization artifact**, not a complete security architecture.

The repository demonstrates:

- deterministic evidence-bound authorization
- downgrade and halt semantics
- explicit execution-control boundaries

It does not claim to provide production-grade security guarantees.

---

## Main Strengths Identified in Review

The strongest aspects of the current design are:

- execution authority granted per evidence cycle, not by role alone
- downgrade invalidates the execution lineage
- natural-language explanations do not count as evidence
- gateway receive time anchors freshness evaluation
- broad claims are explicitly avoided

---

## Main Risks Identified in Review

The main risks remain:

- collapse into “OPA + validation + middleware”
- insufficiently explicit gateway boundary
- weak trace provenance in the reference implementation
- future scope creep into ontology or broad framework territory

---

## Result

**Hostile review result:** initial round survived

Interpretation:

- the narrow execution-control thesis remains coherent
- the broad framework thesis is not supported and should continue to be avoided
- the artifact is publishable as a narrow demonstrator, not as a universal control plane

---

## Follow-Up Items

The following hardening items remain outside v0.2 scope:

1. stronger trace provenance
2. tamper-evident audit persistence
3. richer allergy / class-level matching
4. production-grade gateway enforcement
5. inter-agent boundary enforcement
6. execution-graph governance beyond the current evidence gate

These are roadmap items, not current claims.
