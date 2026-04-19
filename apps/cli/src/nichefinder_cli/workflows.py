import asyncio
from contextlib import nullcontext
from datetime import datetime, timedelta, timezone

from rich.console import Console

from nichefinder_core.agents.ads_agent import AdsAgentInput
from nichefinder_core.agents.competitor_agent import CompetitorAgentInput
from nichefinder_core.agents.content_agent import ContentAgentInput
from nichefinder_core.agents.keyword_agent import KeywordAgentInput
from nichefinder_core.agents.serp_agent import SerpAgentInput
from nichefinder_core.agents.synthesis_agent import SynthesisAgentInput
from nichefinder_core.agents.trend_agent import TrendAgentInput
from nichefinder_core.models import Keyword, RankingSnapshot
from nichefinder_core.sources.scraper import ContentScraper


def _score_color(score: float) -> str:
    if score >= 70:
        return "green"
    if score >= 50:
        return "yellow"
    return "red"


async def run_full_pipeline(
    seed_keyword: str,
    site_config: dict,
    services,
    repository,
    location: str = "Montreal, Quebec, Canada",
    console: Console | None = None,
) -> dict:
    def log(msg: str) -> None:
        if console:
            console.print(msg)

    def spin(msg: str):
        return console.status(msg, spinner="dots") if console else nullcontext()

    log(f"\n[bold cyan]Research:[/bold cyan] [bold]{seed_keyword}[/bold]  [dim]({location})[/dim]")

    with spin("[dim]Step 1/3 — Expanding seed with Gemini + SerpAPI...[/dim]"):
        keyword_output = await services.keyword_agent.run(
            KeywordAgentInput(seed_keyword=seed_keyword, site_config=site_config)
        )

    log(
        f"[green]✓[/green] Expanded to [bold]{keyword_output.keywords_found}[/bold] keywords, "
        f"[bold]{keyword_output.keywords_saved}[/bold] passed filters"
    )

    if not keyword_output.keyword_ids:
        log("[yellow]⚠ No keywords passed filters — try lowering MIN_OPPORTUNITY_SCORE in .env[/yellow]")
        return {"keyword_output": keyword_output, "analyses": []}

    log(f"\n[dim]Step 2/3 — Analyzing each keyword (SERP + Trends + Competitors)...[/dim]")

    analyses = []
    total = len(keyword_output.keyword_ids)

    for i, keyword_id in enumerate(keyword_output.keyword_ids, 1):
        keyword = repository.get_keyword(keyword_id)
        if keyword is None:
            continue

        log(f"\n  [{i}/{total}] [bold]{keyword.term}[/bold]")

        with spin(f"  [{i}/{total}] Fetching SERP + Google Trends..."):
            serp_output, trend_output = await asyncio.gather(
                services.serp_agent.run(SerpAgentInput(keyword_id=keyword_id, keyword_term=keyword.term, location=location)),
                services.trend_agent.run(TrendAgentInput(keyword_id=keyword_id, keyword_term=keyword.term)),
            )

        features_str = ", ".join(serp_output.features_detected) if serp_output.features_detected else "none"
        log(
            f"         [dim]SERP:[/dim] {serp_output.pages_analyzed} pages · "
            f"difficulty {serp_output.difficulty_estimate}/100 · "
            f"competition: {serp_output.competition_level} · "
            f"features: {features_str}"
        )
        log(
            f"         [dim]Trend:[/dim] {trend_output.direction} · "
            f"avg interest {trend_output.avg_interest}/100"
        )

        if not serp_output.rankable:
            log(f"         [yellow]⚠ not rankable — skipping competitor scrape[/yellow]")

        with spin(f"  [{i}/{total}] Estimating ad signals..."):
            ads_output = await services.ads_agent.run(
                AdsAgentInput(keyword_id=keyword_id, keyword_term=keyword.term)
            )

        competitor_output = {
            "avg_word_count": 0,
            "content_gaps": [],
            "questions_covered": [],
            "recommended_word_count": 1200,
        }
        if serp_output.rankable:
            with spin(f"  [{i}/{total}] Scraping competitor pages..."):
                competitor_agent_output = await services.competitor_agent.run(
                    CompetitorAgentInput(
                        keyword_id=keyword_id,
                        serp_result_id=serp_output.serp_result_id,
                    )
                )
            competitor_output = competitor_agent_output.model_dump()
            scraped = competitor_output.get("pages_scraped", 0)
            avg_words = competitor_output.get("avg_word_count", 0)
            log(f"         [dim]Competitors:[/dim] {scraped} pages · avg {avg_words} words")

        with spin(f"  [{i}/{total}] Scoring opportunity with Gemini..."):
            synthesis_output = await services.synthesis_agent.run(
                SynthesisAgentInput(
                    keyword_id=keyword_id,
                    site_config=site_config,
                    keyword_data=keyword_output.model_dump(),
                    serp_data=serp_output.model_dump(),
                    trend_data=trend_output.model_dump(),
                    ads_data=ads_output.model_dump(),
                    competitor_data=competitor_output,
                )
            )

        score = synthesis_output.opportunity_score.composite_score
        priority = synthesis_output.opportunity_score.priority
        color = _score_color(score)
        write_flag = " [green]→ BRIEF QUEUED[/green]" if synthesis_output.should_create_content else ""
        log(
            f"         [bold {color}]Score: {score:.0f}[/bold {color}] · "
            f"priority: {priority}{write_flag}"
        )

        analyses.append(
            {
                "keyword": keyword,
                "serp": serp_output,
                "trend": trend_output,
                "ads": ads_output,
                "competitor": competitor_output,
                "synthesis": synthesis_output,
            }
        )

    analyses.sort(
        key=lambda item: item["synthesis"].opportunity_score.composite_score,
        reverse=True,
    )

    if analyses and console:
        log(f"\n[dim]Step 3/3 — Final ranking[/dim]")
        from rich.table import Table
        table = Table(title=f"Opportunity Ranking — {seed_keyword}")
        table.add_column("#", style="dim", width=3)
        table.add_column("Keyword")
        table.add_column("Score", justify="right")
        table.add_column("Difficulty", justify="right")
        table.add_column("Trend")
        table.add_column("Write?")
        for rank, item in enumerate(analyses, 1):
            opp = item["synthesis"].opportunity_score
            color = _score_color(opp.composite_score)
            table.add_row(
                str(rank),
                item["keyword"].term,
                f"[{color}]{opp.composite_score:.0f}[/{color}]",
                str(item["serp"].difficulty_estimate),
                item["trend"].direction,
                "✓" if item["synthesis"].should_create_content else "—",
            )
        console.print(table)

    return {"keyword_output": keyword_output, "analyses": analyses}


async def generate_brief(keyword_id: str, site_config: dict, services, repository):
    keyword = repository.get_keyword(keyword_id)
    if keyword is None:
        raise ValueError(f"Keyword not found: {keyword_id}")
    serp_output = await services.serp_agent.run(SerpAgentInput(keyword_id=keyword.id, keyword_term=keyword.term))
    trend_output = await services.trend_agent.run(TrendAgentInput(keyword_id=keyword.id, keyword_term=keyword.term))
    ads_output = await services.ads_agent.run(AdsAgentInput(keyword_id=keyword.id, keyword_term=keyword.term))
    competitor_output = {
        "avg_word_count": 0,
        "content_gaps": [],
        "questions_covered": [],
        "recommended_word_count": 1200,
    }
    if serp_output.rankable:
        competitor = await services.competitor_agent.run(
            CompetitorAgentInput(keyword_id=keyword.id, serp_result_id=serp_output.serp_result_id)
        )
        competitor_output = competitor.model_dump()
    return await services.synthesis_agent.run(
        SynthesisAgentInput(
            keyword_id=keyword.id,
            site_config=site_config,
            keyword_data={"keyword_id": keyword.id},
            serp_data=serp_output.model_dump(),
            trend_data=trend_output.model_dump(),
            ads_data=ads_output.model_dump(),
            competitor_data=competitor_output,
        )
    )


async def write_article(keyword_id: str, site_config: dict, services, repository):
    brief = repository.get_latest_content_brief(keyword_id)
    if brief is None:
        synthesis_output = await generate_brief(keyword_id, site_config, services, repository)
        brief = synthesis_output.content_brief
    if brief is None:
        raise ValueError("No content brief available for the keyword")
    return await services.content_agent.run(
        ContentAgentInput(content_brief=brief, site_config=site_config),
        keyword_id=keyword_id,
    )


async def rewrite_article(url: str, site_config: dict, services, repository):
    scraped = await services.scraper.fetch_article(url)
    if scraped is None:
        raise ValueError(f"Could not fetch article: {url}")
    keyword = repository.upsert_keyword(
        Keyword(term=scraped.title or url, seed_keyword=scraped.title or url, source="manual")
    )
    synthesis_output = await generate_brief(keyword.id, site_config, services, repository)
    if synthesis_output.content_brief is None:
        raise ValueError("Unable to build rewrite brief for the URL")
    brief = synthesis_output.content_brief.model_copy(
        update={
            "is_rewrite": True,
            "existing_article_url": url,
            "existing_article_content": scraped.clean_text,
        }
    )
    repository.save_content_brief(keyword.id, brief)
    return await services.content_agent.run(
        ContentAgentInput(content_brief=brief, site_config=site_config, existing_content=scraped.clean_text),
        keyword_id=keyword.id,
    )


async def check_rankings(services, repository, skip_recent: bool = True) -> list[dict]:
    rows = []
    for article in repository.get_published_articles():
        latest = repository.get_latest_ranking_snapshot(article.id)
        if skip_recent and latest and latest.checked_at >= datetime.now(timezone.utc) - timedelta(days=7):
            continue
        keyword = repository.get_keyword(article.keyword_id)
        if keyword is None or not article.published_url:
            continue
        payload = await services.serpapi.search(keyword.term)
        _, pages, _, _ = services.serpapi.parse_search_response(payload)
        position = None
        for page in pages:
            if page.url.rstrip("/") == article.published_url.rstrip("/"):
                position = page.position
                break
        snapshot = repository.create_ranking_snapshot(
            RankingSnapshot(
                article_id=article.id,
                keyword_id=keyword.id,
                position=position,
                page=((position - 1) // 10 + 1) if position else None,
            )
        )
        rows.append({"article": article, "keyword": keyword, "snapshot": snapshot, "last": latest})
    return rows
