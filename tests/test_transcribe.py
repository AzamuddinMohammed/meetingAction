import io


def test_transcribe_unavailable_without_openai_key(client, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    files = {"file": ("meeting.mp3", io.BytesIO(b"fake-audio-bytes"), "audio/mpeg")}
    resp = client.post("/api/transcribe", files=files)
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "feature_unavailable"


def test_transcribe_rejects_empty_file(client, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    files = {"file": ("meeting.mp3", io.BytesIO(b""), "audio/mpeg")}
    resp = client.post("/api/transcribe", files=files)
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "empty_file"
