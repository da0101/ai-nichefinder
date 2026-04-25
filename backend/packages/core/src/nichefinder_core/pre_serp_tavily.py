from nichefinder_core.pre_serp import PreSerpCandidateScore
from nichefinder_core.pre_serp_external import ExternalEvidenceValidation, apply_external_validation


async def apply_tavily_validation(
    shortlist: list[PreSerpCandidateScore],
    buyer_problems: list[object],
    tavily_client,
    *,
    max_keywords: int,
    max_keyword_validations: int,
    max_problem_validations: int,
) -> tuple[
    list[PreSerpCandidateScore],
    list[ExternalEvidenceValidation],
    list[ExternalEvidenceValidation],
]:
    return await apply_external_validation(
        shortlist,
        buyer_problems,
        source="tavily",
        ready=bool(getattr(getattr(tavily_client, "settings", None), "tavily_ready", False)),
        search=lambda query: tavily_client.search(
            query,
            max_results=3,
            search_depth="basic",
            topic="general",
        ),
        max_keywords=max_keywords,
        max_keyword_validations=max_keyword_validations,
        max_problem_validations=max_problem_validations,
        concurrency=2,
        base_weight=0.35,
    )
