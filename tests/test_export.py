def _payload():
    return {
        "meeting_title": "Sprint planning",
        "action_items": [
            {"task": "Write release notes", "owner": "Sam", "priority": "high"}
        ],
    }


def test_jira_export_unavailable_without_config(client, monkeypatch):
    for var in ("JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN", "JIRA_PROJECT_KEY"):
        monkeypatch.delenv(var, raising=False)
    resp = client.post("/api/export/jira", json=_payload())
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "feature_unavailable"


def test_notion_export_unavailable_without_config(client, monkeypatch):
    monkeypatch.delenv("NOTION_API_KEY", raising=False)
    monkeypatch.delenv("NOTION_DATABASE_ID", raising=False)
    resp = client.post("/api/export/notion", json=_payload())
    assert resp.status_code == 503


def test_export_requires_action_items(client):
    resp = client.post("/api/export/jira", json={"action_items": []})
    assert resp.status_code == 422
