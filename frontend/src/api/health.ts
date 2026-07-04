import { apiClient } from './client'

export interface HealthResponse {
  status: string
}

export async function checkHealth(): Promise<HealthResponse> {
  const { data } = await apiClient.get<HealthResponse>('/health')
  return data
}
