from nichefinder_db import SeoRepository


def record_gemini_usage(repository: SeoRepository, services) -> None:
    usage = services.gemini.get_usage_stats()
    repository.record_api_usage(
        provider="gemini",
        tokens_in=usage["prompt_tokens"],
        tokens_out=usage["response_tokens"],
    )


def validation_payload(item) -> dict:
    return {
        "source": item.source,
        "query": item.query,
        "score": item.score,
        "degraded": item.degraded,
        "unavailable": getattr(item, "unavailable", False),
        "result_count": item.result_count,
        "top_domains": item.top_domains,
        "notes": item.notes,
    }


def analysis_payload(item: dict) -> dict:
    synthesis = item["synthesis"]
    opportunity = synthesis.opportunity_score
    keyword = item["keyword"]
    serp = item["serp"]
    trend = item["trend"]
    return {
        "keyword": {
            "id": keyword.id,
            "term": keyword.term,
            "intent": keyword.search_intent.value if keyword.search_intent else None,
        },
        "opportunity": opportunity.model_dump(),
        "should_create_content": synthesis.should_create_content,
        "content_angle": synthesis.content_angle,
        "serp": serp.model_dump(),
        "trend": trend.model_dump(),
        "ads": item["ads"].model_dump(),
        "competitor": item["competitor"],
    }
