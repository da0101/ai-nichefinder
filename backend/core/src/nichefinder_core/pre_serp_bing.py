from nichefinder_core.pre_serp import PreSerpCandidateScore
from nichefinder_core.pre_serp_external import ExternalEvidenceValidation, apply_external_validation


async def apply_bing_validation(
    shortlist: list[PreSerpCandidateScore],
    buyer_problems: list[object],
    bing_client,
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
        source="bing",
        ready=bool(getattr(getattr(bing_client, "settings", None), "bing_ready", False)),
        search=lambda query: bing_client.search(query, max_results=3),
        max_keywords=max_keywords,
        max_keyword_validations=max_keyword_validations,
        max_problem_validations=max_problem_validations,
        concurrency=1,
        base_weight=0.22,
    )
