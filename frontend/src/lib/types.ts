/** Tipos espejo de los esquemas Pydantic del backend (app/schemas). */

export type UserRole = 'FARMER' | 'OPERATOR' | 'BUYER'

export type ProductStatus =
  | 'DRAFT'
  | 'GROWING'
  | 'HARVESTED'
  | 'PROCESSING'
  | 'READY'
  | 'EXPORTED'

export type EventType =
  | 'REGISTRO_INICIAL'
  | 'SIEMBRA'
  | 'LABOR_CULTURAL'
  | 'FERTILIZACION'
  | 'CONTROL_FITOSANITARIO'
  | 'COSECHA'
  | 'POST_COSECHA'
  | 'SECADO'
  | 'CONTROL_CALIDAD'
  | 'EMPAQUE'
  | 'CERTIFICACION'
  | 'DESPACHO'

export type AgentKind =
  | 'STORYTELLING'
  | 'EXPORT_SHEET'
  | 'INSIGHTS'
  | 'ASSISTANT'
  | 'CERTIFICATION'
export type AgentStatus = 'OK' | 'FALLBACK' | 'ERROR'

export interface User {
  id: number
  email: string
  full_name: string
  role: UserRole
  created_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}

export interface Farm {
  id: number
  name: string
  owner_name: string | null
  municipality: string | null
  department: string | null
  country: string
  altitude_m: number | null
  area_ha: number | null
  description: string | null
  location: string
  latitude: number | null
  longitude: number | null
  created_at: string
  product_count: number
}

export interface FarmInput {
  name: string
  owner_name?: string | null
  municipality?: string | null
  department?: string | null
  country?: string
  altitude_m?: number | null
  area_ha?: number | null
  description?: string | null
}

export interface Product {
  id: number
  farm_id: number
  public_id: string
  name: string
  variety: string | null
  description: string | null
  status: ProductStatus
  responsable: string | null
  insumos: string | null
  post_cosecha: string | null
  planting_date: string | null
  harvest_date: string | null
  directory_listed: boolean
  created_at: string
  farm_name: string
  farm_location: string
  event_count: number
  reputation_score: number
  has_story: boolean
  passport_url: string
  published_certification_standards: CertificationStandard[]
}

export interface ProductInput {
  farm_id: number
  name: string
  variety?: string | null
  description?: string | null
  status?: ProductStatus
  responsable?: string | null
  insumos?: string | null
  post_cosecha?: string | null
  planting_date?: string | null
  harvest_date?: string | null
  directory_listed?: boolean
}

export interface EventPhoto {
  id: number
  product_id: number
  event_id: number | null
  filename: string
  content_type: string
  size_bytes: number
  sha256: string
  caption: string | null
  created_at: string
  url: string
  /** False si el archivo en disco ya no coincide con la huella sellada. */
  integrity_ok: boolean
}

export interface TraceEvent {
  id: number
  product_id: number
  sequence: number
  event_type: EventType
  payload: Record<string, unknown>
  note: string | null
  payload_hash: string
  prev_hash: string
  chain_hash: string
  recorded_by: string | null
  occurred_at: string
  photos: EventPhoto[]
}

export interface EventInput {
  event_type: EventType
  payload: Record<string, unknown>
  note?: string | null
  occurred_at?: string | null
  photo_ids?: number[]
}

export interface Verification {
  valid: boolean
  total_events: number
  broken_at_sequence: number | null
  broken_event_id: number | null
  verified_at: string
  message: string
}

export interface Passport {
  public_id: string
  product_name: string
  variety: string | null
  farm_name: string
  owner_name: string | null
  location: string
  altitude_m: number | null
  status: ProductStatus
  planting_date: string | null
  harvest_date: string | null
  story_es: string | null
  story_en: string | null
  export_title_es: string | null
  export_title_en: string | null
  export_body_es: string | null
  export_body_en: string | null
  tasting_notes: string | null
  reputation_score: number
  ai_model: string | null
  ai_generated_at: string | null
  events: TraceEvent[]
  verification: Verification
  qr_url: string
  certifications: PublicCertificationBadge[]
}

export interface PublicCertificationBadge {
  standard: CertificationStandard
  standard_name: string
  badge: string
  color: string
  verdict: CertificationVerdict
  overall_score: number
  assessed_at: string
}

export interface DirectoryEntry {
  public_id: string
  product_name: string
  variety: string | null
  farm_name: string
  location: string
  status: ProductStatus
  reputation_score: number
  has_story: boolean
  thumbnail_url: string | null
}

export interface AiStatus {
  enabled: boolean
  backend: string
  model: string
  model_pro: string
  reason: string | null
}

export interface StoryResult {
  story_es: string
  story_en: string
  tasting_notes: string
  generated_by_ai: boolean
}

export interface ExportSheetResult {
  title_es: string
  title_en: string
  body_es: string
  body_en: string
  generated_by_ai: boolean
}

export interface InsightItem {
  title: string
  detail: string
  severity: string
}

export interface InsightsResult {
  summary: string
  quality_score: number
  items: InsightItem[]
  generated_by_ai: boolean
}

export interface AssistantResult {
  answer: string
  generated_by_ai: boolean
}

export interface AgentRun {
  id: number
  product_id: number | null
  agent: AgentKind
  status: AgentStatus
  model: string | null
  latency_ms: number | null
  tokens_in: number | null
  tokens_out: number | null
  detail: string | null
  created_at: string
}

export interface TimelinePoint {
  date: string
  count: number
}

export interface EventTypeSlice {
  event_type: string
  count: number
}

export interface DashboardSummary {
  farm_count: number
  product_count: number
  event_count: number
  chains_valid: number
  chains_broken: number
  avg_reputation: number
  ai_runs: number
  ai_success_rate: number
  events_last_30_days: TimelinePoint[]
  events_by_type: EventTypeSlice[]
  recent_events: TraceEvent[]
  recent_agent_runs: AgentRun[]
}

// --- Clima --------------------------------------------------------------------

export interface WeatherDay {
  date: string
  temp_min: number | null
  temp_max: number | null
  precipitation_mm: number | null
  precipitation_probability: number | null
}

export interface WeatherAlert {
  severity: string
  title: string
  detail: string
}

export interface WeatherReport {
  farm_id: number
  farm_name: string
  location: string
  latitude: number
  longitude: number
  timezone: string
  days: WeatherDay[]
  alerts: WeatherAlert[]
}

// --- Mensajes de compradores ---------------------------------------------------

export interface InquiryInput {
  buyer_name: string
  buyer_email: string
  buyer_country?: string | null
  message: string
}

export interface Inquiry {
  id: number
  product_id: number
  buyer_name: string
  buyer_email: string
  buyer_country: string | null
  message: string
  read_at: string | null
  created_at: string
  product_name: string
}

// --- Diagnóstico de certificación -------------------------------------------

export type CertificationStandard = 'FAIRTRADE' | 'RAINFOREST_ALLIANCE'
export type CertificationVerdict = 'READY' | 'ALMOST_READY' | 'NOT_READY'

export interface CertOption {
  value: string
  label: string
}

export interface CertQuestion {
  id: string
  text: string
  critical: boolean
  options: CertOption[]
}

export interface CertSection {
  id: string
  name: string
  questions: CertQuestion[]
}

export interface CertStandardDef {
  key: CertificationStandard
  name: string
  badge: string
  color: string
  sections: CertSection[]
  total_questions: number
}

export interface SectionScore {
  id: string
  name: string
  score: number
  yes: number
  partial: number
  no: number
}

export interface CriticalGap {
  id: string
  text: string
}

export interface RoadmapStep {
  title: string
  detail: string
  priority: string
}

export interface CertificationAssessment {
  id: number
  product_id: number
  standard: CertificationStandard
  overall_score: number
  verdict: CertificationVerdict
  section_scores: SectionScore[]
  critical_gaps: CriticalGap[]
  roadmap_summary: string | null
  roadmap_steps: RoadmapStep[]
  generated_by_ai: boolean
  created_at: string
}
