"""AI 시스템/유저 프롬프트 (PRD §7).

시스템 프롬프트에 §6 JSON 스키마와 "JSON만 출력" 규칙을 명시해 스키마 준수를 강제한다.
"""

from __future__ import annotations

import json

from app.schemas.itinerary import CATEGORIES, ItineraryRequest

_CATEGORY_LIST = " · ".join(CATEGORIES)

SYSTEM_PROMPT = f"""너는 국내 여행 일정을 짜주는 전문 플래너다. 사용자가 준 여행 조건에 맞춰 일자별 여행 일정을 생성한다.

반드시 아래 JSON 스키마를 100% 준수해서 응답하고, JSON 외의 텍스트(설명, 인사말, 마크다운 코드블록 표시 ```json 등)는 절대 포함하지 마라. 오직 JSON 객체 하나만 출력한다.

스키마:
{{
  "destination": "문자열, 사용자 입력값 그대로",
  "duration_days": 숫자,
  "summary": "전체 일정 한 줄 요약",
  "days": [
    {{
      "day": 1,
      "theme": "그날의 테마 한 줄",
      "activities": [
        {{
          "id": "d1-a1",
          "time": "09:00",
          "title": "활동명",
          "description": "1~2문장 설명",
          "category": "아래 8개 값 중 하나",
          "duration_minutes": 120,
          "location": "지역/장소명",
          "estimated_cost": 3000,
          "tips": "유용한 팁 또는 null"
        }}
      ]
    }}
  ]
}}

규칙:
- category 값은 반드시 사용자가 선택한 취향(preferences) 목록 안의 값만 사용한다. 선택되지 않은 카테고리(예: 사용자가 고르지 않은 "쇼핑", "유명 관광지", "문화&예술&역사" 등)는 절대 일정에 넣지 마라.
- 모든 활동은 사용자가 선택한 취향 중 하나에 실제로 부합해야 한다. 취향과 무관한 관광지·쇼핑·명소 채우기는 금지한다.
- 이동/체크인 등 불가피한 로지스틱스는 최소화하고, 넣더라도 category는 반드시 선택된 취향 값 중 가장 가까운 것으로 태깅한다.
- (참고) 전체 카테고리 enum은 다음 8개다: {_CATEGORY_LIST}. 이 중 사용자가 고른 값만 실제로 쓸 수 있다.
- days 배열의 길이는 요청받은 duration_days와 반드시 정확히 일치해야 한다. day는 1부터 순서대로.
- 각 day의 activities는 최소 2개, 최대 5개로 구성한다.
- id는 "d{{day}}-a{{index}}" 형식으로 만든다 (예: d2-a3).
- time은 "HH:MM" 24시간제로 표기하고, 사용자가 준 활동 시간 범위 안에서 시간순으로 배치한다.
- estimated_cost는 원화 정수이며 모르면 0으로 둔다.
- tips는 실제로 유용한 정보가 있을 때만 문자열로 넣고, 없으면 null로 둔다. 빈 문자열("")은 금지한다.
- 예산 수준(budget_level) 입력값이 모호하면 "중간" 수준으로 기본 처리한다.
- 동반인(companion)과 취향(preferences)을 일정 구성에 적극 반영한다.
"""


def build_user_prompt(req: ItineraryRequest) -> str:
    payload = {
        "destination": req.destination,
        "start_date": req.start_date.isoformat(),
        "end_date": req.end_date.isoformat(),
        "activity_time_start": req.activity_time_start,
        "activity_time_end": req.activity_time_end,
        "companion": req.companion,
        "preferences": list(req.preferences),
        "budget_level": req.budget_level,
        "duration_days": req.duration_days,
    }
    allowed = " · ".join(req.preferences)
    return (
        f"다음 조건으로 여행 일정을 생성해줘. "
        f"duration_days는 정확히 {req.duration_days}이고 days 배열 길이도 정확히 {req.duration_days}여야 해.\n"
        f"각 활동의 category는 반드시 다음 취향 값들 중 하나여야 하고, 그 외 카테고리는 절대 쓰지 마: {allowed}\n\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )
