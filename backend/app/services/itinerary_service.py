"""OpenRouter 무료 모델을 호출해 일정을 생성하는 서비스 (PRD §7, §8.2, §10.1).

- openai 공식 SDK의 base_url을 OpenRouter로 지정해 호출한다.
- 타임아웃 20초, 실패 시 최대 1회 자동 재시도 후 GenerationError(502/504)로 종료한다.
- AI 응답은 JSON 파싱 후 Pydantic(AIItinerary)으로 검증하고, destination/duration_days/meta는
  백엔드가 요청값으로 확정해 스키마(§6)를 보장한다.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone

from openai import APITimeoutError, AsyncOpenAI, BadRequestError

from app.core.config import settings
from app.core.prompts import SYSTEM_PROMPT, build_user_prompt
from app.schemas.itinerary import AIItinerary, Itinerary, ItineraryRequest, Meta

logger = logging.getLogger("itinerary")

# 공통 실패 메시지 (§9 / §10.1)
GENERATION_FAILED_MESSAGE = "일정을 생성하지 못했어요. 다시 시도해주세요."


class GenerationError(Exception):
    """AI 호출/파싱 실패. status_code: 타임아웃 504, 그 외 502 (§9)."""

    def __init__(self, status_code: int = 502) -> None:
        self.status_code = status_code
        super().__init__(GENERATION_FAILED_MESSAGE)


_FENCE_RE = re.compile(r"^```(?:json)?|```$", re.IGNORECASE | re.MULTILINE)


def _extract_json(content: str) -> str:
    """모델이 코드블록/여분 텍스트를 붙여도 JSON 본문만 뽑아낸다."""
    text = _FENCE_RE.sub("", content).strip()
    if not text.startswith("{"):
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start : end + 1]
    return text.strip()


def _client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        timeout=settings.ai_timeout_seconds,
        max_retries=0,  # 재시도/폴백은 서비스에서 직접 관리 (§10.1)
        default_headers={"X-Title": "AI Travel Planner"},
    )


def _build(req: ItineraryRequest, ai: AIItinerary) -> Itinerary:
    # destination/duration_days/meta는 요청값으로 확정해 스키마를 보장한다 (§6.1)
    return Itinerary(
        destination=req.destination,
        duration_days=req.duration_days,
        summary=ai.summary,
        days=ai.days,
        meta=Meta(
            generated_at=datetime.now(timezone.utc).isoformat(),
            preferences_used=list(req.preferences),
            budget_level=req.budget_level,
        ),
    )


async def _call(
    client: AsyncOpenAI, model: str, messages: list[dict], use_json_format: bool
) -> str:
    kwargs: dict = {"model": model, "messages": messages, "temperature": 0.7}
    if use_json_format:
        kwargs["response_format"] = {"type": "json_object"}
    resp = await client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content or ""


async def generate_itinerary(req: ItineraryRequest) -> Itinerary:
    client = _client()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(req)},
    ]
    status_code = 502
    try:
        # 무료 모델 rate-limit(429) 대비 모델 체인을 순차 시도한다 (§10.1).
        for model in settings.model_list:
            # 각 모델에 대해 json_object 강제 → 미지원(400)이면 일반 모드로 1회 재시도.
            for use_json in (True, False):
                try:
                    content = await _call(client, model, messages, use_json)
                    data = json.loads(_extract_json(content))
                    ai = AIItinerary.model_validate(data)
                    if len(ai.days) != req.duration_days:
                        raise ValueError("days length does not match duration_days")
                    return _build(req, ai)
                except APITimeoutError as exc:
                    logger.warning("model %s timed out: %s", model, exc)
                    status_code = 504
                    break  # 다음 모델로
                except BadRequestError as exc:
                    # response_format 미지원 등 → 일반 모드로 재시도 (같은 모델)
                    logger.warning("model %s bad request (json=%s): %s", model, use_json, exc)
                    status_code = 502
                    continue
                except Exception as exc:
                    # 429/네트워크/파싱/스키마 불일치 → 다음 모델로
                    logger.warning("model %s failed (json=%s): %s", model, use_json, exc)
                    status_code = 502
                    break  # 다음 모델로
        raise GenerationError(status_code=status_code)
    finally:
        await client.close()
