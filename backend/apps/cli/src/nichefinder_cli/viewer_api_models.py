from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class JobParamsBase(ApiModel):
    profile: str | None = None


class ValidateFreeJobParams(JobParamsBase):
    keyword: str
    sources: list[str] | None = None

    @field_validator("keyword")
    @classmethod
    def _validate_keyword(cls, value: str) -> str:
        if not value:
            raise ValueError("keyword is required")
        return value


class ResearchJobParams(JobParamsBase):
    keyword: str

    @field_validator("keyword")
    @classmethod
    def _validate_keyword(cls, value: str) -> str:
        if not value:
            raise ValueError("keyword is required")
        return value


class KeywordIdJobParams(JobParamsBase):
    keyword_id: str
    force: StrictBool = False

    @field_validator("keyword_id")
    @classmethod
    def _validate_keyword_id(cls, value: str) -> str:
        if not value:
            raise ValueError("keyword_id is required")
        return value


class RewriteJobParams(JobParamsBase):
    url: str

    @field_validator("url")
    @classmethod
    def _validate_url(cls, value: str) -> str:
        if not value:
            raise ValueError("url is required")
        return value


class MonitorSyncJobParams(JobParamsBase):
    days: int = 7
    property_url: str | None = None

    @field_validator("days")
    @classmethod
    def _validate_days(cls, value: int) -> int:
        if value < 1:
            raise ValueError("days must be at least 1")
        return value


class RankCheckJobParams(JobParamsBase):
    skip_recent: StrictBool = True


class JobEnvelope(ApiModel):
    action: Literal[
        "validate-free",
        "research",
        "brief",
        "write",
        "rewrite",
        "monitor-sync",
        "rank-check",
    ]
    params: (
        ValidateFreeJobParams
        | ResearchJobParams
        | KeywordIdJobParams
        | RewriteJobParams
        | MonitorSyncJobParams
        | RankCheckJobParams
    )


class ArticleApiModel(ApiModel):
    id: str
    title: str | None
    status: str | None
    keyword_term: str | None = None
    slug: str | None = None
    word_count: int | None = None
    file_path: str | None = None
    published_url: str | None = None
    created_at: str | None = None
    approved_at: str | None = None
    published_at: str | None = None
    latest_rank_position: int | None = None
    content_preview: str | None = None


class ArticlesSummary(ApiModel):
    total_articles: int
    published_articles: int


class ArticlesResponse(ApiModel):
    articles: list[ArticleApiModel]
    summary: ArticlesSummary


class ContentPerformanceRow(ApiModel):
    content_type: str
    article_count: int


class ReportKeywordRow(ApiModel):
    id: str
    term: str
    score: float | None
    volume: int | None
    difficulty: int | None


class ReportSummary(ApiModel):
    total_keywords: int
    articles: int
    published_articles: int
    content_performance: list[ContentPerformanceRow]


class ReportResponse(ApiModel):
    top_keywords: list[ReportKeywordRow]
    summary: ReportSummary


class BudgetUsageRow(ApiModel):
    provider: str
    calls: int
    spend_usd: float
    tokens_in: int
    tokens_out: int


class BudgetResponse(ApiModel):
    usage: list[BudgetUsageRow]


class ArticleMutationDetail(ApiModel):
    id: str
    title: str
    status: str
    keyword_term: str | None = None
    approved_at: str | None = None
    published_url: str | None = None
    published_at: str | None = None


class ArticleMutationResponse(ApiModel):
    profile: str
    article: ArticleMutationDetail


class GeneratedArticleResponse(ApiModel):
    article_id: str
    file_path: str
    word_count: int
    title: str
    meta_description: str
    slug: str


class RewriteJobResponse(ApiModel):
    profile: str
    url: str
    article: GeneratedArticleResponse


class MonitorSyncResponse(ApiModel):
    profile: str
    days: int
    property_url: str
    start_date: date
    end_date: date
    total_rows: int
    inserted: int
    updated: int


class StatusResponse(ApiModel):
    active_profile: str
    environment: str
    database_url: str
    site_config_path: str
    articles_dir: str
    reports_dir: str
    cache_dir: str
    site_url: str
    primary_language: str
    gemini_configured: bool
    serpapi_configured: bool


class ReviewProfileSummary(ApiModel):
    slug: str
    site_name: str
    site_url: str
    runs: int
    approved_noise: int
    approved_validity: int
    approved_legitimacy: int


class ApprovedNoiseResponse(ApiModel):
    keyword_phrases: list[str]
    secondary_phrases: list[str]
    domains: list[str]


class ApprovedValidityResponse(ApiModel):
    keyword_phrases: list[str]
    secondary_phrases: list[str]


class ApprovedLegitimacyResponse(ApiModel):
    domains: list[str]


class ApprovedTrainingResponse(ApiModel):
    noise: ApprovedNoiseResponse
    validity: ApprovedValidityResponse
    legitimacy: ApprovedLegitimacyResponse


class ReviewCandidate(ApiModel):
    scope: Literal["domain", "keyword_phrase", "secondary_phrase"]
    label: Literal["noise", "validity", "legitimacy"]
    value: str
    support_runs: int
    support_count: int
    examples: list[str]


class NoiseReviewResponse(ApiModel):
    profile: ReviewProfileSummary
    approved: ApprovedNoiseResponse
    candidates: list[ReviewCandidate]


class TrainingReviewResponse(ApiModel):
    profile: ReviewProfileSummary
    approved: ApprovedTrainingResponse
    candidates: list[ReviewCandidate]


class FinalReviewResponse(ApiModel):
    summary: list[ReviewProfileSummary]
    shared_valid_keywords: list[str]
    shared_trusted_domains: list[str]
    profiles: list[TrainingReviewResponse]


class NoiseApprovalRequest(JobParamsBase):
    keyword_phrases: list[str] | None = None
    secondary_phrases: list[str] | None = None
    domains: list[str] | None = None
    min_runs: int = Field(default=2, ge=1)
    limit: int = Field(default=12, ge=1)


class TrainingApprovalRequest(JobParamsBase):
    noise_keyword_phrases: list[str] | None = None
    noise_secondary_phrases: list[str] | None = None
    noise_domains: list[str] | None = None
    valid_keyword_phrases: list[str] | None = None
    valid_secondary_phrases: list[str] | None = None
    trusted_domains: list[str] | None = None
    min_runs: int = Field(default=2, ge=1)
    limit: int = Field(default=18, ge=1)


class RankCheckRow(ApiModel):
    article_id: str
    article_title: str
    keyword_id: str
    keyword_term: str
    last_position: int | None
    current_position: int | None
    change: int | None
    checked_at: str


class RankCheckResponse(ApiModel):
    profile: str
    skip_recent: bool
    rows: list[RankCheckRow]
