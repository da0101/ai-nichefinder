from contextlib import nullcontext

from rich.console import Console

from nichefinder_cli.research_output import (
    normalize_external_validation_output,
    print_article_evidence,
    print_buyer_problems,
    print_cross_source_patterns,
    print_keyword_validations,
    print_pre_serp_shortlist,
    print_problem_validations,
)
from nichefinder_core.agents.keyword_agent import KeywordAgentInput
from nichefinder_core.free_article_evidence import collect_free_article_evidence
from nichefinder_core.free_validation_context import (
    load_free_validation_context,
    save_free_validation_context,
    thaw_shortlist,
)
from nichefinder_core.models import BuyerProblem
from nichefinder_core.pre_serp_bing import apply_bing_validation
from nichefinder_core.pre_serp_ddgs import apply_ddgs_validation
from nichefinder_core.pre_serp_trends import build_trend_assisted_shortlist
from nichefinder_core.pre_serp_yahoo import apply_yahoo_validation
from nichefinder_core.research_overlap import apply_overlap_confidence, summarize_cross_source_patterns


async def run_free_validation_pipeline(
    seed_keyword: str,
    site_config: dict,
    services,
    repository,
    *,
    location: str = "Montreal, Quebec, Canada",
    sources: tuple[str, ...] = ("ddgs", "bing", "yahoo"),
    console: Console | None = None,
) -> dict:
    def log(message: str) -> None:
        if console:
            console.print(message)

    def spin(message: str):
        return console.status(message, spinner="dots") if console else nullcontext()

    log(
        f"\n[bold cyan]Free Validation:[/bold cyan] [bold]{seed_keyword}[/bold] "
        f"[dim]({location})[/dim]"
    )
    log(f"[dim]Sources:[/dim] {', '.join(source.upper() for source in sources)}")
    log("[dim]Paid validation skipped:[/dim] Tavily, SerpAPI")
    active_sources = {source.lower() for source in sources}
    frozen_context = None
    if len(active_sources) == 1:
        frozen_context = load_free_validation_context(
            services.settings,
            seed_keyword=seed_keyword,
            location=location,
            site_config=site_config,
        )

    if frozen_context is not None:
        keyword_output = None
        buyer_problems = [problem.model_dump() for problem in frozen_context.buyer_problems]
        shortlist = thaw_shortlist(frozen_context)
        log("[dim]Using frozen free-validation context from local cache[/dim]")
    else:
        with spin("[dim]Step 1/3 — Discovering buyer problems and expanding with Gemini...[/dim]"):
            keyword_output = await services.keyword_agent.run(
                KeywordAgentInput(seed_keyword=seed_keyword, site_config=site_config)
            )
        buyer_problems = [problem.model_dump() for problem in keyword_output.buyer_problems]

        log(
            f"[green]✓[/green] Expanded to [bold]{keyword_output.keywords_found}[/bold] keywords, "
            f"[bold]{keyword_output.keywords_saved}[/bold] passed filters"
        )

        if not keyword_output.keyword_ids:
            log("[yellow]⚠ No keywords passed filters — try lowering MIN_OPPORTUNITY_SCORE in .env[/yellow]")
            return {
                "keyword_output": keyword_output,
                "shortlist": [],
                "keyword_validations": [],
                "problem_validations": [],
                "article_evidence": [],
            }

        with spin("[dim]Step 2/3 — Enriching top candidates with Google Trends...[/dim]"):
            shortlist = await build_trend_assisted_shortlist(
                keyword_output.keyword_ids,
                repository,
                services.trend_agent,
                site_config=site_config,
                location=location,
                max_keywords=services.settings.max_serp_keywords,
            )
        save_free_validation_context(
            services.settings,
            seed_keyword=seed_keyword,
            location=location,
            site_config=site_config,
            keywords_found=keyword_output.keywords_found,
            keywords_saved=keyword_output.keywords_saved,
            buyer_problems=[BuyerProblem.model_validate(item) for item in buyer_problems],
            shortlist=shortlist,
        )
    if console:
        print_buyer_problems(console, buyer_problems)

    keyword_validations = []
    problem_validations = []
    article_evidence = []

    async def run_bucket(
        *,
        label: str,
        apply_validation,
        client,
        max_keyword_validations: int,
        max_problem_validations: int,
    ) -> None:
        nonlocal shortlist, keyword_validations, problem_validations, article_evidence
        with spin(f"[dim]Step 3/4 — Cross-checking shortlist and buyer problems with {label}...[/dim]"):
            shortlist, bucket_keyword_validations, bucket_problem_validations = normalize_external_validation_output(
                await apply_validation(
                    shortlist,
                    buyer_problems,
                    client,
                    max_keywords=services.settings.max_serp_keywords,
                    max_keyword_validations=max_keyword_validations,
                    max_problem_validations=max_problem_validations,
                )
            )
        keyword_validations.extend(bucket_keyword_validations)
        problem_validations.extend(bucket_problem_validations)
        if not bucket_keyword_validations and not bucket_problem_validations:
            return
        with spin(f"[dim]Step 4/4 — Scraping {label}-backed articles for keyword-bank evidence...[/dim]"):
            article_evidence.extend(
                await collect_free_article_evidence(
                    bucket_keyword_validations,
                    services.scraper,
                    max_keywords=services.settings.max_free_article_keywords,
                    max_pages_per_keyword=services.settings.max_free_article_pages_per_keyword,
                )
            )
            article_evidence.extend(
                await collect_free_article_evidence(
                    bucket_problem_validations,
                    services.scraper,
                    max_keywords=services.settings.max_free_problem_article_queries,
                    max_pages_per_keyword=services.settings.max_free_problem_pages_per_query,
                )
            )

    if "ddgs" in active_sources and services.settings.ddgs_ready:
        await run_bucket(
            label="DDGS",
            apply_validation=apply_ddgs_validation,
            client=services.ddgs,
            max_keyword_validations=services.settings.max_ddgs_keyword_validations,
            max_problem_validations=services.settings.max_ddgs_problem_validations,
        )
    if "bing" in active_sources and services.settings.bing_ready:
        await run_bucket(
            label="Bing",
            apply_validation=apply_bing_validation,
            client=services.bing,
            max_keyword_validations=services.settings.max_bing_keyword_validations,
            max_problem_validations=services.settings.max_bing_problem_validations,
        )
    if "yahoo" in active_sources and services.settings.yahoo_ready:
        await run_bucket(
            label="Yahoo",
            apply_validation=apply_yahoo_validation,
            client=services.yahoo,
            max_keyword_validations=services.settings.max_yahoo_keyword_validations,
            max_problem_validations=services.settings.max_yahoo_problem_validations,
        )

    keyword_patterns = []
    family_keyword_patterns = []
    problem_patterns = []
    family_problem_patterns = []
    if len(active_sources) > 1:
        keyword_patterns = summarize_cross_source_patterns(keyword_validations, article_evidence)
        family_keyword_patterns = summarize_cross_source_patterns(
            keyword_validations,
            article_evidence,
            grouping="family",
        )
        shortlist = apply_overlap_confidence(shortlist, keyword_patterns, family_keyword_patterns)
        problem_patterns = summarize_cross_source_patterns(problem_validations)
        family_problem_patterns = summarize_cross_source_patterns(problem_validations, grouping="family")

    if console and shortlist:
        print_pre_serp_shortlist(console, shortlist, services.settings.max_serp_keywords)
    if console and keyword_validations:
        print_keyword_validations(console, keyword_validations)
    if console and problem_validations:
        print_problem_validations(console, problem_validations)
    if console and article_evidence:
        print_article_evidence(console, article_evidence)
    if console and len(active_sources) > 1:
        if keyword_patterns:
            print_cross_source_patterns(
                console,
                keyword_patterns,
                title="Cross-Engine Keyword Patterns",
                include_research_bank=True,
            )
        if family_keyword_patterns:
            print_cross_source_patterns(
                console,
                family_keyword_patterns,
                title="Topic-Family Keyword Patterns",
                include_research_bank=True,
            )
        if problem_patterns:
            print_cross_source_patterns(
                console,
                problem_patterns,
                title="Cross-Engine Buyer Problem Patterns",
                include_research_bank=False,
            )
        if family_problem_patterns:
            print_cross_source_patterns(
                console,
                family_problem_patterns,
                title="Topic-Family Buyer Problem Patterns",
                include_research_bank=False,
            )
    log("[dim]Score cheat sheet:[/dim] docs/scoring-cheatsheet.md")

    return {
        "keyword_output": keyword_output or frozen_context,
        "shortlist": shortlist,
        "keyword_validations": keyword_validations,
        "problem_validations": problem_validations,
        "article_evidence": article_evidence,
    }
