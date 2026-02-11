import api from './client'

export async function downloadCSV(leadIds?: number[]): Promise<void> {
  const params = leadIds ? { lead_ids: leadIds.join(',') } : {}
  const { data } = await api.get('/export/csv', { params, responseType: 'blob' })
  downloadBlob(data, 'leads_export.csv', 'text/csv')
}

export async function downloadExcel(leadIds?: number[]): Promise<void> {
  const params = leadIds ? { lead_ids: leadIds.join(',') } : {}
  const { data } = await api.get('/export/excel', { params, responseType: 'blob' })
  downloadBlob(
    data,
    'leads_export.xlsx',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  )
}

function downloadBlob(blob: Blob, filename: string, type: string) {
  const url = window.URL.createObjectURL(new Blob([blob], { type }))
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}
