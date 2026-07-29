"""Prompt construction for meeting analysis.

The system prompt is kept static (no interpolation) so it stays a stable prefix
for prompt caching. Per-meeting context (title, attendees, date) is placed in the
user turn instead.
"""

from __future__ import annotations

from .schemas import AnalyzeRequest

SYSTEM_PROMPT = """You are an expert meeting assistant. You read a raw meeting \
transcript or set of notes and extract a faithful, well-structured record.

Rules:
- Ground every item in what was actually said. Do not invent action items, \
owners, decisions, or dates that are not supported by the transcript.
- If an owner or due date is not stated or clearly implied, leave it null rather \
than guessing.
- Write the summary and email in clear, neutral, professional prose.
- Deduplicate: if the same task is mentioned several times, produce one action item.
- Order action items by priority (high first), then by the order they arose.
- The follow-up email should be ready to send: greet attendees, summarize \
outcomes and decisions, list who owns what by when, and close politely. Do not \
include placeholders like [Name] unless the information is genuinely unknown.
- Respond only with the structured data requested; do not add commentary."""


def build_user_prompt(req: AnalyzeRequest) -> str:
    """Assemble the user-turn prompt from the request metadata and transcript."""
    header_lines: list[str] = []
    if req.meeting_title:
        header_lines.append(f"Meeting title: {req.meeting_title}")
    if req.meeting_date:
        header_lines.append(f"Meeting date: {req.meeting_date}")
    if req.attendees:
        header_lines.append("Attendees: " + ", ".join(req.attendees))

    if not req.options.include_email:
        header_lines.append(
            "Note: a follow-up email is still required by the schema; keep it brief."
        )

    header = "\n".join(header_lines)
    context_block = f"{header}\n\n" if header else ""

    return (
        f"{context_block}"
        "Analyze the following meeting transcript and produce the structured "
        "record.\n\n"
        "<transcript>\n"
        f"{req.transcript.strip()}\n"
        "</transcript>"
    )
