import api from './client'
import type { Lead, LeadDetail, Stats } from '../types'

export async function getLeads(params?: {
  page?: number
  per_page?: number
  status?: string
  search?: string
  ecommerce_only?: boolean
  with_gaps?: boolean
}): Promise<Lead[]> {
  const { data } = await api.get('/leads', { params })
  return data
}

export async function getLead(id: number): Promise<LeadDetail> {
  const { data } = await api.get(`/leads/${id}`)
  return data
}

export async function createLead(domain: string): Promise<Lead> {
  const { data } = await api.post('/leads', { domain })
  return data
}

export async function createLeadsBulk(domains: string[]): Promise<Lead[]> {
  const { data } = await api.post('/leads/bulk', { domains })
  return data
}

export async function uploadCSV(file: File): Promise<Lead[]> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post('/leads/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function deleteLead(id: number): Promise<void> {
  await api.delete(`/leads/${id}`)
}

export async function getStats(): Promise<Stats> {
  const { data } = await api.get('/leads/stats')
  return data
}
