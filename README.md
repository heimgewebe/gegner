# Gegner

Gegner is a deliberately tiny MCP plugin for one purpose: interrupting ChatGPT's current
reasoning path **inside the same thread and with the same model**.

It is not a second model, reviewer, observer, evidence source, or authority.

## Surface

Exactly one MCP tool is exposed:

`gegenprobe(trigger, current_claim, planned_action=None)`

The tool does not generate the counterargument. It deterministically chooses a countercheck
lens and returns an instruction that the same ChatGPT instance must apply after the tool call.

Supported triggers:

- `architecture` — goal mismatch + simpler alternative
- `commitment` — fragile assumption + failure boundary
- `closeout` — evidence gap + realistic counterexample
- `path_lock` — path dependence + sunk-cost reset
- `convenient_result` — alternative explanation + confirmation bias
- `manual` — invert the strongest necessary assumption
- `dialectic` — independently develop and defend a rival thesis, then compare both

After the tool returns, ChatGPT should produce:

1. strongest plausible countercase;
2. fragile assumption;
3. discriminating evidence / cheapest useful test;
4. one disposition: `CONTINUE`, `CHANGE`, `TEST`, or `PARK/STOP`.

For `dialectic`, the required return is `thesis`, `antithesis`, `comparison`,
and `disposition`, in that order. First identify the original goal and established state.
Next advocate a plausible rival problem framing or action strategy on its own terms,
including its supporting evidence and real weaknesses; do not immediately rebut it.
Only then compare approaches against the original goal, evidence, future cost, risk
and maintenance. In long-running work, ask whether the same path would be chosen
from today's state. Simplification, continuation, testing, change and stopping are
legitimate outcomes; no contrived dispute or compulsory synthesis is required.

A legitimate result is `CONTINUE` when no material countercase survives the available evidence.

The instruction contract is testable; whether the same model follows it reliably or
reduces confirmation bias is **not** established by deterministic unit tests.

## Non-claims

Gegner does **not** establish independent cognition, independent review, correctness, external
evidence, decision authority, or execution authority.

## Runtime

The public deployment examples use:

- MCP: `127.0.0.1:18188`
- tunnel health: `127.0.0.1:18088`

Live tunnel identifiers and credentials belong only in the private local tunnel-client profile.

On both NixOS and traditional Linux, the tunnel service resolves the readiness
probe using `/usr/bin/env -i PATH=/run/current-system/sw/bin:/usr/bin:/bin curl`.
This avoids assuming that `/usr/bin/curl` exists on NixOS, forces the lookup
through system-managed directories even if the credential EnvironmentFile defines
another PATH, and prevents the readiness probe from inheriting tunnel credentials. It still expects a previously installed
`%h/.local/bin/tunnel-client` and a real, pre-existing private `gegner`
tunnel profile and credential environment file. It deliberately never creates
an OpenAI tunnel, chooses a new ID, or copies secrets into Git. Missing live
registration is a blocking prerequisite, not a reason to guess identifiers.
Local MCP health checks do not establish the externally registered ChatGPT link.

## Development

```bash
python3 -m venv .venv
.venv/bin/pip install -e . pytest ruff
.venv/bin/pytest -q
.venv/bin/ruff check .
```
