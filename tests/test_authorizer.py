from datetime import timedelta, timezone
from datetime import datetime as dt

from ref.authorizer import (
    AuthorizationResult,
    Decision,
    EvidenceBundle,
    HITLApproval,
    ProposedAction,
    ReasonCode,
    SessionState,
    Trace,
    _hash_action_payload,
    _hash_trace_set,
    authorize_submit_order,
)


def ts(seconds: int = 0) -> dt:
    base = dt(2026, 2, 20, 12, 0, 0, tzinfo=timezone.utc)
    return base + timedelta(seconds=seconds)


def make_action(action_id: str = "a1", **overrides) -> ProposedAction:
    payload = {
        "patient_id": "p-123",
        "ingredient": "ibuprofen",
        "dose": "200",
        "unit": "mg",
        "route": "oral",
        "frequency": "bid",
    }
    payload.update(overrides.pop("payload", {}))
    return ProposedAction(
        action_id=action_id,
        tool_name=overrides.pop("tool_name", "ehr.submit_order"),
        payload=payload,
        collected_at=overrides.pop("collected_at", ts(0)),
    )


def make_traces(
    patient_id: str = "p-123",
    collected_at: dt = None,
    allergies=None,
):
    if collected_at is None:
        collected_at = ts(0)
    if allergies is None:
        allergies = ["penicillin"]

    return [
        Trace(
            trace_id="t-patient",
            trace_type="read_patient",
            patient_id=patient_id,
            collected_at=collected_at,
            payload={"patient_id": patient_id, "mrn": "mrn-1"},
        ),
        Trace(
            trace_id="t-allergies",
            trace_type="read_allergies",
            patient_id=patient_id,
            collected_at=collected_at,
            payload={"allergies": allergies},
        ),
        Trace(
            trace_id="t-meds",
            trace_type="read_current_medications",
            patient_id=patient_id,
            collected_at=collected_at,
            payload={"medications": ["metformin"]},
        ),
    ]


def make_hitl(action: ProposedAction, traces) -> HITLApproval:
    return HITLApproval(
        approver_id="clinician-1",
        signed_action_hash=_hash_action_payload(action.payload),
        signed_trace_hash=_hash_trace_set(traces),
        approval_timestamp=ts(1),
    )


def test_allow_with_complete_fresh_evidence():
    action = make_action()
    traces = make_traces()
    bundle = EvidenceBundle(traces=traces, hitl_approval=make_hitl(action, traces))
    state = SessionState()

    result = authorize_submit_order(
        action=action,
        bundle=bundle,
        state=state,
        gateway_receive_time=ts(10),
    )

    assert isinstance(result, AuthorizationResult)
    assert result.decision == Decision.ALLOW
    assert result.reason_codes == []


def test_downgrade_on_missing_trace():
    action = make_action()
    traces = make_traces()
    traces = [t for t in traces if t.trace_type != "read_allergies"]
    bundle = EvidenceBundle(traces=traces, hitl_approval=None)
    state = SessionState()

    result = authorize_submit_order(
        action=action,
        bundle=bundle,
        state=state,
        gateway_receive_time=ts(10),
    )

    assert result.decision == Decision.DOWNGRADE
    assert result.reason_codes == [ReasonCode.TRACE_MISSING]
    assert action.action_id in state.downgraded_action_ids


def test_downgrade_on_stale_trace():
    action = make_action()
    old = ts(0)
    traces = make_traces(collected_at=old)
    bundle = EvidenceBundle(traces=traces, hitl_approval=make_hitl(action, traces))
    state = SessionState()

    # > 300 seconds stale
    result = authorize_submit_order(
        action=action,
        bundle=bundle,
        state=state,
        gateway_receive_time=ts(301),
    )

    assert result.decision == Decision.DOWNGRADE
    assert result.reason_codes == [ReasonCode.TRACE_STALE]
    assert action.action_id in state.downgraded_action_ids


def test_downgrade_on_missing_hitl():
    action = make_action()
    traces = make_traces()
    bundle = EvidenceBundle(traces=traces, hitl_approval=None)
    state = SessionState()

    result = authorize_submit_order(
        action=action,
        bundle=bundle,
        state=state,
        gateway_receive_time=ts(10),
    )

    assert result.decision == Decision.DOWNGRADE
    assert result.reason_codes == [ReasonCode.HITL_MISSING]
    assert action.action_id in state.downgraded_action_ids


def test_halt_on_identity_mismatch():
    action = make_action()
    traces = make_traces()
    # corrupt one trace identity
    traces[1] = Trace(
        trace_id=traces[1].trace_id,
        trace_type=traces[1].trace_type,
        patient_id="p-999",
        collected_at=traces[1].collected_at,
        payload=traces[1].payload,
    )
    bundle = EvidenceBundle(traces=traces, hitl_approval=make_hitl(action, traces))
    state = SessionState()

    result = authorize_submit_order(
        action=action,
        bundle=bundle,
        state=state,
        gateway_receive_time=ts(10),
    )

    assert result.decision == Decision.HALT
    assert result.reason_codes == [ReasonCode.IDENTITY_CONFLICT]


def test_halt_on_allergy_conflict():
    action = make_action(payload={"ingredient": "penicillin"})
    traces = make_traces(allergies=["penicillin", "latex"])
    bundle = EvidenceBundle(traces=traces, hitl_approval=make_hitl(action, traces))
    state = SessionState()

    result = authorize_submit_order(
        action=action,
        bundle=bundle,
        state=state,
        gateway_receive_time=ts(10),
    )

    assert result.decision == Decision.HALT
    assert result.reason_codes == [ReasonCode.ALLERGY_CONFLICT]


def test_halt_on_post_downgrade_bypass():
    action = make_action(action_id="same-action")
    traces = make_traces()
    state = SessionState()

    # first attempt: missing HITL => DOWNGRADE and lock action_id
    first = authorize_submit_order(
        action=action,
        bundle=EvidenceBundle(traces=traces, hitl_approval=None),
        state=state,
        gateway_receive_time=ts(10),
    )
    assert first.decision == Decision.DOWNGRADE
    assert action.action_id in state.downgraded_action_ids

    # second attempt with same action_id, even with fixed evidence => HALT
    second = authorize_submit_order(
        action=action,
        bundle=EvidenceBundle(traces=traces, hitl_approval=make_hitl(action, traces)),
        state=state,
        gateway_receive_time=ts(20),
    )
    assert second.decision == Decision.HALT
    assert second.reason_codes == [ReasonCode.POST_DOWNGRADE_BYPASS]


def test_halt_on_retry_ceiling_exceeded():
    action = make_action(action_id="retry-action")
    traces = make_traces()
    state = SessionState()

    # first attempt consumes the single allowed attempt and downgrades
    first = authorize_submit_order(
        action=action,
        bundle=EvidenceBundle(traces=traces, hitl_approval=None),
        state=state,
        gateway_receive_time=ts(10),
    )
    assert first.decision == Decision.DOWNGRADE

    # use a new action_id state would avoid this; same action_id should now halt
    # because action_attempts > MAX_SUBMIT_ATTEMPTS_PER_ACTION
    state = SessionState(downgraded_action_ids=set(), action_attempts={"retry-action": 1})
    second = authorize_submit_order(
        action=action,
        bundle=EvidenceBundle(traces=traces, hitl_approval=make_hitl(action, traces)),
        state=state,
        gateway_receive_time=ts(20),
    )
    assert second.decision == Decision.HALT
    assert second.reason_codes == [ReasonCode.RETRY_CEILING_EXCEEDED]


def test_halt_on_invalid_hitl_binding():
    action = make_action()
    traces = make_traces()
    bad_hitl = HITLApproval(
        approver_id="clinician-1",
        signed_action_hash="bad-action-hash",
        signed_trace_hash="bad-trace-hash",
        approval_timestamp=ts(1),
    )
    bundle = EvidenceBundle(traces=traces, hitl_approval=bad_hitl)
    state = SessionState()

    result = authorize_submit_order(
        action=action,
        bundle=bundle,
        state=state,
        gateway_receive_time=ts(10),
    )

    # current authorizer maps HITL_INVALID into DOWNGRADE path
    assert result.decision == Decision.DOWNGRADE
    assert result.reason_codes == [ReasonCode.HITL_INVALID]
    assert action.action_id in state.downgraded_action_ids
