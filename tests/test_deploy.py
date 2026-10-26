from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_mcp_service_is_hardened_and_has_no_writable_home_surface() -> None:
    unit = (ROOT / "deploy" / "gegner-mcp.service").read_text(encoding="utf-8")
    assert "ProtectSystem=strict" in unit
    assert "ProtectHome=read-only" in unit
    assert "NoNewPrivileges=true" in unit
    assert "PrivateTmp=true" in unit
    assert "MemoryDenyWriteExecute=true" in unit
    assert "ReadWritePaths=" not in unit
    assert "--host 127.0.0.1 --port 18188" in unit


def test_tunnel_service_uses_existing_tunnel_client_and_profile() -> None:
    unit = (ROOT / "deploy" / "tunnel-client-gegner.service").read_text(encoding="utf-8")
    assert "tunnel-client run --profile gegner" in unit
    assert "http://127.0.0.1:18188/healthz" in unit
    assert "EnvironmentFile=%h/.config/tunnel-client/gegner-runtime.env" in unit
    assert "Environment=PATH=/run/current-system/sw/bin:/usr/bin:/bin" in unit
    assert "ExecStartPre=/usr/bin/env curl " in unit
    assert "/usr/bin/curl " not in unit
    assert "ExecStart=%h/.local/bin/tunnel-client run --profile gegner" in unit
    assert "ProtectSystem=strict" in unit
    assert "ProtectHome=read-only" in unit


def test_public_tunnel_example_contains_no_live_identifiers() -> None:
    profile = (ROOT / "deploy" / "gegner.yaml").read_text(encoding="utf-8")
    assert 'tunnel_id: "tunnel_REPLACE_ME"' in profile
    assert 'OpenAI-Organization: "org_REPLACE_ME"' in profile
    assert "18188/mcp" in profile
    assert "127.0.0.1:18088" in profile
