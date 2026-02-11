export interface Lead {
  id: number
  domain: string
  url: string | null
  company_name: string | null
  status: 'pending' | 'analyzing' | 'completed' | 'failed'
  source: string
  created_at: string
  updated_at: string
}

export interface EcommerceData {
  is_ecommerce: boolean
  platform: string | null
  confidence_score: number
  evidence: string[]
  has_cart: boolean
  has_product_pages: boolean
  has_checkout: boolean
}

export interface MarketingToolsData {
  has_google_analytics: boolean
  ga_version: string | null
  ga_id: string | null
  has_gtm: boolean
  gtm_id: string | null
  has_gsc: boolean
  has_facebook_pixel: boolean
  fb_pixel_id: string | null
  has_tiktok_pixel: boolean
  tiktok_pixel_id: string | null
  has_hotjar: boolean
  has_clarity: boolean
  has_mixpanel: boolean
  has_segment: boolean
  has_heap: boolean
  has_amplitude: boolean
  all_detected_tools: string[]
}

export interface HostingEmailData {
  hosting_provider: string | null
  ip_address: string | null
  nameservers: string[]
  cdn_provider: string | null
  email_provider: string | null
  mx_records: string[]
  registrar: string | null
  registration_date: string | null
}

export interface AdActivityData {
  is_running_google_ads: boolean
  google_ads_count: number
  google_advertiser_id: string | null
  is_running_meta_ads: boolean
  meta_ads_count: number
  meta_page_id: string | null
  is_running_tiktok_ads: boolean
  tiktok_ads_count: number
  ad_details: Record<string, unknown>
}

export interface SocialMediaData {
  instagram_url: string | null
  facebook_url: string | null
  tiktok_url: string | null
  twitter_url: string | null
  linkedin_url: string | null
  youtube_url: string | null
  instagram_active: boolean | null
  facebook_active: boolean | null
  tiktok_active: boolean | null
  twitter_active: boolean | null
  linkedin_active: boolean | null
  activity_details: Record<string, unknown>
}

export interface DecisionMaker {
  id: number
  name: string | null
  title: string | null
  linkedin_url: string | null
  email: string | null
  source: string | null
  confidence: number
}

export interface ContactInfo {
  id: number
  type: 'email' | 'phone'
  value: string
  source: string | null
  page_url: string | null
  confidence: number
}

export interface PitchData {
  gaps_identified: string[]
  recommendations: string[]
  pitch_text: string | null
  pitch_subject_line: string | null
  generated_at: string | null
  edited: boolean
}

export interface LeadDetail extends Lead {
  ecommerce: EcommerceData | null
  marketing_tools: MarketingToolsData | null
  hosting_email: HostingEmailData | null
  ad_activity: AdActivityData | null
  social_media: SocialMediaData | null
  decision_makers: DecisionMaker[]
  contacts: ContactInfo[]
  pitch: PitchData | null
}

export interface AnalysisStatus {
  lead_id: number
  overall_status: string
  modules: Record<string, string>
  started_at: string | null
  completed_at: string | null
}

export interface DiscoveryResult {
  domain: string
  url: string
  title: string
  snippet: string
}

export interface Stats {
  total_leads: number
  analyzed: number
  pending: number
  analyzing: number
  failed: number
  ecommerce_confirmed: number
  with_gaps: number
}
