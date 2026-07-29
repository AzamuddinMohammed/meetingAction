"""Optional Notion integration: create database pages from action items.

Assumes the target database has (at least) a title property named ``Name``. Other
properties (Owner, Due, Priority) are set only if they exist on the database, so
the export degrades gracefully across differently-shaped databases.
"""

from __future__ import annotations

import logging

import httpx

from ..config import Settings
from ..errors import FeatureUnavailableError, UpstreamError
from ..schemas import ExportedRecord, ExportItem

logger = logging.getLogger(__name__)

_NOTION_VERSION = "2022-06-28"
_NOTION_API = "https://api.notion.com/v1"


class NotionService:
    def __init__(self, settings: Settings):
        self._settings = settings

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._settings.notion_api_key}",
            "Notion-Version": _NOTION_VERSION,
            "Content-Type": "application/json",
        }

    async def create_pages(
        self, items: list[ExportItem], meeting_title: str | None
    ) -> list[ExportedRecord]:
        if not self._settings.notion_configured:
            raise FeatureUnavailableError(
                "Notion export is unavailable: NOTION_API_KEY / NOTION_DATABASE_ID "
                "are not configured."
            )

        async with httpx.AsyncClient(timeout=self._settings.request_timeout_seconds) as client:
            available = await self._database_properties(client)
            created: list[ExportedRecord] = []
            for item in items:
                payload = self._build_payload(item, meeting_title, available)
                try:
                    resp = await client.post(
                        f"{_NOTION_API}/pages", headers=self._headers(), json=payload
                    )
                except httpx.HTTPError as exc:
                    logger.warning("Notion request failed: %s", exc)
                    raise UpstreamError("Could not reach Notion.") from exc

                if resp.status_code >= 400:
                    logger.warning("Notion error %s: %s", resp.status_code, resp.text[:500])
                    raise UpstreamError(
                        f"Notion rejected a page ({resp.status_code}): {resp.text[:200]}"
                    )

                data = resp.json()
                created.append(
                    ExportedRecord(
                        task=item.task,
                        external_id=data.get("id", "unknown"),
                        url=data.get("url"),
                    )
                )
        return created

    async def _database_properties(self, client: httpx.AsyncClient) -> dict[str, str]:
        """Return {property_name: property_type} for the target database."""
        try:
            resp = await client.get(
                f"{_NOTION_API}/databases/{self._settings.notion_database_id}",
                headers=self._headers(),
            )
        except httpx.HTTPError as exc:
            raise UpstreamError("Could not reach Notion.") from exc
        if resp.status_code >= 400:
            raise UpstreamError(
                f"Could not read the Notion database ({resp.status_code})."
            )
        props = resp.json().get("properties", {})
        return {name: meta.get("type", "") for name, meta in props.items()}

    def _title_property_name(self, available: dict[str, str]) -> str:
        for name, prop_type in available.items():
            if prop_type == "title":
                return name
        return "Name"

    def _build_payload(
        self, item: ExportItem, meeting_title: str | None, available: dict[str, str]
    ) -> dict:
        title_prop = self._title_property_name(available)
        properties: dict = {
            title_prop: {"title": [{"text": {"content": item.task[:2000]}}]}
        }

        if available.get("Owner") == "rich_text" and item.owner:
            properties["Owner"] = {"rich_text": [{"text": {"content": item.owner}}]}
        if available.get("Due") == "date" and item.due_date:
            properties["Due"] = {"date": {"start": item.due_date}}
        if available.get("Priority") == "select":
            properties["Priority"] = {"select": {"name": item.priority.capitalize()}}

        children = []
        if meeting_title:
            children.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"type": "text", "text": {"content": f"From meeting: {meeting_title}"}}
                        ]
                    },
                }
            )

        return {
            "parent": {"database_id": self._settings.notion_database_id},
            "properties": properties,
            "children": children,
        }
