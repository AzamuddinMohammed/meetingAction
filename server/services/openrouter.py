"""OpenRouter-backed meeting analysis.

OpenRouter exposes an OpenAI-compatible Chat Completions API that can route to
Claude (and other) models. We ask for a JSON object, embed the target JSON schema
in the system prompt, and validate the reply against ``LlmAnalysis`` — with one
corrective retry — so the result is the same validated structure the Anthropic
path produces.
"""

from __future__ import annotations

import json
import logging

import httpx
from pydantic import ValidationError

from ..config import Settings
from ..errors import FeatureUnavailableError, UpstreamError
from ..prompts import SYSTEM_PROMPT, build_user_prompt
from ..schemas import AnalyzeRequest, LlmAnalysis, MeetingAnalysis
from ._common import to_public_analysis

logger = logging.getLogger(__name__)

_SCHEMA_JSON = json.dumps(LlmAnalysis.model_json_schema(), separators=(",", ":"))
_JSON_INSTRUCTION = (
    "Return your answer as a single JSON object and nothing else — no markdown, "
    "no code fences, no commentary. It must conform to this JSON schema:\n"
    f"{_SCHEMA_JSON}"
)


class OpenRouterService:
    def __init__(self, settings: Settings):
        self._settings = settings

    async def analyze(self, req: AnalyzeRequest) -> tuple[MeetingAnalysis, dict[str, int]]:
        if not self._settings.openrouter_configured:
            raise FeatureUnavailableError(
                "Meeting analysis is unavailable: no analysis provider is configured."
            )

        messages = [
            {"role": "system", "content": f"{SYSTEM_PROMPT}\n\n{_JSON_INSTRUCTION}"},
            {"role": "user", "content": build_user_prompt(req)},
        ]

        async with httpx.AsyncClient(timeout=self._settings.request_timeout_seconds) as client:
            data = await self._call(client, messages)
            content = _message_content(data)

            llm = _try_parse(content)
            if llm is None:
                # One corrective retry: show the model its bad output and re-ask.
                messages.append({"role": "assistant", "content": content})
                messages.append(
                    {
                        "role": "user",
                        "content": "That was not a valid JSON object matching the schema. "
                        "Respond again with only the JSON object.",
                    }
                )
                data = await self._call(client, messages)
                content = _message_content(data)
                llm = _try_parse(content)

        if llm is None:
            logger.error("OpenRouter returned unparseable analysis output")
            raise UpstreamError("The analysis provider returned an unusable response.")

        return to_public_analysis(llm), _extract_usage(data)

    async def _call(self, client: httpx.AsyncClient, messages: list[dict]) -> dict:
        headers = {
            "Authorization": f"Bearer {self._settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "X-Title": self._settings.openrouter_app_title,
        }
        if self._settings.openrouter_site_url:
            headers["HTTP-Referer"] = self._settings.openrouter_site_url

        body = {
            "model": self._settings.openrouter_model,
            "max_tokens": self._settings.analysis_max_tokens,
            "messages": messages,
            "response_format": {"type": "json_object"},
        }

        url = f"{self._settings.openrouter_base_url.rstrip('/')}/chat/completions"
        try:
            resp = await client.post(url, headers=headers, json=body)
        except httpx.HTTPError as exc:
            logger.warning("OpenRouter request failed: %s", exc)
            raise UpstreamError("Could not reach the analysis provider.") from exc

        if resp.status_code >= 400:
            logger.warning("OpenRouter error %s: %s", resp.status_code, resp.text[:500])
            raise UpstreamError(
                f"The analysis provider returned an error ({resp.status_code})."
            )
        return resp.json()


def _message_content(data: dict) -> str:
    try:
        return data["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError) as exc:
        raise UpstreamError("The analysis provider returned an unexpected response.") from exc


def _try_parse(content: str) -> LlmAnalysis | None:
    text = _strip_code_fences(content).strip()
    try:
        return LlmAnalysis.model_validate_json(text)
    except ValidationError:
        return None


def _strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        # Drop the opening fence line (``` or ```json) and any trailing fence.
        stripped = stripped.split("\n", 1)[-1] if "\n" in stripped else ""
        if stripped.rstrip().endswith("```"):
            stripped = stripped.rstrip()[:-3]
    return stripped


def _extract_usage(data: dict) -> dict[str, int]:
    usage = data.get("usage") or {}
    result: dict[str, int] = {}
    if isinstance(usage.get("prompt_tokens"), int):
        result["input_tokens"] = usage["prompt_tokens"]
    if isinstance(usage.get("completion_tokens"), int):
        result["output_tokens"] = usage["completion_tokens"]
    return result
