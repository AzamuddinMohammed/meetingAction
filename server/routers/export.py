"""Export endpoints: push action items into Jira and Notion."""

from __future__ import annotations

from fastapi import APIRouter

from ..dependencies import JiraServiceDep, NotionServiceDep
from ..schemas import ExportRequest, ExportResponse

router = APIRouter(prefix="/export", tags=["export"])


@router.post("/jira", response_model=ExportResponse)
async def export_to_jira(req: ExportRequest, service: JiraServiceDep) -> ExportResponse:
    """Create one Jira issue per action item."""
    created = await service.create_issues(req.action_items, req.meeting_title)
    return ExportResponse(target="jira", created=created)


@router.post("/notion", response_model=ExportResponse)
async def export_to_notion(req: ExportRequest, service: NotionServiceDep) -> ExportResponse:
    """Create one Notion database page per action item."""
    created = await service.create_pages(req.action_items, req.meeting_title)
    return ExportResponse(target="notion", created=created)
