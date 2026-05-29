# tests/utils/test_computer_basic.py
import json
from types import SimpleNamespace

import utils.computer as comp


class FakeRoom:
    def __init__(self):
        self.LOCAL_BASE_URL = "http://local/v1"
        self.LOCAL_MODEL = "local-model"
        self.OPENAI_BASE_URL = "https://api.openai.com/v1"
        self.OPENAI_MODEL = "gpt-x"
        self.OPENAI_API_KEY = ""
        self.contents = []
        self.key = "Test Room"
        self.db = SimpleNamespace(
            desc="",
            memory=[],
            director_facts=[],
            last_generated_desc="",
        )


def test_json_safe_primitives_and_bytes():
    assert comp._json_safe(None) is None
    assert comp._json_safe(True) is True
    assert comp._json_safe(3) == 3
    assert comp._json_safe(1.25) == 1.25
    assert comp._json_safe("x") == "x"
    assert comp._json_safe(b"hi") == "hi"
    assert comp._json_safe(bytearray(b"hi")) == "hi"


def test_json_safe_mapping_and_sequence():
    data = {
        "a": 1,
        2: b"bin",
        "nested": {"x": 2},
        "lst": [b"a", {"k": "v"}],
    }
    out = comp._json_safe(data)
    assert out == {
        "a": 1,
        "2": "bin",
        "nested": {"x": 2},
        "lst": ["a", {"k": "v"}],
    }

    # ensure it's json serializable
    json.dumps(out)


def test_json_safe_fallback_stringifies_unknown():
    class Weird:
        def __str__(self):
            return "<weird>"
    assert comp._json_safe(Weird()) == "<weird>"


def test_llm_providers_local_only_when_no_openai_key(monkeypatch):
    fake_settings = SimpleNamespace(
        LOCAL_BASE_URL="http://test/v1",
        LOCAL_MODEL="test-model",
        OPENAI_API_KEY=None,
    )
    monkeypatch.setattr(comp, "settings", fake_settings, raising=False)
    r = FakeRoom()
    c = comp.Computer(r)

    providers = c.llm_providers()
    assert len(providers) == 1
    assert providers[0].label == "LOCAL"
    assert providers[0].base_url == "http://test/v1"
    assert providers[0].model == "test-model"
    assert providers[0].api_key is None


def test_llm_providers_includes_openai_when_key_present(monkeypatch):
    fake_settings = SimpleNamespace(
        LOCAL_BASE_URL="http://test/v1",
        LOCAL_MODEL="test-model",
        OPENAI_API_KEY="sk-test",
        OPENAI_MODEL="gpt-4.1-mini",
    )
    monkeypatch.setattr(comp, "settings", fake_settings, raising=False)
    r = FakeRoom()
    c = comp.Computer(r)

    providers = c.llm_providers()
    assert [p.label for p in providers] == ["LOCAL", "OPENAI"]
    assert providers[1].api_key == "sk-test"


def test_room_memory_text_formats_and_truncates():
    r = FakeRoom()
    r.db.memory = [
        {"who": "A", "msg": "hello"},
        {"who": "B", "msg": "world"},
    ]
    c = comp.Computer(r)

    txt = c.room_memory_text(max_chars=999)
    assert txt == "A: hello\nB: world"

    # truncation keeps the tail
    long = [{"who": "X", "msg": "x" * 5000}]
    r.db.memory = long
    tail = c.room_memory_text(max_chars=10)
    assert len(tail) == 10


# --- Tests for _build_messages helper ---

def test_build_messages_with_json_safe():
    r = FakeRoom()
    c = comp.Computer(r)

    sys_prompt = "You are a system."
    payload = {"key": "value", "nested": {"a": b"bytes"}}
    messages = c._build_messages(sys_prompt, payload, ensure_json_safe=True)

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == sys_prompt
    assert messages[1]["role"] == "user"
    # The payload was JSON-encoded (bytes converted to string)
    parsed = json.loads(messages[1]["content"])
    assert parsed["key"] == "value"
    assert parsed["nested"]["a"] == "bytes"


def test_build_messages_without_json_safe():
    r = FakeRoom()
    c = comp.Computer(r)

    sys_prompt = "System prompt."
    payload = {"text": "hello", "num": 42}
    messages = c._build_messages(sys_prompt, payload, ensure_json_safe=False)

    assert len(messages) == 2
    assert messages[0]["content"] == sys_prompt
    parsed = json.loads(messages[1]["content"])
    assert parsed == {"text": "hello", "num": 42}


def test_build_messages_handles_empty_payload():
    r = FakeRoom()
    c = comp.Computer(r)

    messages = c._build_messages("sys", {})
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == "sys"
    assert messages[1]["role"] == "user"
    assert json.loads(messages[1]["content"]) == {}


def test_chat_json_delegates_to_client(monkeypatch):
    r = FakeRoom()
    c = comp.Computer(r)

    # Mock the client
    mock_client = SimpleNamespace()
    mock_client.chat_json = lambda providers, msgs: {"result": "ok"}

    class FakeModule:
        @staticmethod
        def build_default_client_from_env():
            return mock_client

    monkeypatch.setattr(comp, "build_default_client_from_env", FakeModule.build_default_client_from_env)

    msgs = [{"role": "system", "content": "test"}]
    result = c._chat_json(msgs)
    assert result == {"result": "ok"}
