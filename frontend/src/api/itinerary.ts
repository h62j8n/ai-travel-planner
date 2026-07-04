// 일정 생성 API 계층 (PRD §5.2 요청 / §6 응답 / §9 계약)

import axios from 'axios'
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

/**
 * 일정 생성. 백엔드(FastAPI + OpenRouter)의 POST /api/v1/itinerary 를 호출한다.
 * 실패 시(§9 계약: VALIDATION_ERROR / GENERATION_FAILED) 서버 메시지를 담아
 * ItineraryError 를 던진다. 서버 메시지가 없으면 공통 실패 메시지를 사용한다.
 */
export async function generateItinerary(req: ItineraryRequest): Promise<Itinerary> {
  try {
    const { data } = await apiClient.post<Itinerary>('/itinerary', req)
    return data
  } catch (err) {
    const serverMessage =
      axios.isAxiosError(err) && (err.response?.data as { message?: string } | undefined)?.message
    throw new ItineraryError(serverMessage || GENERATION_FAILED_MESSAGE)
  }
}
