import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Plus, Upload, Play, Download, Trash2, Search, ExternalLink, X, ChevronLeft, ChevronRight, FileText } from 'lucide-react'
import toast from 'react-hot-toast'
import { getLeads, getLead, createLead, createLeadsBulk, uploadCSV, deleteLead } from '../api/leads'
import { triggerAnalysis, triggerBulkAnalysis, triggerAnalyzeAllPending } from '../api/analysis'
import { downloadCSV, downloadExcel } from '../api/export'
import type { Lead, LeadDetail } from '../types'
import AddLeadModal from '../components/leads/AddLeadModal'

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    pending: 'bg-gray-100 text-gray-700',
    analyzing: 'bg-yellow-100 text-yellow-700',
    completed: 'bg-green-100 text-green-700',
    failed: 'bg-red-100 text-red-700',
  }
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${colors[status] || colors.pending}`}>
      {status === 'analyzing' && (
        <span className="mr-1.5 h-2 w-2 animate-pulse rounded-full bg-yellow-400" />
      )}
      {status}
    </span>
  )
}

export default function LeadsPage() {
  const [showAddModal, setShowAddModal] = useState(false)
  const [showSummary, setShowSummary] = useState(false)
  const [summaryIndex, setSummaryIndex] = useState(0)
  const [selected, setSelected] = useState<Set<number>>(new Set())
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [ecommerceOnly, setEcommerceOnly] = useState(false)
  const [withGaps, setWithGaps] = useState(false)
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const queryClient = useQueryClient()

  // Read filters from URL on mount / URL change
  useEffect(() => {
    const urlStatus = searchParams.get('status') || ''
    const urlEcommerce = searchParams.get('ecommerce_only') === 'true'
    const urlGaps = searchParams.get('with_gaps') === 'true'
    setStatusFilter(urlStatus)
    setEcommerceOnly(urlEcommerce)
    setWithGaps(urlGaps)
  }, [searchParams])

  const clearAllFilters = () => {
    setSearch('')
    setStatusFilter('')
    setEcommerceOnly(false)
    setWithGaps(false)
    setSearchParams({})
  }

  const hasActiveFilters = statusFilter || ecommerceOnly || withGaps

  const activeFilterLabel = ecommerceOnly
    ? 'E-commerce Confirmed'
    : withGaps
      ? 'With Gaps Found'
      : statusFilter
        ? statusFilter.charAt(0).toUpperCase() + statusFilter.slice(1)
        : null

  const { data: leads = [], isLoading } = useQuery<Lead[]>({
    queryKey: ['leads', search, statusFilter, ecommerceOnly, withGaps],
    queryFn: () => getLeads({
      search: search || undefined,
      status: statusFilter || undefined,
      ecommerce_only: ecommerceOnly || undefined,
      with_gaps: withGaps || undefined,
      per_page: 200,
    }),
    refetchInterval: 5000,
  })

  const deleteMutation = useMutation({
    mutationFn: deleteLead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leads'] })
      toast.success('Lead deleted')
    },
  })

  const analyzeMutation = useMutation({
    mutationFn: triggerAnalysis,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leads'] })
      toast.success('Analysis started')
    },
    onError: () => toast.error('Failed to start analysis'),
  })

  const bulkAnalyzeMutation = useMutation({
    mutationFn: triggerBulkAnalysis,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leads'] })
      setSelected(new Set())
      toast.success('Bulk analysis started')
    },
  })

  const analyzeAllMutation = useMutation({
    mutationFn: triggerAnalyzeAllPending,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['leads'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
      toast.success(`Analysis started for ${data.lead_ids.length} leads`)
    },
    onError: () => toast.error('Failed to start analysis'),
  })

  const pendingCount = leads.filter((l) => l.status === 'pending').length
  const completedLeads = leads.filter((l) => l.status === 'completed')
  const currentSummaryLead = completedLeads[summaryIndex]

  const { data: summaryDetail } = useQuery<LeadDetail>({
    queryKey: ['lead', currentSummaryLead?.id],
    queryFn: () => getLead(currentSummaryLead!.id),
    enabled: showSummary && !!currentSummaryLead,
  })

  const toggleSelect = (id: number) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const toggleAll = () => {
    if (selected.size === leads.length) {
      setSelected(new Set())
    } else {
      setSelected(new Set(leads.map((l) => l.id)))
    }
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Leads</h1>
          <p className="text-gray-500 mt-1">{leads.length} total leads</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => downloadCSV()}
            className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            <Download className="h-4 w-4" />
            CSV
          </button>
          <button
            onClick={() => downloadExcel()}
            className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            <Download className="h-4 w-4" />
            Excel
          </button>
          {completedLeads.length > 0 && (
            <button
              onClick={() => { setShowSummary(true); setSummaryIndex(0) }}
              className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              <FileText className="h-4 w-4" />
              Summary ({completedLeads.length})
            </button>
          )}
          {pendingCount > 0 && (
            <button
              onClick={() => analyzeAllMutation.mutate()}
              disabled={analyzeAllMutation.isPending}
              className="flex items-center gap-2 rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
            >
              <Play className="h-4 w-4" />
              {analyzeAllMutation.isPending ? 'Starting...' : `Analyze All (${pendingCount})`}
            </button>
          )}
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            <Plus className="h-4 w-4" />
            Add Leads
          </button>
        </div>
      </div>

      {/* Active filter banner */}
      {hasActiveFilters && (
        <div className="mb-4 flex items-center gap-2 rounded-lg bg-blue-50 border border-blue-200 px-4 py-2.5">
          <span className="text-sm text-blue-700">Filtered by:</span>
          <span className="inline-flex items-center gap-1 rounded-full bg-blue-100 px-3 py-0.5 text-sm font-medium text-blue-800">
            {activeFilterLabel}
            <button onClick={clearAllFilters} className="ml-1 rounded-full p-0.5 hover:bg-blue-200">
              <X className="h-3 w-3" />
            </button>
          </span>
        </div>
      )}

      {/* Filters */}
      <div className="mb-4 flex gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search domains..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-gray-300 py-2 pl-10 pr-4 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value)
            setEcommerceOnly(false)
            setWithGaps(false)
            const params: Record<string, string> = {}
            if (e.target.value) params.status = e.target.value
            setSearchParams(params)
          }}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        >
          <option value="">All statuses</option>
          <option value="pending">Pending</option>
          <option value="analyzing">Analyzing</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
        </select>
        {selected.size > 0 && (
          <button
            onClick={() => bulkAnalyzeMutation.mutate(Array.from(selected))}
            className="flex items-center gap-2 rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
          >
            <Play className="h-4 w-4" />
            Analyze {selected.size} selected
          </button>
        )}
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="w-10 px-4 py-3">
                <input
                  type="checkbox"
                  checked={leads.length > 0 && selected.size === leads.length}
                  onChange={toggleAll}
                  className="h-4 w-4 rounded border-gray-300"
                />
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Domain</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Location</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Status</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Source</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Added</th>
              <th className="px-4 py-3 text-right text-xs font-medium uppercase text-gray-500">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {isLoading ? (
              <tr>
                <td colSpan={7} className="px-4 py-12 text-center text-gray-400">
                  <div className="flex justify-center">
                    <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
                  </div>
                </td>
              </tr>
            ) : leads.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-12 text-center text-gray-400">
                  No leads yet. Click "Add Leads" to get started.
                </td>
              </tr>
            ) : (
              leads.map((lead) => (
                <tr key={lead.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => navigate(`/leads/${lead.id}`)}>
                  <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                    <input
                      type="checkbox"
                      checked={selected.has(lead.id)}
                      onChange={() => toggleSelect(lead.id)}
                      className="h-4 w-4 rounded border-gray-300"
                    />
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-900">{lead.domain}</span>
                      <a
                        href={`https://${lead.domain}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="text-gray-400 hover:text-blue-500"
                      >
                        <ExternalLink className="h-3.5 w-3.5" />
                      </a>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {[lead.city, lead.country].filter(Boolean).join(', ') || '-'}
                  </td>
                  <td className="px-4 py-3"><StatusBadge status={lead.status} /></td>
                  <td className="px-4 py-3 text-sm text-gray-500">{lead.source}</td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {new Date(lead.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 text-right" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center justify-end gap-1">
                      {lead.status === 'pending' && (
                        <button
                          onClick={() => analyzeMutation.mutate(lead.id)}
                          className="rounded p-1.5 text-green-600 hover:bg-green-50"
                          title="Analyze"
                        >
                          <Play className="h-4 w-4" />
                        </button>
                      )}
                      <button
                        onClick={() => {
                          if (confirm('Delete this lead?')) deleteMutation.mutate(lead.id)
                        }}
                        className="rounded p-1.5 text-red-500 hover:bg-red-50"
                        title="Delete"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {showAddModal && (
        <AddLeadModal
          onClose={() => setShowAddModal(false)}
          onSuccess={() => {
            queryClient.invalidateQueries({ queryKey: ['leads'] })
            setShowAddModal(false)
          }}
        />
      )}

      {/* Summary Sidebar */}
      {showSummary && (
        <SummarySidebar
          lead={summaryDetail ?? null}
          index={summaryIndex}
          total={completedLeads.length}
          onClose={() => setShowSummary(false)}
          onPrev={() => setSummaryIndex((i) => Math.max(0, i - 1))}
          onNext={() => setSummaryIndex((i) => Math.min(completedLeads.length - 1, i + 1))}
          onViewDetail={(id) => navigate(`/leads/${id}`)}
        />
      )}
    </div>
  )
}

function SummarySidebar({ lead, index, total, onClose, onPrev, onNext, onViewDetail }: {
  lead: LeadDetail | null
  index: number
  total: number
  onClose: () => void
  onPrev: () => void
  onNext: () => void
  onViewDetail: (id: number) => void
}) {
  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />
      <div className="relative w-full max-w-md bg-white shadow-xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Lead Summary</h2>
            <p className="text-sm text-gray-500">{index + 1} of {total} analyzed leads</p>
          </div>
          <button onClick={onClose} className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Navigation */}
        <div className="flex items-center justify-between border-b border-gray-100 px-6 py-2">
          <button onClick={onPrev} disabled={index === 0}
            className="flex items-center gap-1 rounded-lg px-3 py-1.5 text-sm font-medium text-gray-600 hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed">
            <ChevronLeft className="h-4 w-4" /> Prev
          </button>
          <button onClick={onNext} disabled={index === total - 1}
            className="flex items-center gap-1 rounded-lg px-3 py-1.5 text-sm font-medium text-gray-600 hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed">
            Next <ChevronRight className="h-4 w-4" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {!lead ? (
            <div className="flex h-32 items-center justify-center">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
            </div>
          ) : (
            <div className="space-y-5">
              {/* Domain */}
              <div>
                <h3 className="text-xl font-bold text-gray-900">{lead.domain}</h3>
                {lead.company_name && <p className="text-sm text-gray-500">{lead.company_name}</p>}
              </div>

              {/* E-commerce */}
              <SummarySection title="E-commerce">
                {lead.ecommerce ? (
                  <>
                    <SummaryRow label="Is E-commerce" value={lead.ecommerce.is_ecommerce ? 'Yes' : 'No'} highlight={lead.ecommerce.is_ecommerce} />
                    {lead.ecommerce.platform && <SummaryRow label="Platform" value={lead.ecommerce.platform} />}
                    <SummaryRow label="Confidence" value={`${(lead.ecommerce.confidence_score * 100).toFixed(0)}%`} />
                  </>
                ) : <p className="text-sm text-gray-400">Not analyzed</p>}
              </SummarySection>

              {/* Location */}
              {(lead as any).country && (
                <SummarySection title="Location">
                  <SummaryRow label="Location" value={[(lead as any).city, (lead as any).state, (lead as any).country].filter(Boolean).join(', ')} />
                </SummarySection>
              )}

              {/* Marketing Tools */}
              <SummarySection title="Marketing Tools">
                {lead.marketing_tools ? (
                  <>
                    {lead.marketing_tools.all_detected_tools.length > 0 ? (
                      <div className="flex flex-wrap gap-1.5">
                        {lead.marketing_tools.all_detected_tools.map((t) => (
                          <span key={t} className="rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700">
                            {t.replace(/_/g, ' ')}
                          </span>
                        ))}
                      </div>
                    ) : <p className="text-sm text-gray-400">No tools detected</p>}
                  </>
                ) : <p className="text-sm text-gray-400">Not analyzed</p>}
              </SummarySection>

              {/* Ads */}
              <SummarySection title="Ad Activity">
                {lead.ad_activity ? (
                  <>
                    <SummaryRow label="Google Ads" value={lead.ad_activity.is_running_google_ads ? 'Running' : 'None'} highlight={lead.ad_activity.is_running_google_ads} />
                    <SummaryRow label="Meta Ads" value={lead.ad_activity.is_running_meta_ads ? 'Running' : 'None'} highlight={lead.ad_activity.is_running_meta_ads} />
                    <SummaryRow label="TikTok Ads" value={lead.ad_activity.is_running_tiktok_ads ? 'Running' : 'None'} highlight={lead.ad_activity.is_running_tiktok_ads} />
                  </>
                ) : <p className="text-sm text-gray-400">Not analyzed</p>}
              </SummarySection>

              {/* Contacts */}
              <SummarySection title="Contacts">
                {lead.contacts.length > 0 ? (
                  <div className="space-y-1">
                    {lead.contacts.slice(0, 5).map((c) => (
                      <div key={c.id} className="flex items-center justify-between text-sm">
                        <span className="font-medium text-gray-800 truncate max-w-[200px]">{c.value}</span>
                        <span className="text-xs text-gray-400 ml-2 shrink-0">{c.source}</span>
                      </div>
                    ))}
                    {lead.contacts.length > 5 && (
                      <p className="text-xs text-gray-400">+{lead.contacts.length - 5} more</p>
                    )}
                  </div>
                ) : <p className="text-sm text-gray-400">No contacts found</p>}
              </SummarySection>

              {/* Gaps */}
              <SummarySection title="Gaps Found">
                {lead.pitch?.gaps_identified && lead.pitch.gaps_identified.length > 0 ? (
                  <ul className="space-y-1">
                    {lead.pitch.gaps_identified.slice(0, 5).map((g, i) => (
                      <li key={i} className="text-sm text-orange-700 flex items-start gap-1.5">
                        <span className="mt-1 h-1.5 w-1.5 rounded-full bg-orange-400 shrink-0" />
                        {g}
                      </li>
                    ))}
                  </ul>
                ) : <p className="text-sm text-gray-400">No gaps identified</p>}
              </SummarySection>

              {/* Social */}
              <SummarySection title="Social Media">
                {lead.social_media ? (
                  <div className="space-y-1">
                    {[
                      { name: 'Instagram', url: lead.social_media.instagram_url },
                      { name: 'Facebook', url: lead.social_media.facebook_url },
                      { name: 'TikTok', url: lead.social_media.tiktok_url },
                      { name: 'LinkedIn', url: lead.social_media.linkedin_url },
                    ].filter((p) => p.url).map((p) => (
                      <div key={p.name} className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">{p.name}</span>
                        <a href={p.url!} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline text-xs truncate max-w-[180px]">
                          {p.url!.replace(/https?:\/\/(www\.)?/, '').slice(0, 40)}
                        </a>
                      </div>
                    ))}
                    {!lead.social_media.instagram_url && !lead.social_media.facebook_url &&
                     !lead.social_media.tiktok_url && !lead.social_media.linkedin_url && (
                      <p className="text-sm text-gray-400">No social profiles found</p>
                    )}
                  </div>
                ) : <p className="text-sm text-gray-400">Not analyzed</p>}
              </SummarySection>
            </div>
          )}
        </div>

        {/* Footer */}
        {lead && (
          <div className="border-t border-gray-200 px-6 py-3">
            <button
              onClick={() => onViewDetail(lead.id)}
              className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              View Full Details
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

function SummarySection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h4 className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-2">{title}</h4>
      {children}
    </div>
  )
}

function SummaryRow({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="flex items-center justify-between text-sm py-0.5">
      <span className="text-gray-500">{label}</span>
      <span className={`font-medium ${highlight ? 'text-green-600' : 'text-gray-800'}`}>{value}</span>
    </div>
  )
}
