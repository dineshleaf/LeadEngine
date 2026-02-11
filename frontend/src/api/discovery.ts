import api from './client'
import type { DiscoveryResult, Lead } from '../types'

export async function searchDomains(query: string, maxResults = 20): Promise<DiscoveryResult[]> {
  const { data } = await api.post('/discovery/search', { query, max_results: maxResults })
  return data
}

export async function importDomains(domains: string[]): Promise<Lead[]> {
  const { data } = await api.post('/discovery/import', { domains })
  return data
}
