"""Optional Jira Cloud integration: create issues from action items.

Uses the Jira Cloud REST API v3 with Basic auth (email + API token). Enabled only
when all four JIRA_* settings are present.
"""

from __future__ import annotations

import base64
import logging

import httpx

from ..config import Settings
from ..errors import FeatureUnavailableError, UpstreamError
from ..schemas import ExportedRecord, ExportItem

logger = logging.getLogger(__name__)

# Jira priority names vary per project; map our scale to common defaults.
_PRIORITY_MAP = {"low": "Low", "medium": "Medium", "high": "High"}


class JiraService:
    def __init__(self, settings: Settings):
        self._settings = settings

    def _auth_header(self) -> str:
        raw = f"{self._settings.jira_email}:{self._settings.jira_api_token}".encode()
        return "Basic " + base64.b64encode(raw).decode()

    async def create_issues(
        self, items: list[ExportItem], meeting_title: str | None
    ) -> list[ExportedRecord]:
        if not self._settings.jira_configured:
            raise FeatureUnavailableError(
                "Jira export is unavailable: JIRA_* settings are not configured."
            )

        base = self._settings.jira_base_url.rstrip("/")
        url = f"{base}/rest/api/3/issue"
        headers = {
            "Authorization": self._auth_header(),
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        created: list[ExportedRecord] = []
        async with httpx.AsyncClient(timeout=self._settings.request_timeout_seconds) as client:
            for item in items:
                payload = self._build_payload(item, meeting_title)
                try:
                    resp = await client.post(url, headers=headers, json=payload)
                except httpx.HTTPError as exc:
                    logger.warning("Jira request failed: %s", exc)
                    raise UpstreamError("Could not reach Jira.") from exc

                if resp.status_code >= 400:
                    logger.warning("Jira error %s: %s", resp.status_code, resp.text[:500])
                    raise UpstreamError(
                        f"Jira rejected an issue ({resp.status_code}): {resp.text[:200]}"
                    )

                data = resp.json()
                key = data.get("key", data.get("id", "unknown"))
                created.append(
                    ExportedRecord(
                        task=item.task,
                        external_id=key,
                        url=f"{base}/browse/{key}",
                    )
                )
        return created

    def _build_payload(self, item: ExportItem, meeting_title: str | None) -> dict:
        description_lines = [item.task]
        if item.owner:
            description_lines.append(f"Owner: {item.owner}")
        if item.due_date:
            description_lines.append(f"Due: {item.due_date}")
        if meeting_title:
            description_lines.append(f"From meeting: {meeting_title}")

        fields: dict = {
            "project": {"key": self._settings.jira_project_key},
            "summary": item.task[:250],
            "issuetype": {"name": self._settings.jira_issue_type},
            "description": _adf_paragraph("\n".join(description_lines)),
        }
        priority_name = _PRIORITY_MAP.get(item.priority)
        if priority_name:
            fields["priority"] = {"name": priority_name}
        if item.due_date:
            # Jira expects YYYY-MM-DD; pass through if it looks like a date.
            fields["duedate"] = item.due_date
        return {"fields": fields}


def _adf_paragraph(text: str) -> dict:
    """Wrap plain text in a minimal Atlassian Document Format node."""
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": text}],
            }
        ],
    }
