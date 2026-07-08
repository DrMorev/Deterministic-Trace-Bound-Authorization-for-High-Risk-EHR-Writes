import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from ref.authorizer import (
    Decision,
    EvidenceBundle,
    HITLApproval,
    ProposedAction,
    ReasonCode,
    SessionState,
    Trace,
    authorize_submit_order,
)


EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "examples"
GATEWAY_RECEIVE_TIME = datetime(2026, 2, 20, 12, 0, 10, tzinfo=timezone.utc)


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def load_example(name: str) -> tuple[ProposedAction, EvidenceBundle]:
    data = json.loads((EXAMPLES_DIR / name).read_text(encoding="utf-8"))
    action_data = data["action"]
    bundle_data = data["evidence_bundle"]

    action = ProposedAction(
        action_id=action_data["action_id"],
        tool_name=action_data["tool_name"],
        payload=action_data["payload"],
        collected_at=parse_ts(action_data["collected_at"]),
    )
    traces = [
        Trace(
            trace_id=trace["trace_id"],
            trace_type=trace["trace_type"],
            patient_id=trace["patient_id"],
            collected_at=parse_ts(trace["collected_at"]),
            payload=trace["payload"],
        )
        for trace in bundle_data["traces"]
    ]

    hitl_data = bundle_data["hitl_approval"]
    hitl_approval = None
    if hitl_data is not None:
        hitl_approval = HITLApproval(
            approver_id=hitl_data["approver_id"],
            signed_action_hash=hitl_data["signed_action_hash"],
            signed_trace_hash=hitl_data["signed_trace_hash"],
            approval_timestamp=parse_ts(hitl_data["approval_timestamp"]),
        )

    return action, EvidenceBundle(traces=traces, hitl_approval=hitl_approval)


@pytest.mark.parametrize(
    ("example_name", "expected_decision", "expected_reasons"),
    [
        ("good_submit.json", Decision.ALLOW, []),
        ("stale_trace.json", Decision.DOWNGRADE, [ReasonCode.TRACE_STALE]),
        ("missing_hitl.json", Decision.DOWNGRADE, [ReasonCode.HITL_MISSING]),
        ("identity_mismatch.json", Decision.HALT, [ReasonCode.IDENTITY_CONFLICT]),
    ],
)
def test_examples_match_expected_authorization_outcomes(
    example_name,
    expected_decision,
    expected_reasons,
):
    action, bundle = load_example(example_name)
    result = authorize_submit_order(
        action=action,
        bundle=bundle,
        state=SessionState(),
        gateway_receive_time=GATEWAY_RECEIVE_TIME,
    )

    assert result.decision == expected_decision
    assert result.reason_codes == expected_reasons
