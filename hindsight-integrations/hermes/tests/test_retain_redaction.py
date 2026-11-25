"""Creations Unit fork: retain content passes through the core redactor before it reaches the bank.

The suite stubs ``agent`` as a plain module, so the real ``agent.redact`` is not importable here;
a stand-in proves the wiring (what the core redactor masks is core's own test surface).
"""

import json
import sys
import types


def test_sync_turn_masks_secret_shaped_content(provider, monkeypatch):
    seen = []

    def fake_redact(text, **_):
        seen.append(text)
        return text.replace("SYNTHETIC-SECRET", "***")

    monkeypatch.setitem(sys.modules, "agent.redact", types.SimpleNamespace(redact_sensitive_text=fake_redact))
    instance, fake = provider({"bank_id": "team"})
    instance.sync_turn("here is the key SYNTHETIC-SECRET ok", "Saved.")
    instance.shutdown()

    content = fake.retains[0]["items"][0]["content"]
    assert len(seen) == 1  # the whole retain payload went through the redactor, once
    assert "SYNTHETIC-SECRET" not in content
    assert json.loads(content)[0]["content"] == "User: here is the key *** ok"  # still a valid turn
