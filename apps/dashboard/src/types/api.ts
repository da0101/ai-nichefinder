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
