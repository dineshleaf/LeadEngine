import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft, Play, ShoppingCart, BarChart3, Server, Megaphone,
  Share2, Users, Phone, MessageSquare, CheckCircle, XCircle,
  ExternalLink, Copy, RefreshCw
} from 'lucide-react'
import toast from 'react-hot-toast'
import { getLead } from '../api/leads'
import { triggerAnalysis, getAnalysisStatus } from '../api/analysis'
import type { LeadDetail, AnalysisStatus } from '../types'

const TABS = [
  { key: 'ecommerce', label: 'E-commerce', icon: ShoppingCart },
  { key: 'marketing', label: 'Marketing Tools', icon: BarChart3 },
  { key: 'hosting', label: 'Hosting & Email', icon: Server },
  { key: 'ads', label: 'Ad Activity', icon: Megaphone },
  { key: 'social', label: 'Social Media', icon: Share2 },
  { key: 'contacts', label: 'Contacts', icon: Phone },
  { key: 'people', label: 'Decision Makers', icon: Users },
  { key: 'pitch', label: 'Pitch', icon: MessageSquare },
] as const

function Bool({ value }: { value: boolean | null | undefined }) {
  if (value === true) return <CheckCircle className="h-5 w-5 text-green-500" />
  if (value === false) return <XCircle className="h-5 w-5 text-red-400" />
  return <span className="text-gray-400">-</span>
}

function InfoRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between border-b border-gray-100 py-3 last:border-b-0">
      <span className="text-sm text-gray-500 w-48 shrink-0">{label}</span>
      <span className="text-sm font-medium text-gray-900 text-right">{value ?? '-'}</span>
    </div>
  )
}

export default function LeadDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<string>('ecommerce')

  const { data: lead, isLoading } = useQuery<LeadDetail>({
    queryKey: ['lead', id],
    queryFn: () => getLead(Number(id)),
    refetchInterval: (query) => {
      return query.state.data?.status === 'analyzing' ? 3000 : false
    },
  })

  const { data: progress } = useQuery<AnalysisStatus>({
    queryKey: ['analysis-status', id],
    queryFn: () => getAnalysisStatus(Number(id)),
    enabled: lead?.status === 'analyzing',
    refetchInterval: 2000,
  })

  const analyzeMutation = useMutation({
    mutationFn: triggerAnalysis,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lead', id] })
      toast.success('Analysis started')
    },
    onError: (err: any) => toast.error(err?.response?.data?.detail || 'Failed to start analysis'),
  })

  if (isLoading || !lead) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
      </div>
    )
  }

  const completedModules = progress
    ? Object.values(progress.modules).filter((s) => s === 'completed').length
    : 0
  const totalModules = progress ? Object.keys(progress.modules).length : 8

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <button onClick={() => navigate('/leads')} className="mb-4 flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700">
          <ArrowLeft className="h-4 w-4" /> Back to Leads
        </button>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{lead.domain}</h1>
            <p className="text-gray-500 mt-1">
              {lead.company_name || lead.domain} &middot; {lead.status}
              {lead.status === 'analyzing' && (
                <span className="ml-2 text-yellow-600">
                  ({completedModules}/{totalModules} modules)
                </span>
              )}
            </p>
          </div>
          <div className="flex gap-2">
            <a
              href={`https://${lead.domain}`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              <ExternalLink className="h-4 w-4" /> Visit Site
            </a>
            {(lead.status === 'pending' || lead.status === 'completed' || lead.status === 'failed') && (
              <button
                onClick={() => analyzeMutation.mutate(lead.id)}
                className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                {lead.status === 'completed' || lead.status === 'failed' ? (
                  <><RefreshCw className="h-4 w-4" /> Re-analyze</>
                ) : (
                  <><Play className="h-4 w-4" /> Analyze</>
                )}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Progress bar when analyzing */}
      {lead.status === 'analyzing' && progress && (
        <div className="mb-6 rounded-xl bg-white p-4 border border-gray-200 shadow-sm">
          <div className="mb-2 flex justify-between text-sm">
            <span className="font-medium">Analysis in progress...</span>
            <span className="text-gray-500">{completedModules}/{totalModules}</span>
          </div>
          <div className="h-2 rounded-full bg-gray-200">
            <div
              className="h-2 rounded-full bg-blue-500 transition-all"
              style={{ width: `${(completedModules / totalModules) * 100}%` }}
            />
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            {Object.entries(progress.modules).map(([key, status]) => (
              <span
                key={key}
                className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                  status === 'completed' ? 'bg-green-100 text-green-700' :
                  status === 'running' ? 'bg-yellow-100 text-yellow-700' :
                  status === 'failed' ? 'bg-red-100 text-red-700' :
                  'bg-gray-100 text-gray-500'
                }`}
              >
                {key}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Tabs */}
      {lead.status === 'completed' && (
        <>
          <div className="mb-6 flex gap-1 overflow-x-auto rounded-xl bg-white p-1 border border-gray-200 shadow-sm">
            {TABS.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium whitespace-nowrap transition ${
                  activeTab === tab.key
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <tab.icon className="h-4 w-4" />
                {tab.label}
              </button>
            ))}
          </div>

          <div className="rounded-xl bg-white border border-gray-200 shadow-sm p-6">
            {activeTab === 'ecommerce' && <EcommerceTab lead={lead} />}
            {activeTab === 'marketing' && <MarketingTab lead={lead} />}
            {activeTab === 'hosting' && <HostingTab lead={lead} />}
            {activeTab === 'ads' && <AdsTab lead={lead} />}
            {activeTab === 'social' && <SocialTab lead={lead} />}
            {activeTab === 'contacts' && <ContactsTab lead={lead} />}
            {activeTab === 'people' && <PeopleTab lead={lead} />}
            {activeTab === 'pitch' && <PitchTab lead={lead} />}
          </div>
        </>
      )}
    </div>
  )
}

function EcommerceTab({ lead }: { lead: LeadDetail }) {
  const ec = lead.ecommerce
  if (!ec) return <p className="text-gray-500">No e-commerce data available.</p>
  return (
    <div>
      <h3 className="text-lg font-semibold mb-4">E-commerce Detection</h3>
      <InfoRow label="Is E-commerce" value={<Bool value={ec.is_ecommerce} />} />
      <InfoRow label="Platform" value={ec.platform || 'Unknown'} />
      <InfoRow label="Confidence" value={`${(ec.confidence_score * 100).toFixed(0)}%`} />
      <InfoRow label="Has Cart" value={<Bool value={ec.has_cart} />} />
      <InfoRow label="Has Product Pages" value={<Bool value={ec.has_product_pages} />} />
      <InfoRow label="Has Checkout" value={<Bool value={ec.has_checkout} />} />
      {ec.evidence.length > 0 && (
        <div className="mt-4">
          <p className="text-sm font-medium text-gray-700 mb-2">Evidence</p>
          <ul className="space-y-1">
            {ec.evidence.map((e, i) => (
              <li key={i} className="text-sm text-gray-600 flex items-start gap-2">
                <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 shrink-0" />
                {e}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function MarketingTab({ lead }: { lead: LeadDetail }) {
  const mt = lead.marketing_tools
  if (!mt) return <p className="text-gray-500">No marketing tools data available.</p>
  return (
    <div>
      <h3 className="text-lg font-semibold mb-4">Marketing Tools</h3>
      <InfoRow label="Google Analytics" value={<Bool value={mt.has_google_analytics} />} />
      {mt.has_google_analytics && <InfoRow label="GA Version" value={mt.ga_version} />}
      {mt.ga_id && <InfoRow label="GA ID" value={mt.ga_id} />}
      <InfoRow label="Google Tag Manager" value={<Bool value={mt.has_gtm} />} />
      {mt.gtm_id && <InfoRow label="GTM ID" value={mt.gtm_id} />}
      <InfoRow label="Google Search Console" value={<Bool value={mt.has_gsc} />} />
      <InfoRow label="Facebook Pixel" value={<Bool value={mt.has_facebook_pixel} />} />
      {mt.fb_pixel_id && <InfoRow label="FB Pixel ID" value={mt.fb_pixel_id} />}
      <InfoRow label="TikTok Pixel" value={<Bool value={mt.has_tiktok_pixel} />} />
      <InfoRow label="Microsoft Clarity" value={<Bool value={mt.has_clarity} />} />
      <InfoRow label="Hotjar" value={<Bool value={mt.has_hotjar} />} />
      <InfoRow label="Mixpanel" value={<Bool value={mt.has_mixpanel} />} />
      <InfoRow label="Segment" value={<Bool value={mt.has_segment} />} />
      <InfoRow label="Heap" value={<Bool value={mt.has_heap} />} />
      <InfoRow label="Amplitude" value={<Bool value={mt.has_amplitude} />} />
      {mt.all_detected_tools.length > 0 && (
        <div className="mt-4">
          <p className="text-sm font-medium text-gray-700 mb-2">All Detected Tools</p>
          <div className="flex flex-wrap gap-2">
            {mt.all_detected_tools.map((tool) => (
              <span key={tool} className="rounded-full bg-blue-100 px-3 py-1 text-xs font-medium text-blue-700">
                {tool.replace(/_/g, ' ')}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function HostingTab({ lead }: { lead: LeadDetail }) {
  const he = lead.hosting_email
  if (!he) return <p className="text-gray-500">No hosting/email data available.</p>
  return (
    <div>
      <h3 className="text-lg font-semibold mb-4">Hosting & Email</h3>
      <InfoRow label="Hosting Provider" value={he.hosting_provider} />
      <InfoRow label="IP Address" value={he.ip_address} />
      <InfoRow label="CDN Provider" value={he.cdn_provider} />
      <InfoRow label="Email Provider" value={he.email_provider} />
      <InfoRow label="Registrar" value={he.registrar} />
      <InfoRow label="Registration Date" value={he.registration_date} />
      {he.nameservers.length > 0 && (
        <InfoRow label="Nameservers" value={he.nameservers.join(', ')} />
      )}
      {he.mx_records.length > 0 && (
        <InfoRow label="MX Records" value={he.mx_records.join(', ')} />
      )}
    </div>
  )
}

function AdsTab({ lead }: { lead: LeadDetail }) {
  const ad = lead.ad_activity
  if (!ad) return <p className="text-gray-500">No ad activity data available.</p>
  return (
    <div>
      <h3 className="text-lg font-semibold mb-4">Ad Activity</h3>
      <InfoRow label="Google Ads" value={<Bool value={ad.is_running_google_ads} />} />
      {ad.is_running_google_ads && <InfoRow label="Google Ads Count" value={ad.google_ads_count} />}
      <InfoRow label="Meta/Facebook Ads" value={<Bool value={ad.is_running_meta_ads} />} />
      {ad.is_running_meta_ads && <InfoRow label="Meta Ads Count" value={ad.meta_ads_count} />}
      <InfoRow label="TikTok Ads" value={<Bool value={ad.is_running_tiktok_ads} />} />
      {ad.is_running_tiktok_ads && <InfoRow label="TikTok Ads Count" value={ad.tiktok_ads_count} />}
    </div>
  )
}

function SocialTab({ lead }: { lead: LeadDetail }) {
  const sm = lead.social_media
  if (!sm) return <p className="text-gray-500">No social media data available.</p>

  const platforms = [
    { name: 'Instagram', url: sm.instagram_url, active: sm.instagram_active },
    { name: 'Facebook', url: sm.facebook_url, active: sm.facebook_active },
    { name: 'TikTok', url: sm.tiktok_url, active: sm.tiktok_active },
    { name: 'Twitter / X', url: sm.twitter_url, active: sm.twitter_active },
    { name: 'LinkedIn', url: sm.linkedin_url, active: sm.linkedin_active },
    { name: 'YouTube', url: sm.youtube_url, active: null },
  ]

  return (
    <div>
      <h3 className="text-lg font-semibold mb-4">Social Media</h3>
      {platforms.map((p) => (
        <div key={p.name} className="flex items-center justify-between border-b border-gray-100 py-3 last:border-b-0">
          <span className="text-sm text-gray-500 w-32">{p.name}</span>
          <div className="flex items-center gap-3">
            {p.active !== null && <Bool value={p.active} />}
            {p.url ? (
              <a href={p.url} target="_blank" rel="noopener noreferrer"
                className="text-sm text-blue-600 hover:underline flex items-center gap-1">
                {p.url.slice(0, 50)} <ExternalLink className="h-3 w-3" />
              </a>
            ) : (
              <span className="text-sm text-gray-400">Not found</span>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

function ContactsTab({ lead }: { lead: LeadDetail }) {
  const emails = lead.contacts.filter((c) => c.type === 'email')
  const phones = lead.contacts.filter((c) => c.type === 'phone')
  return (
    <div>
      <h3 className="text-lg font-semibold mb-4">Contact Information</h3>
      {lead.contacts.length === 0 ? (
        <p className="text-gray-500">No contact information found.</p>
      ) : (
        <>
          {emails.length > 0 && (
            <div className="mb-6">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Emails</h4>
              {emails.map((c) => (
                <div key={c.id} className="flex items-center justify-between py-2 border-b border-gray-100">
                  <span className="text-sm font-medium">{c.value}</span>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-gray-400">{c.source}</span>
                    <span className="text-xs text-gray-400">{(c.confidence * 100).toFixed(0)}%</span>
                    <button
                      onClick={() => { navigator.clipboard.writeText(c.value); toast.success('Copied') }}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      <Copy className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
          {phones.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">Phone Numbers</h4>
              {phones.map((c) => (
                <div key={c.id} className="flex items-center justify-between py-2 border-b border-gray-100">
                  <span className="text-sm font-medium">{c.value}</span>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-gray-400">{c.source}</span>
                    <button
                      onClick={() => { navigator.clipboard.writeText(c.value); toast.success('Copied') }}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      <Copy className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}

function PeopleTab({ lead }: { lead: LeadDetail }) {
  return (
    <div>
      <h3 className="text-lg font-semibold mb-4">Decision Makers</h3>
      {lead.decision_makers.length === 0 ? (
        <p className="text-gray-500">No decision makers found.</p>
      ) : (
        <div className="space-y-4">
          {lead.decision_makers.map((dm) => (
            <div key={dm.id} className="rounded-lg border border-gray-200 p-4">
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-medium text-gray-900">{dm.name}</p>
                  {dm.title && <p className="text-sm text-gray-500">{dm.title}</p>}
                </div>
                <span className="rounded-full bg-gray-100 px-2.5 py-0.5 text-xs text-gray-500">
                  {(dm.confidence * 100).toFixed(0)}% confidence
                </span>
              </div>
              <div className="mt-3 flex flex-wrap gap-3">
                {dm.email && (
                  <span className="flex items-center gap-1 text-sm text-gray-600">
                    <Phone className="h-3.5 w-3.5" /> {dm.email}
                  </span>
                )}
                {dm.linkedin_url && (
                  <a href={dm.linkedin_url} target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-1 text-sm text-blue-600 hover:underline">
                    LinkedIn <ExternalLink className="h-3 w-3" />
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function PitchTab({ lead }: { lead: LeadDetail }) {
  const pitch = lead.pitch
  if (!pitch) return <p className="text-gray-500">No pitch generated yet.</p>
  return (
    <div>
      <h3 className="text-lg font-semibold mb-4">Generated Pitch</h3>

      {pitch.pitch_subject_line && (
        <div className="mb-4">
          <p className="text-sm font-medium text-gray-700 mb-1">Subject Line</p>
          <div className="flex items-center gap-2">
            <p className="text-sm bg-gray-100 rounded-lg px-3 py-2 flex-1">{pitch.pitch_subject_line}</p>
            <button
              onClick={() => { navigator.clipboard.writeText(pitch.pitch_subject_line!); toast.success('Copied') }}
              className="text-gray-400 hover:text-gray-600"
            >
              <Copy className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {pitch.pitch_text && (
        <div className="mb-6">
          <div className="flex items-center justify-between mb-1">
            <p className="text-sm font-medium text-gray-700">Pitch</p>
            <button
              onClick={() => { navigator.clipboard.writeText(pitch.pitch_text!); toast.success('Copied') }}
              className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700"
            >
              <Copy className="h-3.5 w-3.5" /> Copy
            </button>
          </div>
          <pre className="whitespace-pre-wrap bg-gray-50 rounded-lg p-4 text-sm text-gray-700 border border-gray-200 leading-relaxed">
            {pitch.pitch_text}
          </pre>
        </div>
      )}

      {pitch.gaps_identified.length > 0 && (
        <div className="mb-4">
          <p className="text-sm font-medium text-gray-700 mb-2">Gaps Identified ({pitch.gaps_identified.length})</p>
          <ul className="space-y-1">
            {pitch.gaps_identified.map((gap, i) => (
              <li key={i} className="text-sm text-gray-600 flex items-start gap-2">
                <XCircle className="h-4 w-4 text-orange-400 mt-0.5 shrink-0" />
                {gap}
              </li>
            ))}
          </ul>
        </div>
      )}

      {pitch.recommendations.length > 0 && (
        <div>
          <p className="text-sm font-medium text-gray-700 mb-2">Recommendations</p>
          <ul className="space-y-2">
            {pitch.recommendations.map((rec, i) => (
              <li key={i} className="text-sm text-gray-600 flex items-start gap-2">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-blue-100 text-xs font-medium text-blue-600">
                  {i + 1}
                </span>
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
