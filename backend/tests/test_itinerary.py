import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import app.services.itinerary_service as svc
from app.main import app

client = TestClient(app)

VALID_BODY = {
    "destination": "부산",
    "start_date": "2026-07-10",
    "end_date": "2026-07-12",  # 3일
    "activity_time_start": "09:00",
    "activity_time_end": "21:00",
    "companion": "연인/배우자",
    "preferences": ["먹방", "힐링"],
    "budget_level": "1인당 15만원 이내",
}


def _itinerary_json(days: int) -> str:
    return json.dumps(
        {
            "destination": "부산",
            "duration_days": days,
            "summary": f"부산 {days}일 일정",
            "days": [
                {
                    "day": d,
                    "theme": "테마",
                    "activities": [
                        {
                            "id": f"d{d}-a1",
                            "time": "09:00",
                            "title": "해운대",
                            "description": "바다 산책",
                            "category": "힐링",
                            "duration_minutes": 90,
                            "location": "해운대",
                            "estimated_cost": 0,
                            "tips": "",  # 빈 문자열 → null 로 정규화되어야 함
                        },
                        {
                            "id": f"d{d}-a2",
                            "time": "12:00",
                            "title": "돼지국밥",
                            "description": "현지 맛집 점심",
                            "category": "먹방",
                            "duration_minutes": 60,
                            "location": "서면",
                        },
                    ],
                }
                for d in range(1, days + 1)
            ],
        },
        ensure_ascii=False,
    )


class _FakeCompletions:
    def __init__(self, content: str) -> None:
        self._content = content

    async def create(self, **kwargs) -> object:
        message = SimpleNamespace(content=self._content)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class _FakeClient:
    def __init__(self, content: str) -> None:
        self.chat = SimpleNamespace(completions=_FakeCompletions(content))

    async def close(self) -> None:
        pass


def _patch(monkeypatch: pytest.MonkeyPatch, content: str) -> None:
    monkeypatch.setattr(svc, "_client", lambda: _FakeClient(content))


def test_generate_success(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch(monkeypatch, _itinerary_json(3))
    res = client.post("/api/v1/itinerary", json=VALID_BODY)
    assert res.status_code == 200
    body = res.json()
    assert body["destination"] == "부산"
    assert body["duration_days"] == 3
    assert len(body["days"]) == 3
    # 빈 문자열 tips 는 null 로 정규화 (§6.3)
    assert body["days"][0]["activities"][0]["tips"] is None
    # meta 는 백엔드가 요청값으로 채운다
    assert body["meta"]["preferences_used"] == ["먹방", "힐링"]
    assert body["meta"]["budget_level"] == "1인당 15만원 이내"


def test_validation_error_period_reversed(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch(monkeypatch, _itinerary_json(3))
    bad = {**VALID_BODY, "start_date": "2026-07-12", "end_date": "2026-07-10"}
    res = client.post("/api/v1/itinerary", json=bad)
    assert res.status_code == 422
    assert res.json()["error"] == "VALIDATION_ERROR"


def test_validation_error_over_30_days(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch(monkeypatch, _itinerary_json(3))
    bad = {**VALID_BODY, "start_date": "2026-07-01", "end_date": "2026-08-15"}
    res = client.post("/api/v1/itinerary", json=bad)
    assert res.status_code == 422
    assert res.json() == {
        "error": "VALIDATION_ERROR",
        "message": "여행 기간은 최대 30일까지 가능합니다.",
    }


def test_validation_error_blank_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch(monkeypatch, _itinerary_json(3))
    bad = {**VALID_BODY, "budget_level": "   "}  # 공백만 → 미입력 (§5.3)
    res = client.post("/api/v1/itinerary", json=bad)
    assert res.status_code == 422
    assert res.json()["error"] == "VALIDATION_ERROR"


def test_generation_failed_bad_json(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch(monkeypatch, "이건 JSON이 아닙니다")
    res = client.post("/api/v1/itinerary", json=VALID_BODY)
    assert res.status_code == 502
    assert res.json() == {
        "error": "GENERATION_FAILED",
        "message": "일정을 생성하지 못했어요. 다시 시도해주세요.",
    }


def test_generation_failed_days_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    # 3일 요청인데 AI가 2일치만 반환 → 스키마 불일치 → 502 (§10.1)
    _patch(monkeypatch, _itinerary_json(2))
    res = client.post("/api/v1/itinerary", json=VALID_BODY)
    assert res.status_code == 502
    assert res.json()["error"] == "GENERATION_FAILED"
