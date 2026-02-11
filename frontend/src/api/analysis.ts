import api from './client'
import type { AnalysisStatus } from '../types'

export async function triggerAnalysis(leadId: number): Promise<void> {
  await api.post(`/analysis/${leadId}`)
}

export async function triggerBulkAnalysis(leadIds: number[]): Promise<void> {
  await api.post('/analysis/bulk', { lead_ids: leadIds })
}

export async function triggerAnalyzeAllPending(): Promise<{ lead_ids: number[] }> {
  const { data } = await api.post('/analysis/all-pending')
  return data
}

export async function getAnalysisStatus(leadId: number): Promise<AnalysisStatus> {
  const { data } = await api.get(`/analysis/${leadId}/status`)
  return data
}
