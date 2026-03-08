Prior Art Notes

Project: EBAC-T4
Scope: Deterministic trace-bound authorization for a single high-risk EHR state-changing action (ehr.submit_order)

This document records the main adjacent system classes considered during design and explains why EBAC-T4 is positioned narrowly.

The goal is not to claim novelty across the authorization or policy space, but to clarify the specific execution-control mechanism demonstrated in this repository.

⸻

Adjacent System Classes

Several established system classes already address related problems.

EBAC-T4 intentionally overlaps with parts of these systems while isolating a narrower execution-control behavior.

⸻

RBAC (Role-Based Access Control)

RBAC determines whether an actor is allowed in principle to perform an action.

Typical RBAC questions include:
	•	Does the user have the correct role?
	•	Is the actor permitted to access this API endpoint?
	•	Does the service identity have write privileges?

RBAC operates at the identity and permission layer.

EBAC-T4 operates at a different layer.

RBAC may allow an agent to call ehr.submit_order, but EBAC-T4 determines whether the specific action instance may execute given the current evidence cycle.

Key distinction:

RBAC answers who may act.
EBAC-T4 answers whether this specific high-risk state change may execute now.

⸻

OPA / Policy Engines

Policy engines such as Open Policy Agent (OPA) evaluate structured inputs against declarative policy rules.

Typical use cases include:
	•	infrastructure policy enforcement
	•	admission control
	•	request validation
	•	contextual access decisions

OPA-style systems can evaluate JSON payloads and contextual metadata before execution.

EBAC-T4 overlaps with this capability.

However, EBAC-T4 narrows the problem to a deterministic execution-control state machine for a specific high-risk medical action.

The mechanism demonstrated here includes:
	•	mandatory independent traces
	•	freshness evaluated at gateway receive time
	•	cross-trace identity invariants
	•	downgrade semantics tied to incomplete evidence
	•	execution-lineage invalidation after downgrade

OPA could theoretically be configured to approximate similar logic.
EBAC-T4 exists as a domain-specific artifact demonstrating this pattern explicitly.

⸻

Clinical Decision Support (CDS)

Clinical decision support systems evaluate the clinical correctness of medical actions.

Examples include:
	•	allergy checks
	•	drug–drug interaction alerts
	•	dose validation
	•	order reminders

CDS systems operate on the clinical reasoning layer.

EBAC-T4 does not attempt to determine clinical correctness.

Instead, it governs execution authority for an agent-generated state-changing action.

Example distinction:
	•	CDS: “Is this medication clinically appropriate?”
	•	EBAC-T4: “Should this agent-generated write be allowed to execute at all?”

These systems address adjacent but distinct concerns.

⸻

Schema Validation

Schema validation frameworks ensure that structured payloads conform to a defined format.

Typical checks include:
	•	required fields
	•	type constraints
	•	enum validation
	•	payload structure

EBAC-T4 incorporates schema validation as a prerequisite but extends beyond it.

The authorization decision also depends on:
	•	trace completeness
	•	cross-trace identity consistency
	•	freshness of supporting evidence
	•	HITL approval binding

Schema validation alone cannot provide trace-bound execution authorization.

⸻

API Gateways and Middleware

API gateways and middleware layers intercept requests before they reach downstream services.

Common gateway functions include:
	•	authentication
	•	rate limiting
	•	request validation
	•	routing
	•	logging

EBAC-T4 shares the pre-execution interception position of a gateway.

However, EBAC-T4 defines a deterministic decision model tied to an evidence cycle, rather than a general request-processing pipeline.

The mechanism assumes a gateway-mediated execution path between the agent and the EHR API.

Without that architectural boundary, the mechanism degrades into advisory middleware rather than an enforceable execution gate.

⸻

Agent Guardrails

Many agent safety frameworks introduce guardrails around LLM outputs.

Examples include:
	•	prompt restrictions
	•	response filtering
	•	tool usage limits
	•	behavioral constraints

These systems typically operate on model behavior.

EBAC-T4 does not attempt to filter or modify model outputs.

Instead, it determines whether a state-changing tool action is permitted to execute.

Natural-language explanations from the model are not considered evidence in the authorization decision.

⸻

Architectural Position

EBAC-T4 is intentionally positioned as a narrow execution-control artifact.

It does not attempt to replace existing systems.

Instead, it demonstrates a specific pattern:

authorization tied to a fresh, complete evidence cycle for a high-risk state-changing action.

The design assumes coexistence with:
	•	RBAC for identity and role control
	•	CDS for clinical correctness checks
	•	policy engines for broader infrastructure rules
	•	schema validation for payload structure

EBAC-T4 addresses a narrower question:

When a stochastic system proposes a high-risk state change, what evidence must exist before the action is allowed to execute?

⸻

Why Broad Claims Are Avoided

Several system classes already occupy adjacent territory:
	•	RBAC
	•	OPA and policy engines
	•	CDS and order validation
	•	API gateways
	•	LLM guardrail frameworks

A broad claim such as:
	•	“agent authorization framework”
	•	“universal runtime governance”
	•	“AI safety control plane”

would collapse into existing prior-art categories.

The repository therefore documents a single narrow mechanism rather than a general framework.

⸻

Practical Scope

The demonstrated mechanism applies to:
	•	one operation (ehr.submit_order)
	•	one high-risk write path
	•	deterministic authorization logic
	•	mandatory evidence traces
	•	downgrade semantics for incomplete context
	•	halt semantics for integrity violations

The implementation is intentionally minimal and demonstrative.

It exists to clarify the architectural boundary between probabilistic agents and deterministic execution control.

⸻

Relationship to the Claim Chart

See:

docs/claim-chart-v0.3.md

The claim chart provides a structured comparison matrix showing where EBAC-T4 overlaps with adjacent systems and where the narrow execution-control delta is demonstrated.

⸻

Status

Prior-art notes status: v0.1

Purpose:
	•	positioning
	•	novelty review
	•	hostile review context
	•	documentation transparency before publication
