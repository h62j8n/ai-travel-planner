import axios from 'axios'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api/v1',
  // 백엔드 AI 호출은 20초 타임아웃 + 1회 재시도(최대 ~40초, PRD §10.1)라
  // 클라이언트 타임아웃은 그보다 넉넉하게 잡는다.
  timeout: 45_000,
})
