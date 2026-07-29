def test_health_reports_features_off_by_default(client, monkeypatch):
    for var in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "JIRA_BASE_URL", "NOTION_API_KEY"):
        monkeypatch.delenv(var, raising=False)

    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["features"]["analysis"] is False
    assert body["features"]["jira_export"] is False
    assert set(body["features"]) == {
        "analysis",
        "transcription",
        "jira_export",
        "notion_export",
    }


def test_health_reflects_configured_analysis(client, monkeypatch):
    from server.config import get_settings

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    get_settings.cache_clear()  # env changed after app build; re-read it
    resp = client.get("/api/health")
    assert resp.json()["features"]["analysis"] is True
