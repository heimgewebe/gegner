from __future__ import annotations

import hashlib
import inspect

import pytest

import server

EXPECTED = {
    "architecture": "goal_mismatch_and_simpler_alternative",
    "commitment": "fragile_assumption_and_failure_boundary",
    "closeout": "evidence_gap_and_counterexample",
    "path_lock": "path_dependence_and_sunk_cost",
    "convenient_result": "alternative_explanation_and_confirmation_bias",
    "manual": "necessary_assumption_inversion",
    "dialectic": "independent_antithesis_then_evidence_based_decision",
}


@pytest.mark.parametrize(("trigger", "lens"), EXPECTED.items())
def test_trigger_mapping_is_exact_and_deterministic(trigger: str, lens: str) -> None:
    first = server.build_countercheck(trigger=trigger, current_claim="  Claim A  ")
    second = server.build_countercheck(trigger=trigger, current_claim="Claim A")
    assert first == second
    assert first["lens"] == lens
    assert first["challenge_contract"] == "gegner-gegenprobe-v1"
    assert first["same_thread_same_model"] is True
    assert first["automatic_effect"] is False


def test_claim_and_action_are_hash_bound_without_being_persisted() -> None:
    result = server.build_countercheck(
        trigger="architecture",
        current_claim="Claim A",
        planned_action="Do B",
    )
    assert result["claim_sha256"] == hashlib.sha256(b"Claim A").hexdigest()
    assert result["planned_action_sha256"] == hashlib.sha256(b"Do B").hexdigest()


def test_optional_action_is_represented_by_null_digest() -> None:
    result = server.build_countercheck(trigger="manual", current_claim="Claim")
    assert result["planned_action_sha256"] is None


def test_unknown_trigger_fails_closed() -> None:
    with pytest.raises(ValueError, match="unsupported trigger"):
        server.build_countercheck(trigger="surprise", current_claim="Claim")


@pytest.mark.parametrize("value", ["", "   ", None])
def test_claim_must_be_nonempty(value: object) -> None:
    with pytest.raises(ValueError):
        server.build_countercheck(trigger="manual", current_claim=value)  # type: ignore[arg-type]


def test_output_explicitly_denies_independent_authority() -> None:
    result = server.build_countercheck(trigger="closeout", current_claim="Done")
    assert result["allowed_dispositions"] == ["CONTINUE", "CHANGE", "TEST", "PARK/STOP"]
    assert set(result["does_not_establish"]) >= {
        "independent_review",
        "independent_cognition",
        "correctness",
        "external_evidence",
        "decision_authority",
        "execution_authority",
    }


def test_mcp_surface_declares_exactly_one_tool_decorator() -> None:
    source = inspect.getsource(server)
    assert source.count("@mcp.tool(") == 1
    assert '@mcp.tool(name="gegenprobe"' in source


def test_server_has_no_model_or_operator_client_dependency() -> None:
    source = inspect.getsource(server)
    forbidden = [
        "subprocess",
        "openai",
        "anthropic",
        "gemini",
        "grabowski",
        "github",
        "requests.",
        "httpx.",
    ]
    assert not any(token in source.lower() for token in forbidden)


def test_instructions_do_not_demand_contrarian_theater() -> None:
    lowered = server.INSTRUCTIONS.lower()
    assert "same thread" in lowered
    assert "not a second model" in lowered
    assert "continue" in lowered
    assert "must find an error" not in lowered


def test_dialectic_defends_an_independent_antithesis_before_comparison() -> None:
    result = server.build_countercheck(trigger="dialectic", current_claim="Keep path A")
    instruction = result["instruction"]
    assert instruction.index("A / THESIS") < instruction.index("B / ANTITHESIS")
    assert instruction.index("B / ANTITHESIS") < instruction.index("C / DECISION")
    assert "independently framed rival understanding" in instruction
    assert "advocate" in instruction
    assert "Do not merely list faults" in instruction
    assert "preemptively dismiss" in instruction
    assert result["required_return"] == [
        "thesis", "antithesis", "comparison", "disposition"
    ]


def test_dialectic_is_pragmatic_evidence_based_and_not_forced_to_change() -> None:
    instruction = server.TRIGGERS["dialectic"]["instruction"]
    for required in (
        "original user goal", "primary evidence", "future effort",
        "complexity", "maintenance", "risk", "switching costs",
        "ignore sunk effort", "existing simpler solution",
        "change course, or stop", "own serious disadvantages",
        "do not force contradiction or compromise",
        "smallest discriminating test",
    ):
        assert required.lower() in instruction.lower()
    result = server.build_countercheck(trigger="dialectic", current_claim="Claim")
    assert result["allowed_dispositions"] == [
        "CONTINUE", "CHANGE", "TEST", "PARK/STOP"
    ]
    assert result["automatic_effect"] is False
    assert result["same_thread_same_model"] is True


@pytest.mark.parametrize(
    ("claim", "action"),
    [
        ("Custom retrieval service is necessary", "Replace existing retrieval"),
        ("Extra access controls are legally required", "Keep scoped isolation"),
        ("Six sequential patch attempts still fail", "Keep patching"),
        ("Renderer is failing because of its code", "Rewrite renderer"),
    ],
)
def test_dialectic_examples_do_not_fabricate_case_specific_evidence(
    claim: str, action: str
) -> None:
    result = server.build_countercheck(
        trigger="dialectic", current_claim=claim, planned_action=action
    )
    assert result["claim_sha256"] == hashlib.sha256(claim.encode()).hexdigest()
    assert result["planned_action_sha256"] == hashlib.sha256(action.encode()).hexdigest()
    assert result["instruction"] == server.TRIGGERS["dialectic"]["instruction"]
    assert "external_evidence" in result["does_not_establish"]


def test_existing_required_return_contract_remains_unchanged() -> None:
    for trigger in EXPECTED:
        if trigger == "dialectic":
            continue
        result = server.build_countercheck(trigger=trigger, current_claim="Claim")
        assert result["required_return"] == [
            "strongest_countercase", "fragile_assumption",
            "discriminating_evidence", "disposition",
        ]
