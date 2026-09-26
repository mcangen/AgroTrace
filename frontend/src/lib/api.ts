/** Cliente HTTP tipado contra la API de AgroTrace. */

import type {
  AgentRun,
  AiStatus,
  AssistantResult,
  CertificationAssessment,
  CertificationStandard,
  CertStandardDef,
  DashboardSummary,
  DirectoryEntry,
  EventInput,
  EventPhoto,
  ExportSheetResult,
  Farm,
  FarmInput,
  Inquiry,
  InquiryInput,
  InsightsResult,
  Passport,
  Product,
  ProductInput,
  StoryResult,
  TokenResponse,
  TraceEvent,
  User,
  Verification,
  WeatherReport,
} from './types'

const BASE = '/api/v1'
const TOKEN_KEY = 'agrotrace.token'

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function setToken(token: string | null): void {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token)
    else localStorage.removeItem(TOKEN_KEY)
  } catch {
    /* modo privado o almacenamiento bloqueado: la sesion dura lo que la pestana */
  }
}

/** Se dispara cuando el backend rechaza el token, para que la app cierre sesion. */
export const onUnauthorized = { handler: null as null | (() => void) }

async function request<T>(
  path: string,
  options: RequestInit & { auth?: boolean } = {},
): Promise<T> {
  const { auth = true, headers, ...rest } = options

  const finalHeaders = new Headers(headers)
  // Con FormData no se fija Content-Type a mano: el navegador tiene que
  // ponerlo él para incluir el boundary del multipart.
  const isFormData = typeof FormData !== 'undefined' && rest.body instanceof FormData
  if (rest.body && !isFormData && !finalHeaders.has('Content-Type')) {
    finalHeaders.set('Content-Type', 'application/json')
  }
  if (auth) {
    const token = getToken()
    if (token) finalHeaders.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(`${BASE}${path}`, { ...rest, headers: finalHeaders })

  if (response.status === 401 && auth) {
    setToken(null)
    onUnauthorized.handler?.()
  }

  if (!response.ok) {
    throw new ApiError(response.status, await readError(response))
  }

  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

async function readError(response: Response): Promise<string> {
  try {
    const data = await response.json()
    const detail = (data as { detail?: unknown }).detail
    if (typeof detail === 'string') return detail
    // Errores de validación de FastAPI: [{loc, msg, type}, ...]
    if (Array.isArray(detail)) {
      const first = detail[0] as { loc?: unknown[]; msg?: string } | undefined
      if (first?.msg) {
        const field = Array.isArray(first.loc) ? first.loc[first.loc.length - 1] : null
        return field ? `${String(field)}: ${first.msg}` : first.msg
      }
    }
  } catch {
    /* la respuesta no era JSON */
  }
  return `Error ${response.status}. Verifica que el backend esté corriendo.`
}

const body = (data: unknown) => JSON.stringify(data)

export const api = {
  // --- auth ---
  register: (data: { email: string; password: string; full_name: string }) =>
    request<TokenResponse>('/auth/register', {
      method: 'POST',
      body: body(data),
      auth: false,
    }),

  login: (data: { email: string; password: string }) =>
    request<TokenResponse>('/auth/login', {
      method: 'POST',
      body: body(data),
      auth: false,
    }),

  me: () => request<User>('/auth/me'),

  forgotPassword: (email: string) =>
    request<{ message: string }>('/auth/forgot-password', {
      method: 'POST',
      body: body({ email }),
      auth: false,
    }),
  resetPassword: (token: string, newPassword: string) =>
    request<TokenResponse>('/auth/reset-password', {
      method: 'POST',
      body: body({ token, new_password: newPassword }),
      auth: false,
    }),

  // --- fincas ---
  listFarms: () => request<Farm[]>('/farms'),
  createFarm: (data: FarmInput) =>
    request<Farm>('/farms', { method: 'POST', body: body(data) }),
  updateFarm: (id: number, data: Partial<FarmInput>) =>
    request<Farm>(`/farms/${id}`, { method: 'PATCH', body: body(data) }),
  deleteFarm: (id: number) => request<void>(`/farms/${id}`, { method: 'DELETE' }),

  // --- productos ---
  listProducts: (farmId?: number) =>
    request<Product[]>(`/products${farmId ? `?farm_id=${farmId}` : ''}`),
  getProduct: (id: number) => request<Product>(`/products/${id}`),
  createProduct: (data: ProductInput) =>
    request<Product>('/products', { method: 'POST', body: body(data) }),
  updateProduct: (id: number, data: Partial<ProductInput>) =>
    request<Product>(`/products/${id}`, { method: 'PATCH', body: body(data) }),
  deleteProduct: (id: number) => request<void>(`/products/${id}`, { method: 'DELETE' }),

  // --- trazabilidad ---
  listEvents: (productId: number) => request<TraceEvent[]>(`/products/${productId}/events`),
  createEvent: (productId: number, data: EventInput) =>
    request<TraceEvent>(`/products/${productId}/events`, {
      method: 'POST',
      body: body(data),
    }),
  verifyChain: (productId: number) =>
    request<Verification>(`/products/${productId}/verify`),

  // --- fotos de evidencia ---
  uploadPhoto: (productId: number, file: File, caption?: string) => {
    const form = new FormData()
    form.append('file', file)
    if (caption) form.append('caption', caption)
    return request<EventPhoto>(`/products/${productId}/photos`, {
      method: 'POST',
      body: form,
    })
  },
  deletePhoto: (productId: number, photoId: number) =>
    request<void>(`/products/${productId}/photos/${photoId}`, { method: 'DELETE' }),

  // --- clima ---
  farmWeather: (farmId: number) => request<WeatherReport>(`/farms/${farmId}/clima`),

  // --- mensajes de compradores ---
  listInquiries: (unreadOnly = false) =>
    request<Inquiry[]>(`/inquiries${unreadOnly ? '?unread_only=true' : ''}`),
  unreadInquiryCount: () => request<number>('/inquiries/unread-count'),
  markInquiryRead: (inquiryId: number) =>
    request<Inquiry>(`/inquiries/${inquiryId}/read`, { method: 'POST' }),
  deleteInquiry: (inquiryId: number) =>
    request<void>(`/inquiries/${inquiryId}`, { method: 'DELETE' }),
  sendInquiry: (publicId: string, data: InquiryInput) =>
    request<{ message: string }>(`/public/passport/${publicId}/contacto`, {
      method: 'POST',
      body: body(data),
      auth: false,
    }),

  // --- dashboard ---
  dashboard: () => request<DashboardSummary>('/dashboard/summary'),

  // --- IA ---
  aiStatus: () => request<AiStatus>('/ai/status', { auth: false }),
  generateStory: (productId: number) =>
    request<StoryResult>(`/ai/products/${productId}/story`, { method: 'POST' }),
  generateExportSheet: (productId: number) =>
    request<ExportSheetResult>(`/ai/products/${productId}/export-sheet`, {
      method: 'POST',
    }),
  generateInsights: (productId: number) =>
    request<InsightsResult>(`/ai/products/${productId}/insights`, { method: 'POST' }),
  askAssistant: (question: string, productId?: number) =>
    request<AssistantResult>('/ai/assistant', {
      method: 'POST',
      body: body({ question, product_id: productId ?? null }),
    }),
  agentRuns: () => request<AgentRun[]>('/ai/runs'),

  // --- certificación ---
  listCertStandards: () => request<CertStandardDef[]>('/certification/standards'),
  submitCertAssessment: (
    productId: number,
    standard: CertificationStandard,
    answers: Record<string, string>,
  ) =>
    request<CertificationAssessment>(`/products/${productId}/certification/assessments`, {
      method: 'POST',
      body: body({ standard, answers }),
    }),
  listCertAssessments: (productId: number, standard?: CertificationStandard) =>
    request<CertificationAssessment[]>(
      `/products/${productId}/certification/assessments${standard ? `?standard=${standard}` : ''}`,
    ),
  latestCertAssessment: (productId: number, standard: CertificationStandard) =>
    request<CertificationAssessment | null>(
      `/products/${productId}/certification/assessments/latest?standard=${standard}`,
    ),
  publishCertification: (productId: number, standard: CertificationStandard, published: boolean) =>
    request<CertificationStandard[]>(`/products/${productId}/certification/publish`, {
      method: 'POST',
      body: body({ standard, published }),
    }),

  // --- publico ---
  passport: (publicId: string) =>
    request<Passport>(`/public/passport/${publicId}`, { auth: false }),
  directory: () => request<DirectoryEntry[]>('/public/directory', { auth: false }),
}

export const passportQrSrc = (publicId: string) =>
  `${BASE}/public/passport/${publicId}/qr.png`

/** Descarga el reporte PDF de un lote.
 *
 * No se puede usar un `<a href>` directo porque el endpoint exige el token de
 * sesión: hay que pedirlo con fetch y entregar el blob al navegador.
 */
export async function downloadProductReport(
  productId: number,
  suggestedName: string,
): Promise<void> {
  const token = getToken()
  const response = await fetch(`${BASE}/products/${productId}/reporte.pdf`, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  })

  if (!response.ok) {
    throw new ApiError(response.status, await readError(response))
  }

  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = suggestedName
  document.body.appendChild(link)
  link.click()
  link.remove()
  // Liberar el objeto en el siguiente tick: revocarlo de inmediato cancela
  // la descarga en algunos navegadores.
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
