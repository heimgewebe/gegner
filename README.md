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

After the tool returns, ChatGPT should produce:

1. strongest plausible countercase;
2. fragile assumption;
3. discriminating evidence / cheapest useful test;
4. one disposition: `CONTINUE`, `CHANGE`, `TEST`, or `PARK/STOP`.

A legitimate result is `CONTINUE` when no material countercase survives the available evidence.

## Non-claims

Gegner does **not** establish independent cognition, independent review, correctness, external
evidence, decision authority, or execution authority.

## Runtime

The public deployment examples use:

- MCP: `127.0.0.1:18188`
- tunnel health: `127.0.0.1:18088`

Live tunnel identifiers and credentials belong only in the private local tunnel-client profile.

## Development

```bash
python3 -m venv .venv
.venv/bin/pip install -e . pytest ruff
.venv/bin/pytest -q
.venv/bin/ruff check .
```
