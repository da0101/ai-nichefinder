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

export interface TrainingReviewResponse {
  profile: {
    slug: string
    site_name: string
    site_url: string
    runs: number
    approved_noise: number
    approved_validity: number
    approved_legitimacy: number
  }
  approved: {
    noise: {
      keyword_phrases: string[]
      secondary_phrases: string[]
      domains: string[]
    }
    validity: {
      keyword_phrases: string[]
      secondary_phrases: string[]
    }
    legitimacy: {
      domains: string[]
    }
  }
  candidates: TrainingCandidate[]
}

export interface TrainingCandidate {
  scope: 'domain' | 'keyword_phrase' | 'secondary_phrase'
  label: 'noise' | 'validity' | 'legitimacy'
  value: string
  support_runs: number
  support_count: number
  examples: string[]
}

export interface FinalReviewResponse {
  summary: Array<{
    slug: string
    runs: number
    approved_noise: number
    approved_validity: number
    approved_legitimacy: number
  }>
  shared_valid_keywords: string[]
  shared_trusted_domains: string[]
  profiles: TrainingReviewResponse[]
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
