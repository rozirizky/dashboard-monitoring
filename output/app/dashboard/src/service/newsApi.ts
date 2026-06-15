// src/services/newsApi.ts
const BASE_URL = 'http://localhost:8000'

// ─── Shared ───────────────────────────────────────────────────────────────────
export interface ArticleTag {
  id: number
  article_id: number
  tag: string
}

export interface ArticleSource {
  id: number
  name?: string           // list endpoint
  source?: string         // detail endpoint
  baseurl?: string
  category?: string
  country?: string
  language?: string
  priority?: number
  status?: boolean
  kafka_topic?: string
  created_at?: string
  updated_at?: string
}

// ─── List endpoint shape (/articles, /articles/category, /articles/sentiment) ─
export interface ArticleAnalysis {
  sentiment: 'positive' | 'negative' | 'neutral'
  confidence: number
  summary: string
}

export interface Article {
  id: number
  title: string
  url: string
  category: string
  country: string
  published_date: string
  source: ArticleSource
  analysis?: ArticleAnalysis
  tags: string[] | ArticleTag[]   // list = string[], detail = ArticleTag[]
}

// ─── Detail endpoint shape (/articles/{id}) ───────────────────────────────────
export interface ArticleDetail {
  id: number
  title: string
  url: string
  content: string
  category: string
  country: string
  published_date: string
  created_at: string
  author: string | null
  language: string
  topic: string
  source_id: number
  source: ArticleSource
  nlp_result?: {
    id: number
    article_id: number
    sentiment_label: 'positive' | 'negative' | 'neutral'
    confidence_score: number
    summary: string
  }
  tags: ArticleTag[]
  storage_ref?: {
    id: number
    article_id: number
    bucket: string
    object_name: string
  }
}

// ─── Response wrappers ────────────────────────────────────────────────────────
interface ListResponse  { success: boolean; count?: number; data: Article[] }
interface DetailResponse { success: boolean; data: ArticleDetail }

// ─── Helpers ──────────────────────────────────────────────────────────────────
async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`)
  if (!res.ok) throw new Error(`API error ${res.status}: ${res.statusText}`)
  return res.json()
}

// ─── API ──────────────────────────────────────────────────────────────────────
export const newsApi = {
  getAll:         ()             => get<ListResponse>('/articles').then(r => r.data),
  getById:        (id: number)   => get<DetailResponse>(`/articles/${id}`).then(r => r.data),
  getByCategory:  (cat: string)  => get<ListResponse>(`/articles/category/${cat}`).then(r => r.data),
  getBySentiment: (s: string)    => get<ListResponse>(`/articles/sentiment/${s}`).then(r => r.data),
}

// ─── Utils ────────────────────────────────────────────────────────────────────

/** Normalise tags: kedua endpoint ke string[] */
export function normalizeTags(tags: string[] | ArticleTag[]): string[] {
  if (!tags?.length) return []
  return typeof tags[0] === 'string'
    ? (tags as string[])
    : (tags as ArticleTag[]).map(t => t.tag)
}

/** Ambil sentiment dari Article (list) atau ArticleDetail (detail) */
export function getSentiment(item: Article | ArticleDetail): 'positive' | 'negative' | 'neutral' {
  if ('analysis' in item && item.analysis) return item.analysis.sentiment
  if ('nlp_result' in item && item.nlp_result) return item.nlp_result.sentiment_label
  return 'neutral'
}

/** Ambil confidence dari Article atau ArticleDetail */
export function getConfidence(item: Article | ArticleDetail): number {
  if ('analysis' in item && item.analysis) return item.analysis.confidence
  if ('nlp_result' in item && item.nlp_result) return item.nlp_result.confidence_score
  return 0
}

/** Ambil summary dari Article atau ArticleDetail */
export function getSummary(item: Article | ArticleDetail): string {
  if ('analysis' in item && item.analysis) return item.analysis.summary
  if ('nlp_result' in item && item.nlp_result) return item.nlp_result.summary
  return ''
}

/** Ambil source name dari ArticleSource */
export function getSourceName(source: ArticleSource): string {
  return source?.name ?? source?.source ?? '—'
}