"""일정 생성 요청/응답 스키마 (PRD §5.2 요청 / §6 응답).

요청 모델은 방어적 서버 검증(§5.3)을, 응답 모델은 AI 출력의 스키마 준수(§6)를 담당한다.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Literal, get_args

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# §6.4 취향/카테고리 8개 고정 enum — preferences 값과 동일
Category = Literal[
    "체험&액티비티",
    "자연",
    "유명 관광지",
    "힐링",
    "문화&예술&역사",
    "쇼핑",
    "먹방",
    "SNS 핫플레이스",
]
CATEGORIES: tuple[str, ...] = get_args(Category)

# §5.2 동반인
Companion = Literal["혼자", "친구", "연인/배우자", "아이", "부모님", "기타"]

MAX_DURATION_DAYS = 30
MAX_BUDGET_LEN = 30
_TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


# ---- 요청 (§5.2) -----------------------------------------------------------
class ItineraryRequest(BaseModel):
    destination: str = Field(min_length=1, max_length=100)
    start_date: date
    end_date: date
    activity_time_start: str
    activity_time_end: str
    companion: Companion
    preferences: list[Category] = Field(min_length=1)
    budget_level: str

    @field_validator("destination")
    @classmethod
    def _strip_destination(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("여행지를 입력해주세요.")
        return v

    @field_validator("activity_time_start", "activity_time_end")
    @classmethod
    def _validate_time(cls, v: str) -> str:
        if not _TIME_RE.match(v):
            raise ValueError("활동 시간은 HH:MM(24시간제) 형식이어야 합니다.")
        return v

    @field_validator("budget_level")
    @classmethod
    def _validate_budget(cls, v: str) -> str:
        # 공백만 입력된 경우 미입력으로 간주 (§5.3)
        v = v.strip()
        if not v:
            raise ValueError("예산 수준을 입력해주세요.")
        if len(v) > MAX_BUDGET_LEN:
            raise ValueError(f"예산 수준은 최대 {MAX_BUDGET_LEN}자까지 입력할 수 있습니다.")
        return v

    @model_validator(mode="after")
    def _validate_period(self) -> ItineraryRequest:
        if self.end_date < self.start_date:
            raise ValueError("종료일은 시작일과 같거나 이후여야 합니다.")
        if self.duration_days > MAX_DURATION_DAYS:
            raise ValueError(f"여행 기간은 최대 {MAX_DURATION_DAYS}일까지 가능합니다.")
        return self

    @property
    def duration_days(self) -> int:
        # duration_days = end_date - start_date + 1 (§5.2)
        return (self.end_date - self.start_date).days + 1


# ---- 응답 (§6) -------------------------------------------------------------
class Activity(BaseModel):
    id: str
    time: str
    title: str
    description: str
    category: Category
    duration_minutes: int
    location: str
    estimated_cost: int = 0  # 모르면 0 (§6.3)
    tips: str | None = None  # 없으면 null, 빈 문자열 금지 (§6.3)

    @field_validator("estimated_cost", mode="before")
    @classmethod
    def _default_cost(cls, v: object) -> object:
        return 0 if v is None else v

    @field_validator("tips")
    @classmethod
    def _empty_tips_to_none(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        return v or None


class Day(BaseModel):
    day: int
    theme: str
    activities: list[Activity] = Field(min_length=1)


class Meta(BaseModel):
    generated_at: str
    preferences_used: list[str]
    budget_level: str


class Itinerary(BaseModel):
    destination: str
    duration_days: int
    summary: str
    days: list[Day]
    meta: Meta


class AIItinerary(BaseModel):
    """AI 원응답 파싱용 — summary/days만 신뢰하고 나머지는 백엔드가 채운다.

    destination/duration_days/meta 등 AI가 덧붙인 값은 무시(extra=ignore)한다.
    """

    model_config = ConfigDict(extra="ignore")

    summary: str
    days: list[Day]
