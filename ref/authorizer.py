from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from hashlib import sha256
from typing import Any, Dict, List, Optional, Set


TTL_SECONDS = 300
MAX_SUBMIT_ATTEMPTS_PER_ACTION = 1


class Decision(str, Enum):
    ALLOW = "ALLOW"
    DOWNGRADE = "DOWNGRADE"
    HALT = "HALT"


class ReasonCode(str, Enum):
    TRACE_MISSING = "TRACE_MISSING"
    TRACE_STALE = "TRACE_STALE"
    HITL_MISSING = "HITL_MISSING"
    HITL_INVALID = "HITL_INVALID"
    IDENTITY_CONFLICT = "IDENTITY_CONFLICT"
    ALLERGY_CONFLICT = "ALLERGY_CONFLICT"
    SCHEMA_INVALID = "SCHEMA_INVALID"
    POST_DOWNGRADE_BYPASS = "POST_DOWNGRADE_BYPASS"
    RETRY_CEILING_EXCEEDED = "RETRY_CEILING_EXCEEDED"


@dataclass(frozen=True)
class ProposedAction:
    action_id: str
    tool_name: str
    payload: Dict[str, Any]
    collected_at: datetime


@dataclass(frozen=True)
class Trace:
    trace_id: str
    trace_type: str
    patient_id: str
    collected_at: datetime
    payload: Dict[str, Any]


@dataclass(frozen=True)
class HITLApproval:
    approver_id: str
    signed_action_hash: str
    signed_trace_hash: str
    approval_timestamp: datetime


@dataclass(frozen=True)
class EvidenceBundle:
    traces: List[Trace]
    hitl_approval: Optional[HITLApproval] = None


@dataclass
class SessionState:
    downgraded_action_ids: Set[str] = field(default_factory=set)
    action_attempts: Dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class AuthorizationResult:
    decision: Decision
    reason_codes: List[ReasonCode]


REQUIRED_TRACE_TYPES = {
    "read_patient",
    "read_allergies",
    "read_current_medications",
}


def _stable_json_like(value: Any) -> str:
    """Deterministic string serialization sufficient for v0.2 reference scope."""
    if isinstance(value, dict):
        parts = []
        for key in sorted(value.keys()):
            parts.append(f"{key}:{_stable_json_like(value[key])}")
        return "{" + ",".join(parts) + "}"
    if isinstance(value, list):
        return "[" + ",".join(_stable_json_like(v) for v in value) + "]"
    return repr(value)


def _hash_action_payload(payload: Dict[str, Any]) -> str:
    return sha256(_stable_json_like(payload).encode("utf-8")).hexdigest()


def _hash_trace_set(traces: List[Trace]) -> str:
    normalized = []
    for trace in sorted(traces, key=lambda t: t.trace_id):
        normalized.append(
            {
                "trace_id": trace.trace_id,
                "trace_type": trace.trace_type,
                "patient_id": trace.patient_id,
                "collected_at": trace.collected_at.isoformat(),
                "payload": trace.payload,
            }
        )
    return sha256(_stable_json_like(normalized).encode("utf-8")).hexdigest()


def _record_attempt(state: SessionState, action_id: str) -> int:
    state.action_attempts[action_id] = state.action_attempts.get(action_id, 0) + 1
    return state.action_attempts[action_id]


def _record_downgrade(state: SessionState, action_id: str) -> None:
    state.downgraded_action_ids.add(action_id)


def _is_post_downgrade_bypass(state: SessionState, action_id: str) -> bool:
    return action_id in state.downgraded_action_ids


def _validate_tool_name(action: ProposedAction) -> Optional[ReasonCode]:
    if action.tool_name != "ehr.submit_order":
        return ReasonCode.SCHEMA_INVALID
    return None


def _validate_payload_schema(action: ProposedAction) -> Optional[ReasonCode]:
    required_fields = {"patient_id", "ingredient", "dose", "unit", "route", "frequency"}
    missing = [field for field in required_fields if field not in action.payload]
    if missing:
        return ReasonCode.SCHEMA_INVALID
    return None


def _index_traces_by_type(traces: List[Trace]) -> Dict[str, Trace]:
    return {trace.trace_type: trace for trace in traces}


def _check_required_traces(bundle: EvidenceBundle) -> Optional[ReasonCode]:
    trace_types = {trace.trace_type for trace in bundle.traces}
    missing = REQUIRED_TRACE_TYPES - trace_types
    if missing:
        return ReasonCode.TRACE_MISSING
    return None


def _check_freshness(bundle: EvidenceBundle, gateway_receive_time: datetime) -> Optional[ReasonCode]:
    for trace in bundle.traces:
        age = gateway_receive_time - trace.collected_at
        if age > timedelta(seconds=TTL_SECONDS):
            return ReasonCode.TRACE_STALE
    return None


def _check_identity_invariant(action: ProposedAction, bundle: EvidenceBundle) -> Optional[ReasonCode]:
    action_patient_id = str(action.payload["patient_id"])
    for trace in bundle.traces:
        if trace.patient_id != action_patient_id:
            return ReasonCode.IDENTITY_CONFLICT
    return None


def _check_hitl_binding(action: ProposedAction, bundle: EvidenceBundle) -> Optional[ReasonCode]:
    if bundle.hitl_approval is None:
        return ReasonCode.HITL_MISSING

    approval = bundle.hitl_approval
    expected_action_hash = _hash_action_payload(action.payload)
    expected_trace_hash = _hash_trace_set(bundle.traces)

    if approval.signed_action_hash != expected_action_hash:
        return ReasonCode.HITL_INVALID
    if approval.signed_trace_hash != expected_trace_hash:
        return ReasonCode.HITL_INVALID
    return None


def _check_allergy_conflict(action: ProposedAction, bundle: EvidenceBundle) -> Optional[ReasonCode]:
    traces = _index_traces_by_type(bundle.traces)
    allergies_trace = traces.get("read_allergies")
    if allergies_trace is None:
        return None  # handled by required trace check

    allergies = allergies_trace.payload.get("allergies", [])
    ingredient = action.payload["ingredient"]

    # v0.2 reference scope: exact deterministic match only
    if ingredient in allergies:
        return ReasonCode.ALLERGY_CONFLICT
    return None


def authorize_submit_order(
    action: ProposedAction,
    bundle: EvidenceBundle,
    state: SessionState,
    gateway_receive_time: datetime,
) -> AuthorizationResult:
    """
    Deterministic authorization gate for a single high-risk action:
    ehr.submit_order
    """

    if _is_post_downgrade_bypass(state, action.action_id):
        return AuthorizationResult(
            decision=Decision.HALT,
            reason_codes=[ReasonCode.POST_DOWNGRADE_BYPASS],
        )

    attempt_count = _record_attempt(state, action.action_id)
    if attempt_count > MAX_SUBMIT_ATTEMPTS_PER_ACTION:
        return AuthorizationResult(
            decision=Decision.HALT,
            reason_codes=[ReasonCode.RETRY_CEILING_EXCEEDED],
        )

    tool_error = _validate_tool_name(action)
    if tool_error is not None:
        return AuthorizationResult(
            decision=Decision.HALT,
            reason_codes=[tool_error],
        )

    schema_error = _validate_payload_schema(action)
    if schema_error is not None:
        return AuthorizationResult(
            decision=Decision.HALT,
            reason_codes=[schema_error],
        )

    trace_error = _check_required_traces(bundle)
    if trace_error is not None:
        _record_downgrade(state, action.action_id)
        return AuthorizationResult(
            decision=Decision.DOWNGRADE,
            reason_codes=[trace_error],
        )

    freshness_error = _check_freshness(bundle, gateway_receive_time)
    if freshness_error is not None:
        _record_downgrade(state, action.action_id)
        return AuthorizationResult(
            decision=Decision.DOWNGRADE,
            reason_codes=[freshness_error],
        )

    identity_error = _check_identity_invariant(action, bundle)
    if identity_error is not None:
        return AuthorizationResult(
            decision=Decision.HALT,
            reason_codes=[identity_error],
        )

    hitl_error = _check_hitl_binding(action, bundle)
    if hitl_error is not None:
        _record_downgrade(state, action.action_id)
        return AuthorizationResult(
            decision=Decision.DOWNGRADE,
            reason_codes=[hitl_error],
        )

    allergy_error = _check_allergy_conflict(action, bundle)
    if allergy_error is not None:
        return AuthorizationResult(
            decision=Decision.HALT,
            reason_codes=[allergy_error],
        )

    return AuthorizationResult(
        decision=Decision.ALLOW,
        reason_codes=[],
    )


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
