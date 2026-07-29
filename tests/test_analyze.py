from server.dependencies import get_analysis_service
from server.errors import ContentRefusedError, FeatureUnavailableError
from server.schemas import (
    ActionItem,
    AnalyzeRequest,
    Decision,
    Email,
    MeetingAnalysis,
)


class FakeClaudeService:
    def __init__(self, analysis: MeetingAnalysis | None = None, exc: Exception | None = None):
        self._analysis = analysis
        self._exc = exc

    async def analyze(self, req: AnalyzeRequest):
        if self._exc:
            raise self._exc
        return self._analysis, {"input_tokens": 100, "output_tokens": 50}


def _sample_analysis() -> MeetingAnalysis:
    return MeetingAnalysis(
        summary="We agreed to ship the beta.",
        key_points=["Beta scope finalized"],
        decisions=[Decision(decision="Ship beta on Friday", rationale="Customer demand")],
        action_items=[
            ActionItem(id="ai-1", task="Write release notes", owner="Sam", priority="high")
        ],
        risks=["Load testing incomplete"],
        follow_up_email=Email(subject="Beta ship", body="Team, we ship Friday..."),
    )


def test_analyze_returns_structured_result(client, app):
    app.dependency_overrides[get_analysis_service] = lambda: FakeClaudeService(_sample_analysis())

    resp = client.post("/api/analyze", json={"transcript": "some meeting text"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["analysis"]["action_items"][0]["id"] == "ai-1"
    assert body["analysis"]["action_items"][0]["status"] == "open"
    assert body["usage"]["input_tokens"] == 100
    app.dependency_overrides.clear()


def test_analyze_requires_transcript(client):
    resp = client.post("/api/analyze", json={"transcript": ""})
    assert resp.status_code == 422  # pydantic min_length


def test_analyze_rejects_oversized_transcript(client, app, monkeypatch):
    from server.config import get_settings

    monkeypatch.setenv("MAX_TRANSCRIPT_CHARS", "10")
    get_settings.cache_clear()  # env changed after app build; re-read it
    app.dependency_overrides[get_analysis_service] = lambda: FakeClaudeService(_sample_analysis())

    resp = client.post("/api/analyze", json={"transcript": "x" * 50})
    assert resp.status_code == 413
    assert resp.json()["error"]["code"] == "transcript_too_large"
    app.dependency_overrides.clear()


def test_analyze_feature_unavailable(client, app):
    app.dependency_overrides[get_analysis_service] = lambda: FakeClaudeService(
        exc=FeatureUnavailableError("no key")
    )
    resp = client.post("/api/analyze", json={"transcript": "hi"})
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "feature_unavailable"
    app.dependency_overrides.clear()


def test_analyze_content_refused(client, app):
    app.dependency_overrides[get_analysis_service] = lambda: FakeClaudeService(
        exc=ContentRefusedError("declined")
    )
    resp = client.post("/api/analyze", json={"transcript": "hi"})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "content_refused"
    app.dependency_overrides.clear()
