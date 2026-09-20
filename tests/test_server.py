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
