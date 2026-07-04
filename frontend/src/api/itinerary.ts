// 일정 생성 API 계층 (PRD §5.2 요청 / §6 응답 / §9 계약)
//
// ⚠️ 백엔드가 아직 없어 지금은 mock 으로 동작한다. 백엔드(FastAPI + OpenRouter)가
// 준비되면 generateItinerary 의 mock 부분을 apiClient.post('/itinerary', payload) 로 교체.

import { apiClient } from './client'

// §6.4 취향/카테고리 (8개 고정 enum) — preferences 값과 동일
export const CATEGORIES = [
  '체험&액티비티',
  '자연',
  '유명 관광지',
  '힐링',
  '문화&예술&역사',
  '쇼핑',
  '먹방',
  'SNS 핫플레이스',
] as const
export type Category = (typeof CATEGORIES)[number]

// §5.2 동반인
export const COMPANIONS = ['혼자', '친구', '연인/배우자', '아이', '부모님', '기타'] as const
export type Companion = (typeof COMPANIONS)[number]

// §5.2 요청 본문
export interface ItineraryRequest {
  destination: string
  start_date: string // YYYY-MM-DD
  end_date: string
  activity_time_start: string // HH:MM
  activity_time_end: string
  companion: Companion
  preferences: string[]
  budget_level: string
}

// §6.3 활동
export interface Activity {
  id: string
  time: string
  title: string
  description: string
  category: Category
  duration_minutes: number
  location: string
  estimated_cost?: number
  tips?: string | null
}

// §6.2 일자
export interface Day {
  day: number
  theme: string
  activities: Activity[]
}

// §6.1 최상위
export interface Itinerary {
  destination: string
  duration_days: number
  summary: string
  days: Day[]
  meta: {
    generated_at: string
    preferences_used: string[]
    budget_level: string
  }
}

// 공통 에러 메시지 (§10.1)
export const GENERATION_FAILED_MESSAGE = '일정을 생성하지 못했어요. 다시 시도해주세요.'

export class ItineraryError extends Error {}

function diffDays(start: string, end: string): number {
  const s = new Date(start).getTime()
  const e = new Date(end).getTime()
  return Math.floor((e - s) / 86_400_000) + 1
}

// ---- mock 생성기 (백엔드 연동 전 화면 개발용) -------------------------------
function buildMock(req: ItineraryRequest): Itinerary {
  const days = diffDays(req.start_date, req.end_date)
  const prefs = req.preferences.length ? req.preferences : ['유명 관광지']
  return {
    destination: req.destination,
    duration_days: days,
    summary: `${req.destination} ${days}일 · ${prefs.join('+')} 중심 일정 (예시)`,
    days: Array.from({ length: days }, (_, i) => {
      const day = i + 1
      return {
        day,
        theme: day === 1 ? '도착 & 시내 탐방' : `${req.destination} 즐기기 ${day}일차`,
        activities: [
          {
            id: `d${day}-a1`,
            time: req.activity_time_start,
            title: `${req.destination} 대표 명소`,
            description: '지역을 대표하는 장소에서 여행을 시작합니다.',
            category: (prefs[0] as Category) ?? '유명 관광지',
            duration_minutes: 120,
            location: req.destination,
            estimated_cost: 15000,
            tips: '오전 일찍 방문하면 붐비지 않아요.',
          },
          {
            id: `d${day}-a2`,
            time: '12:30',
            title: '현지 맛집에서 점심',
            description: '동행과 함께 지역 별미를 즐깁니다.',
            category: '먹방',
            duration_minutes: 90,
            location: `${req.destination} 중심가`,
            estimated_cost: 20000,
            tips: null,
          },
          {
            id: `d${day}-a3`,
            time: '15:00',
            title: '감성 카페 & 산책',
            description: `${prefs[prefs.length - 1]} 취향에 맞춘 여유로운 오후.`,
            category: (prefs[prefs.length - 1] as Category) ?? '힐링',
            duration_minutes: 120,
            location: `${req.destination} 해안/공원`,
            estimated_cost: 8000,
            tips: '노을 시간대를 노려보세요.',
          },
        ],
      }
    }),
    meta: {
      generated_at: new Date().toISOString(),
      preferences_used: req.preferences,
      budget_level: req.budget_level || '중간',
    },
  }
}

/**
 * 일정 생성. 현재는 mock (0.9초 지연 후 예시 일정 반환).
 * 실제 백엔드 연동 시 아래 mock 블록을 apiClient 호출로 교체한다.
 */
export async function generateItinerary(req: ItineraryRequest): Promise<Itinerary> {
  // --- 실제 연동 시 (백엔드 준비 후 주석 해제) ---
  // const { data } = await apiClient.post<Itinerary>('/itinerary', req)
  // return data
  void apiClient // 아직 미사용 (연동 전)

  await new Promise((r) => setTimeout(r, 900))
  return buildMock(req)
}
