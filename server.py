from __future__ import annotations

import argparse
import hashlib
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

try:
    from starlette.responses import JSONResponse
except ImportError:  # pragma: no cover - mcp depends on starlette in deployed runtime
    JSONResponse = None  # type: ignore[assignment]


APP_NAME = "Gegner"
CONTRACT = "gegner-gegenprobe-v1"
MAX_TEXT_BYTES = 8_192

INSTRUCTIONS = """You are Gegner, a minimal same-thread countercheck interrupt for ChatGPT.
You are not a second model, reviewer, observer, evidence source, or authority.
Your only tool deterministically returns a countercheck lens for the current claim.
The same ChatGPT instance in the same thread must perform the actual counterargument after the tool returns.
Do not imply independent cognition, correctness, external evidence, or permission to act.
A countercheck may legitimately end in CONTINUE when no material countercase survives the available evidence."""

mcp = FastMCP(APP_NAME, instructions=INSTRUCTIONS)

READ_ONLY = ToolAnnotations(
    title="Same-thread countercheck interrupt",
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)

Trigger = Literal[
    "architecture",
    "commitment",
    "closeout",
    "path_lock",
    "convenient_result",
    "manual",
]

TRIGGERS: dict[str, dict[str, str]] = {
    "architecture": {
        "lens": "goal_mismatch_and_simpler_alternative",
        "instruction": (
            "Treat the current claim as provisional. Test whether it serves the original user "
            "outcome or mainly optimizes an intermediate problem created by the current path. "
            "Construct the strongest materially simpler alternative."
        ),
    },
    "commitment": {
        "lens": "fragile_assumption_and_failure_boundary",
        "instruction": (
            "Identify the necessary assumption that most strongly carries the planned commitment. "
            "Assume it fails and reconstruct the most plausible boundary or failure case that would "
            "make the commitment wrong or premature."
        ),
    },
    "closeout": {
        "lens": "evidence_gap_and_counterexample",
        "instruction": (
            "Treat the closeout claim as unproven. Find the strongest realistic counterexample or "
            "missing observation that would make 'done', 'optimal', or 'complete' premature."
        ),
    },
    "path_lock": {
        "lens": "path_dependence_and_sunk_cost",
        "instruction": (
            "Ignore sunk effort. Ask what direction would be chosen today if none of the current "
            "implementation path had already been built, while preserving the original user outcome."
        ),
    },
    "convenient_result": {
        "lens": "alternative_explanation_and_confirmation_bias",
        "instruction": (
            "Assume the convenient result has another plausible explanation. Construct the strongest "
            "alternative explanation and name the observation that would distinguish it from the "
            "current interpretation."
        ),
    },
    "manual": {
        "lens": "necessary_assumption_inversion",
        "instruction": (
            "Identify the strongest necessary assumption behind the current claim and invert it. "
            "Construct the strongest plausible countercase that follows from the inversion."
        ),
    },
}

ALLOWED_DISPOSITIONS = ["CONTINUE", "CHANGE", "TEST", "PARK/STOP"]
REQUIRED_RETURN = [
    "strongest_countercase",
    "fragile_assumption",
    "discriminating_evidence",
    "disposition",
]
DOES_NOT_ESTABLISH = [
    "independent_review",
    "independent_cognition",
    "correctness",
    "external_evidence",
    "decision_authority",
    "execution_authority",
]


def _clean_text(value: Any, *, label: str, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    cleaned = value.strip()
    if len(cleaned.encode("utf-8")) > MAX_TEXT_BYTES:
        raise ValueError(f"{label} exceeds the size bound")
    return cleaned


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_countercheck(
    *,
    trigger: str,
    current_claim: str,
    planned_action: str | None = None,
) -> dict[str, Any]:
    if trigger not in TRIGGERS:
        raise ValueError(f"unsupported trigger: {trigger}")
    claim = _clean_text(current_claim, label="current_claim")
    assert isinstance(claim, str)
    action = _clean_text(planned_action, label="planned_action", optional=True)
    lens = TRIGGERS[trigger]
    return {
        "schema_version": 1,
        "challenge_contract": CONTRACT,
        "trigger": trigger,
        "claim_sha256": _sha256_text(claim),
        "planned_action_sha256": _sha256_text(action) if action is not None else None,
        "lens": lens["lens"],
        "instruction": lens["instruction"],
        "required_return": list(REQUIRED_RETURN),
        "allowed_dispositions": list(ALLOWED_DISPOSITIONS),
        "automatic_effect": False,
        "same_thread_same_model": True,
        "does_not_establish": list(DOES_NOT_ESTABLISH),
    }


@mcp.tool(name="gegenprobe", annotations=READ_ONLY)
def gegenprobe(
    trigger: Trigger,
    current_claim: str,
    planned_action: str | None = None,
) -> dict[str, Any]:
    """Return one deterministic lens that ChatGPT must apply to its own current claim."""
    return build_countercheck(
        trigger=trigger,
        current_claim=current_claim,
        planned_action=planned_action,
    )


@mcp.custom_route("/healthz", methods=["GET"], include_in_schema=False)
async def healthz(_request: Any) -> Any:
    if JSONResponse is None:  # pragma: no cover
        raise RuntimeError("starlette is unavailable")
    return JSONResponse(
        {"healthy": True, "app": APP_NAME, "contract": CONTRACT},
        headers={"Cache-Control": "no-store"},
    )


@mcp.custom_route("/readyz", methods=["GET"], include_in_schema=False)
async def readyz(_request: Any) -> Any:
    if JSONResponse is None:  # pragma: no cover
        raise RuntimeError("starlette is unavailable")
    return JSONResponse(
        {"ready": True, "tool": "gegenprobe", "contract": CONTRACT},
        headers={"Cache-Control": "no-store"},
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Gegner same-thread countercheck MCP service.")
    parser.add_argument("--transport", choices=("stdio", "streamable-http"), default="stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18188)
    args = parser.parse_args()

    if args.transport == "streamable-http":
        if args.host != "127.0.0.1":
            raise SystemExit("Gegner HTTP transport must bind to 127.0.0.1")
        if not 1024 <= args.port <= 65535:
            raise SystemExit("port must be between 1024 and 65535")
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.settings.stateless_http = True
        if hasattr(mcp.settings, "session_idle_timeout"):
            mcp.settings.session_idle_timeout = None
        if hasattr(mcp.settings, "max_sessions"):
            mcp.settings.max_sessions = None
        mcp.settings.log_level = "WARNING"
        mcp.streamable_http_app()

    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()