import asyncio

from langgraph.graph import END, START, StateGraph

from nichefinder_core.agents.ads_agent import AdsAgentInput
from nichefinder_core.agents.competitor_agent import CompetitorAgentInput
from nichefinder_core.agents.content_agent import ContentAgentInput
from nichefinder_core.agents.keyword_agent import KeywordAgentInput
from nichefinder_core.agents.serp_agent import SerpAgentInput
from nichefinder_core.agents.synthesis_agent import SynthesisAgentInput
from nichefinder_core.agents.trend_agent import TrendAgentInput
from nichefinder_core.orchestrator.state import PipelineState


def build_graph(services: dict):
    graph = StateGraph(PipelineState)

    async def keyword_node(state: PipelineState):
        outputs = await asyncio.gather(
            *[
                services["keyword_agent"].run(
                    KeywordAgentInput(seed_keyword=seed, site_config=state["site_config"])
                )
                for seed in state["seed_keywords"]
            ]
        )
        discovered_keyword_ids = [keyword_id for output in outputs for keyword_id in output.keyword_ids]
        return {
            "discovered_keyword_ids": discovered_keyword_ids,
            "current_phase": "keywords",
            "keyword_analyses": {},
        }

    async def parallel_analysis_node(state: PipelineState):
        semaphore = asyncio.Semaphore(3)

        async def analyze(keyword_id: str):
            async with semaphore:
                keyword = services["repository"].get_keyword(keyword_id)
                serp_output, trend_output = await asyncio.gather(
                    services["serp_agent"].run(
                        SerpAgentInput(keyword_id=keyword.id, keyword_term=keyword.term)
                    ),
                    services["trend_agent"].run(
                        TrendAgentInput(keyword_id=keyword.id, keyword_term=keyword.term)
                    ),
                )
                ads_output = await services["ads_agent"].run(
                    AdsAgentInput(keyword_id=keyword.id, keyword_term=keyword.term)
                )
                return keyword_id, {
                    "serp": serp_output.model_dump(),
                    "trend": trend_output.model_dump(),
                    "ads": ads_output.model_dump(),
                }

        results = await asyncio.gather(*[analyze(keyword_id) for keyword_id in state["discovered_keyword_ids"]])
        analyses = dict(results)
        return {"keyword_analyses": analyses, "current_phase": "parallel_analysis"}

    async def competitor_node(state: PipelineState):
        analyses = state["keyword_analyses"]
        for keyword_id, analysis in list(analyses.items()):
            if not analysis["serp"]["rankable"]:
                continue
            output = await services["competitor_agent"].run(
                CompetitorAgentInput(
                    keyword_id=keyword_id,
                    serp_result_id=analysis["serp"]["serp_result_id"],
                )
            )
            analyses[keyword_id]["competitor"] = output.model_dump()
        return {"keyword_analyses": analyses, "current_phase": "competitors"}

    async def synthesis_node(state: PipelineState):
        opportunity_scores = []
        content_briefs = []
        analyses = state["keyword_analyses"]
        for keyword_id, analysis in analyses.items():
            if "competitor" not in analysis:
                analysis["competitor"] = {
                    "avg_word_count": 0,
                    "content_gaps": [],
                    "questions_covered": [],
                    "recommended_word_count": 1200,
                }
            output = await services["synthesis_agent"].run(
                SynthesisAgentInput(
                    keyword_id=keyword_id,
                    site_config=state["site_config"],
                    keyword_data={"keyword_id": keyword_id},
                    serp_data=analysis["serp"],
                    trend_data=analysis["trend"],
                    ads_data=analysis["ads"],
                    competitor_data=analysis["competitor"],
                )
            )
            analyses[keyword_id]["synthesis"] = output.model_dump(mode="json")
            opportunity_scores.append(output.opportunity_score.model_dump())
            if output.content_brief:
                content_briefs.append(output.content_brief.model_dump(mode="json"))
        opportunity_scores.sort(key=lambda item: item["composite_score"], reverse=True)
        return {
            "keyword_analyses": analyses,
            "opportunity_scores": opportunity_scores,
            "content_briefs": content_briefs,
            "current_phase": "synthesis",
            "human_checkpoint_required": True,
        }

    def human_review_node(state: PipelineState):
        return {"current_phase": "human_review", "human_checkpoint_required": True}

    async def content_node(state: PipelineState):
        generated_article_ids = []
        for keyword_id in state.get("approved_keyword_ids", []):
            brief = services["repository"].get_latest_content_brief(keyword_id)
            if brief is None:
                continue
            output = await services["content_agent"].run(
                ContentAgentInput(content_brief=brief, site_config=state["site_config"]),
                keyword_id=keyword_id,
            )
            generated_article_ids.append(output.article_id)
        return {
            "generated_article_ids": generated_article_ids,
            "current_phase": "content",
            "human_checkpoint_required": True,
        }

    def human_content_review_node(state: PipelineState):
        return {"current_phase": "human_content_review", "human_checkpoint_required": True}

    def should_continue_after_synthesis(state: PipelineState):
        return "human_review" if state.get("content_briefs") else END

    def should_continue_after_human_review(state: PipelineState):
        return "content" if state.get("approved_keyword_ids") else END

    graph.add_node("keyword", keyword_node)
    graph.add_node("parallel_analysis", parallel_analysis_node)
    graph.add_node("competitor", competitor_node)
    graph.add_node("synthesis", synthesis_node)
    graph.add_node("human_review", human_review_node)
    graph.add_node("content", content_node)
    graph.add_node("human_content_review", human_content_review_node)

    graph.add_edge(START, "keyword")
    graph.add_edge("keyword", "parallel_analysis")
    graph.add_edge("parallel_analysis", "competitor")
    graph.add_edge("competitor", "synthesis")
    graph.add_conditional_edges("synthesis", should_continue_after_synthesis)
    graph.add_conditional_edges("human_review", should_continue_after_human_review)
    graph.add_edge("content", "human_content_review")
    graph.add_edge("human_content_review", END)

    return graph.compile()
