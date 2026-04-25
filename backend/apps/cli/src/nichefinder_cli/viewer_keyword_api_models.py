from __future__ import annotations

from typing import Any

from pydantic import ConfigDict

from nichefinder_cli.viewer_api_models import ApiModel, ArticleApiModel


class KeywordSummaryApiModel(ApiModel):
    id: str
    term: str
    intent: str | None
    trend: str | None
    score: float | None
    volume: int | None
    difficulty: int | None
    has_brief: bool
    priority: str | None


class KeywordsResponse(ApiModel):
    keywords: list[KeywordSummaryApiModel]


class ScoreBreakdownResponse(ApiModel):
    volume: float
    difficulty: float
    trend: float
    intent: float
    competition: float
    composite: float
    priority: str
    action: str
    why: str | None


class CompetitionAnalysisResponse(ApiModel):
    model_config = ConfigDict(extra="allow", str_strip_whitespace=True)

    rankable: bool | None = None
    competition_level: str | None = None
    dominant_content_type: str | None = None
    recommended_content_angle: str | None = None


class SerpPageResponse(ApiModel):
    position: int | None = None
    title: str | None = None
    url: str | None = None
    domain: str | None = None


class SerpResponse(ApiModel):
    fetched_at: str | None
    competition: CompetitionAnalysisResponse
    pages: list[SerpPageResponse]


class CompetitorPageResponse(ApiModel):
    title: str | None
    url: str | None
    word_count: int | None
    reading_time_min: int | None
    summary: str | None


class ContentBriefResponse(ApiModel):
    title: str | None
    content_type: str | None
    tone: str | None
    word_count_target: int | None
    secondary_keywords: list[str] | None
    suggested_h2_structure: list[str] | None
    questions_to_answer: list[str] | None


class KeywordMetadataResponse(ApiModel):
    id: str
    term: str
    seed_keyword: str | None
    source: str | None
    intent: str | None
    trend: str | None
    score: float | None
    volume: int | None
    difficulty: int | None
    discovered_at: str | None


class KeywordDetailResponse(ApiModel):
    keyword: KeywordMetadataResponse
    score_breakdown: ScoreBreakdownResponse | None
    serp: SerpResponse | None
    competitors: list[CompetitorPageResponse]
    brief: ContentBriefResponse | None
    articles: list[ArticleApiModel]


class KeywordClusterResponse(ApiModel):
    cluster_name: str
    total_cluster_volume: int
    primary_keyword_id: str
    keyword_ids: list[str]
    keyword_terms: list[str]


class KeywordClustersResponse(ApiModel):
    clusters: list[KeywordClusterResponse]
