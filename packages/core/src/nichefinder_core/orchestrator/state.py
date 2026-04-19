from typing import TypedDict


class PipelineState(TypedDict, total=False):
    seed_keywords: list[str]
    site_config: dict
    discovered_keyword_ids: list[str]
    keyword_analyses: dict[str, dict]
    opportunity_scores: list[dict]
    content_briefs: list[dict]
    approved_keyword_ids: list[str]
    generated_article_ids: list[str]
    current_phase: str
    serpapi_calls_used: int
    errors: list[str]
    human_checkpoint_required: bool
