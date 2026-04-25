// GET /api/dashboard
export interface DashboardResponse {
  summary: {
    total_keywords: number
    briefed_keywords: number
    articles: number
    published_articles: number
  }
  keywords: KeywordSummary[]
  articles: ArticleSummary[]
  usage: UsageRow[]
  paths: { database: string; articles_dir: string }
}

export interface KeywordSummary {
  id: string
  term: string
  intent: string | null
  trend: string | null
  score: number | null
  volume: number | null
  difficulty: number | null
  has_brief: boolean
  priority: string | null
}

export interface KeywordsResponse {
  keywords: KeywordSummary[]
}

// GET /api/keywords/:id
export interface KeywordDetailResponse {
  keyword: {
    id: string
    term: string
    seed_keyword: string | null
    source: string | null
    intent: string | null
    trend: string | null
    score: number | null
    volume: number | null
    difficulty: number | null
    discovered_at: string | null
  }
  score_breakdown: ScoreBreakdown | null
  serp: {
    fetched_at: string | null
    competition: CompetitionAnalysis
    pages: SerpPage[]
  } | null
  competitors: CompetitorPage[]
  brief: ContentBrief | null
  articles: ArticleDetail[]
}

export interface KeywordClusterResponse {
  cluster_name: string
  total_cluster_volume: number
  primary_keyword_id: string
  keyword_ids: string[]
  keyword_terms: string[]
}

export interface KeywordClustersResponse {
  clusters: KeywordClusterResponse[]
}

export interface ScoreBreakdown {
  volume: number
  difficulty: number
  trend: number
  intent: number
  competition: number
  composite: number
  priority: string
  action: string
  why: string | null
}

export interface CompetitionAnalysis {
  rankable?: boolean
  competition_level?: string
  [key: string]: unknown
}

export interface SerpPage {
  position?: number
  title?: string
  url?: string
}

export interface CompetitorPage {
  title: string | null
  url: string | null
  word_count: number | null
  reading_time_min: number | null
  summary: string | null
}

export interface ContentBrief {
  title: string | null
  content_type: string | null
  tone: string | null
  word_count_target: number | null
  secondary_keywords: string[] | null
  suggested_h2_structure: string[] | null
  questions_to_answer: string[] | null
}

export interface ArticleSummary {
  id: string
  title: string | null
  status: string | null
  file_path: string | null
  published_url: string | null
  created_at: string | null
}

export interface ArticleDetail extends ArticleSummary {
  slug: string | null
  word_count: number | null
  latest_rank_position: number | null
  content_preview: string | null
}

export interface UsageRow {
  provider: string
  calls: number
  spend_usd: number
  tokens_in: number
  tokens_out: number
  usage_month: string | null
}

export interface ProfilesResponse {
  active_profile: string
  profiles: ProfileSummary[]
}

export interface SiteConfigDto {
  site_url: string
  site_name: string
  site_description: string
  target_audience: string
  services: string[]
  primary_language: string
  blog_url: string
  existing_articles: string[]
  seed_keywords: string[]
  target_persona: string
  competitors: string[]
  geographic_focus: string[]
}

export interface ProfileSummary {
  slug: string
  site_name: string
  site_url: string
  site_description: string
  is_default: boolean
  site_config: SiteConfigDto
  database_url: string
  keywords: number
  articles: number
  runs: number
  approved_noise: number
  approved_validity: number
  approved_legitimacy: number
}

export interface TrainingCandidate {
  scope: 'domain' | 'keyword_phrase' | 'secondary_phrase'
  label: 'noise' | 'validity' | 'legitimacy'
  value: string
  support_runs: number
  support_count: number
  examples: string[]
}

export interface ReviewProfileSummary {
  slug: string
  site_name: string
  site_url: string
  runs: number
  approved_noise: number
  approved_validity: number
  approved_legitimacy: number
}

export interface ApprovedNoiseResponse {
  keyword_phrases: string[]
  secondary_phrases: string[]
  domains: string[]
}

export interface ApprovedValidityResponse {
  keyword_phrases: string[]
  secondary_phrases: string[]
}

export interface ApprovedLegitimacyResponse {
  domains: string[]
}

export interface ApprovedTrainingResponse {
  noise: ApprovedNoiseResponse
  validity: ApprovedValidityResponse
  legitimacy: ApprovedLegitimacyResponse
}

export interface NoiseReviewResponse {
  profile: ReviewProfileSummary
  approved: ApprovedNoiseResponse
  candidates: TrainingCandidate[]
}

export interface TrainingReviewResponse {
  profile: ReviewProfileSummary
  approved: ApprovedTrainingResponse
  candidates: TrainingCandidate[]
}

export interface FinalReviewResponse {
  summary: ReviewProfileSummary[]
  shared_valid_keywords: string[]
  shared_trusted_domains: string[]
  profiles: TrainingReviewResponse[]
}

export interface NoiseApprovalRequest {
  profile?: string | null
  keyword_phrases?: string[]
  secondary_phrases?: string[]
  domains?: string[]
  min_runs?: number
  limit?: number
}

export interface TrainingApprovalRequest {
  profile?: string | null
  noise_keyword_phrases?: string[]
  noise_secondary_phrases?: string[]
  noise_domains?: string[]
  valid_keyword_phrases?: string[]
  valid_secondary_phrases?: string[]
  trusted_domains?: string[]
  min_runs?: number
  limit?: number
}

export interface ProfileConfigResponse {
  profile: string
  site_config: SiteConfigDto
  paths: {
    site_config_path: string
    database_url: string
  }
}

export interface ValidateFreeResponse {
  profile: string
  keyword: string
  sources: string[]
  location: string
  buyer_problems: Array<Record<string, unknown>>
  shortlist: Array<{
    term: string
    score: number
    selected: boolean
    notes: string[]
    breakdown: Record<string, number>
  }>
  keyword_validations: ValidationRow[]
  problem_validations: ValidationRow[]
  article_evidence: Array<{
    query: string
    source: string
    validation_score: number
    source_urls: string[]
    pages_scraped: number
    recurring_headings: string[]
    body_signal_terms: string[]
    question_bank: string[]
    suggested_secondary_keywords: string[]
  }>
}

export interface ValidationRow {
  source: string
  query: string
  score: number
  degraded: boolean
  unavailable: boolean
  result_count: number
  top_domains: string[]
  notes: string[]
}

export interface ArticlesResponse {
  articles: ArticleDetail[]
  summary: {
    total_articles: number
    published_articles: number
  }
}

export interface StatusDetailResponse {
  active_profile: string
  environment: string
  database_url: string
  site_config_path: string
  articles_dir: string
  reports_dir: string
  cache_dir: string
  site_url: string
  primary_language: string
  gemini_configured: boolean
  serpapi_configured: boolean
}

export interface ReportResponse {
  top_keywords: Array<{
    id: string
    term: string
    score: number | null
    volume: number | null
    difficulty: number | null
  }>
  summary: {
    total_keywords: number
    articles: number
    published_articles: number
    content_performance: Array<{
      content_type: string
      article_count: number
    }>
  }
}

export interface BudgetResponse {
  usage: BudgetUsageRow[]
}

export interface BudgetUsageRow {
  provider: string
  calls: number
  spend_usd: number
  tokens_in: number
  tokens_out: number
}

export interface ArticleMutationResponse {
  profile: string
  article: {
    id: string
    title: string
    status: string
    keyword_term: string | null
    approved_at?: string | null
    published_url?: string | null
    published_at?: string | null
  }
}

export type JobAction =
  | 'validate-free'
  | 'research'
  | 'brief'
  | 'write'
  | 'rewrite'
  | 'monitor-sync'
  | 'rank-check'

export type JobStatus = 'queued' | 'running' | 'succeeded' | 'failed'

export interface ValidateFreeJobParams {
  profile?: string
  keyword: string
  sources?: string[]
}

export interface ResearchJobParams {
  profile?: string
  keyword: string
}

export interface KeywordIdJobParams {
  profile?: string
  keyword_id: string
  force?: boolean
}

export interface RewriteJobParams {
  profile?: string
  url: string
}

export interface MonitorSyncJobParams {
  profile?: string
  days?: number
  property_url?: string
}

export interface RankCheckJobParams {
  profile?: string
  skip_recent?: boolean
}

export type JobParams =
  | ValidateFreeJobParams
  | ResearchJobParams
  | KeywordIdJobParams
  | RewriteJobParams
  | MonitorSyncJobParams
  | RankCheckJobParams

export interface JobRecordResponse {
  id: string
  action: JobAction
  status: JobStatus
  params: JobParams
  result: unknown
  error: string | null
  created_at: string
  updated_at: string
  started_at: string | null
  finished_at: string | null
}

export interface JobListResponse {
  jobs: JobRecordResponse[]
}
