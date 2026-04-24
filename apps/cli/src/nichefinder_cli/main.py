import asyncio
from datetime import datetime, timezone

from nichefinder_cli.commands.articles import articles_app
from nichefinder_cli.commands.db import db_app
from nichefinder_cli.commands.keywords import keywords_app
from nichefinder_cli.commands.monitor import monitor_app
from nichefinder_cli.commands.ranks import ranks_app
from nichefinder_cli.commands.status import status
from nichefinder_cli.commands.viewer import view
from nichefinder_cli.free_validation import run_free_validation_pipeline
from nichefinder_cli.runtime import (
    build_services,
    create_profile,
    delete_profile,
    get_active_profile,
    get_runtime,
    list_profiles,
    resolve_runtime_settings,
    save_profile_site_config,
    set_active_profile,
)
from nichefinder_cli.workflows import generate_brief, rewrite_article, run_full_pipeline, write_article
from nichefinder_core.agents.serp_agent import SerpAgentInput
from nichefinder_core.models import Keyword
from nichefinder_core.models.site import SiteConfig
from nichefinder_core.noise_memory import (
    approve_noise_entries,
    approve_training_entries,
    learning_memory_stats,
    load_noise_profile,
    summarize_noise_candidates,
    summarize_training_candidates,
)
from nichefinder_db import SeoRepository, create_db_and_tables
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table
from typer import Argument, Option, Typer
from typing import Annotated

app = Typer(
    add_completion=False,
    no_args_is_help=True,
    help="CLI-first personal SEO intelligence for danilulmashev.com.",
)

app.command()(status)
app.command()(view)
app.add_typer(db_app, name="db")
app.add_typer(keywords_app, name="keywords")
app.add_typer(articles_app, name="articles")
app.add_typer(ranks_app, name="rank")
app.add_typer(monitor_app, name="monitor")


def _console() -> Console:
    return Console()


def _record_gemini_usage(repository: SeoRepository, services) -> None:
    usage = services.gemini.get_usage_stats()
    repository.record_api_usage(
        provider="gemini",
        tokens_in=usage["prompt_tokens"],
        tokens_out=usage["response_tokens"],
    )


def _print_serpapi_usage(repository: SeoRepository, settings) -> None:
    usage = repository.get_api_usage("serpapi")
    used = usage.call_count if usage else 0
    limit = settings.serpapi_calls_per_month
    remaining = max(0, limit - used)
    color = "green" if remaining > 30 else "yellow" if remaining > 10 else "red"
    _console().print(
        f"\n[dim]SerpAPI this month:[/dim] [{color}]{used}/{limit} searches used · {remaining} remaining[/{color}]"
    )


def _print_tavily_usage(repository: SeoRepository, settings) -> None:
    usage = repository.get_api_usage("tavily")
    used = usage.call_count if usage else 0
    limit = settings.tavily_credits_per_month
    remaining = max(0, limit - used)
    color = "green" if remaining > 500 else "yellow" if remaining > 200 else "red"
    _console().print(
        f"[dim]Tavily this month:[/dim] [{color}]{used}/{limit} credits used · {remaining} remaining[/{color}]"
    )


def _print_ddgs_usage(repository: SeoRepository, settings) -> None:
    usage = repository.get_api_usage("ddgs")
    used = usage.call_count if usage else 0
    limit = settings.ddgs_calls_per_month
    remaining = max(0, limit - used)
    color = "green" if remaining > 150 else "yellow" if remaining > 50 else "red"
    _console().print(
        f"[dim]DDGS this month:[/dim] [{color}]{used}/{limit} validations used · {remaining} remaining[/{color}]"
    )


def _print_bing_usage(repository: SeoRepository, settings) -> None:
    usage = repository.get_api_usage("bing")
    used = usage.call_count if usage else 0
    limit = settings.bing_calls_per_month
    remaining = max(0, limit - used)
    color = "green" if remaining > 150 else "yellow" if remaining > 50 else "red"
    _console().print(
        f"[dim]Bing this month:[/dim] [{color}]{used}/{limit} validations used · {remaining} remaining[/{color}]"
    )


def _print_yahoo_usage(repository: SeoRepository, settings) -> None:
    usage = repository.get_api_usage("yahoo")
    used = usage.call_count if usage else 0
    limit = settings.yahoo_calls_per_month
    remaining = max(0, limit - used)
    color = "green" if remaining > 150 else "yellow" if remaining > 50 else "red"
    _console().print(
        f"[dim]Yahoo this month:[/dim] [{color}]{used}/{limit} validations used · {remaining} remaining[/{color}]"
    )


def _print_usage_for_sources(repository: SeoRepository, settings, sources: tuple[str, ...]) -> None:
    printers = {
        "ddgs": _print_ddgs_usage,
        "bing": _print_bing_usage,
        "yahoo": _print_yahoo_usage,
    }
    for source in sources:
        printer = printers.get(source)
        if printer is not None:
            printer(repository, settings)


def _run_free_validation_command(keyword: str, *, sources: tuple[str, ...]) -> None:
    settings, site_config, session_context = get_runtime()
    with session_context as session:
        repository = SeoRepository(session)
        services = build_services(settings, repository)
        asyncio.run(
            run_free_validation_pipeline(
                keyword,
                site_config.model_dump(),
                services,
                repository,
                location=settings.search_location,
                sources=sources,
                console=_console(),
            )
        )
        _record_gemini_usage(repository, services)
        _print_usage_for_sources(repository, settings, sources)
        asyncio.run(services.scraper.close())


def _print_training_candidates(site_config: dict, settings, *, min_runs: int, limit: int, label: str | None = None) -> None:
    candidates = summarize_training_candidates(
        settings,
        site_config=site_config,
        min_runs=min_runs,
        limit=limit,
        label=label,
    )
    profile = load_noise_profile(settings, site_config=site_config)
    _console().print(
        f"[dim]Approved training memory:[/dim] "
        f"noise={len(profile.keyword_phrases) + len(profile.secondary_phrases) + len(profile.domains)}, "
        f"validity={len(profile.valid_keyword_phrases) + len(profile.valid_secondary_phrases)}, "
        f"legitimacy={len(profile.trusted_domains)}"
    )
    if not candidates:
        _console().print("[yellow]No repeated training candidates yet.[/yellow]")
        _console().print("[dim]Run 3-5 validate-free probes first, then review again.[/dim]")
        return
    for candidate_label in ("validity", "legitimacy", "noise"):
        scoped_label = [item for item in candidates if item.label == candidate_label]
        if not scoped_label:
            continue
        for scope in ("keyword_phrase", "secondary_phrase", "domain"):
            scoped = [item for item in scoped_label if item.scope == scope]
            if not scoped:
                continue
            table = Table(title=f"{candidate_label.title()} · {scope.replace('_', ' ').title()}")
            table.add_column("Candidate")
            table.add_column("Runs", justify="right")
            table.add_column("Hits", justify="right")
            table.add_column("Examples")
            for item in scoped:
                table.add_row(item.value, str(item.support_runs), str(item.support_count), "; ".join(item.examples))
            _console().print(table)
    _console().print(
        "[dim]Approve examples:[/dim] "
        "`uv run seo approve-training --valid-keyword-phrase \"food cost percentage\"` "
        "`--trusted-domain \"restaurant.org\"` "
        "`--noise-keyword-phrase \"custom software development\"`"
    )


def _print_noise_candidates(site_config: dict, settings, *, min_runs: int, limit: int) -> None:
    candidates = summarize_noise_candidates(settings, site_config=site_config, min_runs=min_runs, limit=limit)
    profile = load_noise_profile(settings, site_config=site_config)
    _console().print(
        f"[dim]Approved noise memory:[/dim] "
        f"{len(profile.keyword_phrases)} keyword phrases, "
        f"{len(profile.secondary_phrases)} secondary phrases, "
        f"{len(profile.domains)} domains"
    )
    if not candidates:
        _console().print("[yellow]No repeated learning candidates yet.[/yellow]")
        _console().print("[dim]Run 3-5 validate-free probes first, then review again.[/dim]")
        return
    for scope in ("keyword_phrase", "secondary_phrase", "domain"):
        scoped = [item for item in candidates if item.scope == scope]
        if not scoped:
            continue
        table = Table(title=scope.replace("_", " ").title())
        table.add_column("Candidate")
        table.add_column("Runs", justify="right")
        table.add_column("Hits", justify="right")
        table.add_column("Examples")
        for item in scoped:
            table.add_row(item.value, str(item.support_runs), str(item.support_count), "; ".join(item.examples))
        _console().print(table)
    _console().print(
        "[dim]Approve examples:[/dim] "
        "`uv run seo approve-noise --keyword-phrase \"web design\"` "
        "`--secondary-phrase \"mobile optimization\"` "
        "`--domain \"dictionary.com\"`"
    )

@app.command("research")
def research(keyword: str = Argument(..., help="Seed keyword")) -> None:
    settings, site_config, session_context = get_runtime()
    with session_context as session:
        repository = SeoRepository(session)
        services = build_services(settings, repository)
        result = asyncio.run(run_full_pipeline(keyword, site_config.model_dump(), services, repository, location=settings.search_location, console=_console()))
        table = Table(title=f"Opportunity Report: {keyword}")
        table.add_column("Keyword ID")
        table.add_column("Keyword")
        table.add_column("Score")
        table.add_column("Priority")
        for item in result["analyses"][:10]:
            opp = item["synthesis"].opportunity_score
            table.add_row(opp.keyword_id, opp.keyword_term, str(opp.composite_score), opp.priority)
        _console().print(table)
        for item in result["analyses"]:
            opp = item["synthesis"].opportunity_score
            if item["synthesis"].should_create_content and Confirm.ask(
                f"Create content for '{opp.keyword_term}'?",
                default=False,
            ):
                output = asyncio.run(write_article(opp.keyword_id, site_config.model_dump(), services, repository))
                _console().print(output.model_dump())
        _record_gemini_usage(repository, services)
        _print_serpapi_usage(repository, settings)
        _print_tavily_usage(repository, settings)
        _print_ddgs_usage(repository, settings)
        _print_bing_usage(repository, settings)
        _print_yahoo_usage(repository, settings)
        asyncio.run(services.scraper.close())


@app.command("validate-free")
def validate_free(keyword: str = Argument(..., help="Seed keyword")) -> None:
    _run_free_validation_command(keyword, sources=("ddgs", "bing", "yahoo"))


@app.command("validate-ddgs")
def validate_ddgs(keyword: str = Argument(..., help="Seed keyword")) -> None:
    _run_free_validation_command(keyword, sources=("ddgs",))


@app.command("validate-bing")
def validate_bing(keyword: str = Argument(..., help="Seed keyword")) -> None:
    _run_free_validation_command(keyword, sources=("bing",))


@app.command("validate-yahoo")
def validate_yahoo(keyword: str = Argument(..., help="Seed keyword")) -> None:
    _run_free_validation_command(keyword, sources=("yahoo",))


@app.command("review-noise")
def review_noise(
    min_runs: Annotated[int, Option("--min-runs", help="Minimum distinct runs before suggesting a candidate")] = 2,
    limit: Annotated[int, Option("--limit", help="Maximum candidates to print")] = 12,
) -> None:
    settings, site_config, _ = get_runtime()
    _print_noise_candidates(site_config.model_dump(), settings, min_runs=min_runs, limit=limit)


@app.command("review-training")
def review_training(
    min_runs: Annotated[int, Option("--min-runs", help="Minimum distinct runs before suggesting a candidate")] = 2,
    limit: Annotated[int, Option("--limit", help="Maximum candidates to print")] = 18,
) -> None:
    settings, site_config, _ = get_runtime()
    _print_training_candidates(site_config.model_dump(), settings, min_runs=min_runs, limit=limit)


@app.command("approve-noise")
def approve_noise(
    keyword_phrase: Annotated[list[str] | None, Option("--keyword-phrase", help="Approve a shortlist phrase to demote")] = None,
    secondary_phrase: Annotated[list[str] | None, Option("--secondary-phrase", help="Approve a support phrase to suppress")] = None,
    domain: Annotated[list[str] | None, Option("--domain", help="Approve a weak domain to ignore for article evidence")] = None,
) -> None:
    settings, site_config, _ = get_runtime()
    profile = approve_noise_entries(
        settings,
        site_config=site_config.model_dump(),
        keyword_phrases=keyword_phrase,
        secondary_phrases=secondary_phrase,
        domains=domain,
    )
    _console().print(
        f"[green]Updated[/green] approved noise memory: "
        f"{len(profile.keyword_phrases)} keyword phrases, "
        f"{len(profile.secondary_phrases)} secondary phrases, "
        f"{len(profile.domains)} domains"
    )


@app.command("approve-training")
def approve_training(
    noise_keyword_phrase: Annotated[list[str] | None, Option("--noise-keyword-phrase", help="Approve a shortlist phrase to demote")] = None,
    noise_secondary_phrase: Annotated[list[str] | None, Option("--noise-secondary-phrase", help="Approve a support phrase to suppress")] = None,
    noise_domain: Annotated[list[str] | None, Option("--noise-domain", help="Approve a weak domain to ignore")] = None,
    valid_keyword_phrase: Annotated[list[str] | None, Option("--valid-keyword-phrase", help="Approve a strong keyword phrase to boost")] = None,
    valid_secondary_phrase: Annotated[list[str] | None, Option("--valid-secondary-phrase", help="Approve a strong support phrase to boost")] = None,
    trusted_domain: Annotated[list[str] | None, Option("--trusted-domain", help="Approve a domain as a legitimacy signal")] = None,
) -> None:
    settings, site_config, _ = get_runtime()
    profile = approve_training_entries(
        settings,
        site_config=site_config.model_dump(),
        noise_keyword_phrases=noise_keyword_phrase,
        noise_secondary_phrases=noise_secondary_phrase,
        noise_domains=noise_domain,
        valid_keyword_phrases=valid_keyword_phrase,
        valid_secondary_phrases=valid_secondary_phrase,
        trusted_domains=trusted_domain,
    )
    _console().print(
        f"[green]Updated[/green] training memory: "
        f"noise={len(profile.keyword_phrases) + len(profile.secondary_phrases) + len(profile.domains)}, "
        f"validity={len(profile.valid_keyword_phrases) + len(profile.valid_secondary_phrases)}, "
        f"legitimacy={len(profile.trusted_domains)}"
    )


@app.command("profile-list")
def profile_list() -> None:
    settings = resolve_runtime_settings()
    active = get_active_profile(settings)
    table = Table(title="Profiles")
    table.add_column("Profile")
    table.add_column("Status")
    profiles = list_profiles(settings)
    if not profiles:
        _console().print("[yellow]No profiles yet. Use `uv run seo profile-init <slug>`.[/yellow]")
        return
    for slug in profiles:
        table.add_row(slug, "active" if slug == active else "")
    _console().print(table)


@app.command("profile-init")
def profile_init(
    slug: str = Argument(..., help="Profile slug"),
    from_current: Annotated[bool, Option("--from-current", help="Copy the currently active site config into the new profile")] = False,
    use: Annotated[bool, Option("--use", help="Switch to the new profile after creating it")] = False,
) -> None:
    source_site_config = get_runtime()[1] if from_current else SiteConfig()
    normalized_slug, target_root = create_profile(slug, site_config=source_site_config, use=use)
    _console().print(f"[green]Created[/green] profile {normalized_slug} at {target_root}")
    if use:
        _console().print(f"[green]Active profile[/green] → {normalized_slug}")


@app.command("profile-use")
def profile_use(slug: str = Argument(..., help="Profile slug")) -> None:
    active = set_active_profile(slug)
    _console().print(f"[green]Active profile[/green] → {active}")


@app.command("profile-status")
def profile_status() -> None:
    settings = resolve_runtime_settings()
    active = get_active_profile(settings)
    if active is None:
        _console().print("[dim]Active profile:[/dim] default")
        _console().print(f"[dim]Site config:[/dim] {settings.resolved_site_config_path}")
        return
    active_settings = resolve_runtime_settings(active)
    _console().print(f"[dim]Active profile:[/dim] {active}")
    _console().print(f"[dim]Site config:[/dim] {active_settings.resolved_site_config_path}")
    _console().print(f"[dim]DB:[/dim] {active_settings.database_url}")
    _console().print(f"[dim]Cache:[/dim] {active_settings.resolved_cache_dir}")


@app.command("final-review")
def final_review(
    profiles: Annotated[list[str] | None, Argument(help="One or more profile slugs. Defaults to all profiles if omitted.")] = None,
    min_runs: Annotated[int, Option("--min-runs", help="Minimum distinct runs before suggesting a candidate")] = 2,
    limit: Annotated[int, Option("--limit", help="Maximum candidates per profile")] = 9,
) -> None:
    root_settings = resolve_runtime_settings()
    selected = profiles or list_profiles(root_settings)
    if not selected:
        raise SystemExit("No profiles found. Create profiles first with `uv run seo profile-init <slug>`.")

    summary = Table(title="Final Review")
    summary.add_column("Profile")
    summary.add_column("Runs", justify="right")
    summary.add_column("Noise", justify="right")
    summary.add_column("Validity", justify="right")
    summary.add_column("Legitimacy", justify="right")

    shared_valid_keywords: set[str] | None = None
    shared_trusted_domains: set[str] | None = None
    for slug in selected:
        settings, site_config, _ = get_runtime(slug)
        stats = learning_memory_stats(settings, site_config=site_config.model_dump())
        summary.add_row(
            slug,
            str(stats["runs"]),
            str(stats["approved_noise"]),
            str(stats["approved_validity"]),
            str(stats["approved_legitimacy"]),
        )
        profile = load_noise_profile(settings, site_config=site_config.model_dump())
        valid_keywords = set(profile.valid_keyword_phrases)
        trusted_domains = set(profile.trusted_domains)
        shared_valid_keywords = valid_keywords if shared_valid_keywords is None else shared_valid_keywords & valid_keywords
        shared_trusted_domains = trusted_domains if shared_trusted_domains is None else shared_trusted_domains & trusted_domains
    _console().print(summary)

    if shared_valid_keywords:
        _console().print(f"[dim]Shared valid keyword phrases:[/dim] {', '.join(sorted(shared_valid_keywords))}")
    if shared_trusted_domains:
        _console().print(f"[dim]Shared trusted domains:[/dim] {', '.join(sorted(shared_trusted_domains))}")

    for slug in selected:
        settings, site_config, _ = get_runtime(slug)
        _console().print(f"\n[bold]{slug}[/bold]")
        _print_training_candidates(site_config.model_dump(), settings, min_runs=min_runs, limit=limit)

@app.command("research-batch")
def research_batch() -> None:
    _, site_config, _ = get_runtime()
    if not site_config.seed_keywords:
        raise SystemExit("No seed_keywords configured in data/site_config.json")
    for seed in site_config.seed_keywords:
        research(seed)


@app.command("serp")
def serp(keyword: str = Argument(..., help="Keyword to analyze")) -> None:
    settings, _, session_context = get_runtime()
    with session_context as session:
        repository = SeoRepository(session)
        services = build_services(settings, repository)
        stored = repository.upsert_keyword(
            Keyword(term=keyword, seed_keyword=keyword, source="manual")
        )
        output = asyncio.run(
            services.serp_agent.run(SerpAgentInput(keyword_id=stored.id, keyword_term=stored.term))
        )
        _console().print(output.model_dump())
        _record_gemini_usage(repository, services)


@app.command("brief")
def brief(
    keyword_id: str = Argument(..., help="Keyword ID"),
    force: Annotated[bool, Option("--force", help="Generate brief even if score/rankable gate says no")] = False,
) -> None:
    settings, site_config, session_context = get_runtime()
    with session_context as session:
        repository = SeoRepository(session)
        services = build_services(settings, repository)
        output = asyncio.run(generate_brief(keyword_id, site_config.model_dump(), services, repository, force=force))
        _console().print(output.model_dump())
        _record_gemini_usage(repository, services)
        asyncio.run(services.scraper.close())


@app.command("write")
def write(
    keyword_id: str = Argument(..., help="Keyword ID"),
    force: Annotated[bool, Option("--force", help="Write article even if score/rankable gate says no")] = False,
) -> None:
    settings, site_config, session_context = get_runtime()
    with session_context as session:
        repository = SeoRepository(session)
        services = build_services(settings, repository)
        output = asyncio.run(write_article(keyword_id, site_config.model_dump(), services, repository, force=force))
        _console().print(output.model_dump())
        _record_gemini_usage(repository, services)


@app.command("rewrite")
def rewrite(url: str = Argument(..., help="Published URL to rewrite")) -> None:
    settings, site_config, session_context = get_runtime()
    with session_context as session:
        repository = SeoRepository(session)
        services = build_services(settings, repository)
        output = asyncio.run(rewrite_article(url, site_config.model_dump(), services, repository))
        _console().print(output.model_dump())
        _record_gemini_usage(repository, services)
        asyncio.run(services.scraper.close())


@app.command("publish")
def publish(article_id: str = Argument(...), url: str = Argument(...)) -> None:
    _, _, session_context = get_runtime()
    with session_context as session:
        repository = SeoRepository(session)
        article = repository.get_article(article_id)
        if article is None:
            raise SystemExit(f"Article not found: {article_id}")
        if article.status != "approved":
            raise SystemExit(
                f"Article '{article.title}' must be approved before it can be published."
            )
        article = repository.update_article(
            article_id,
            status="published",
            published_at=datetime.now(timezone.utc),
            published_url=url,
        )
        _console().print(f"[green]Published[/green] {article.title} -> {url}")


@app.command("report")
def report() -> None:
    _, _, session_context = get_runtime()
    with session_context as session:
        repository = SeoRepository(session)
        top_keywords = repository.get_top_opportunities(limit=10)
        table = Table(title="Opportunity Report")
        table.add_column("Keyword")
        table.add_column("Score")
        table.add_column("Volume")
        table.add_column("Difficulty")
        for keyword in top_keywords:
            table.add_row(
                keyword.term,
                str(keyword.opportunity_score or "-"),
                str(keyword.monthly_volume or "-"),
                str(keyword.difficulty_score or "-"),
            )
        _console().print(table)
        _console().print(
            {
                "total_keywords": len(repository.list_keywords()),
                "articles": len(repository.list_articles()),
                "published_articles": len(repository.get_published_articles()),
                "content_performance": repository.get_content_performance_by_type(),
            }
        )


@app.command("budget")
def budget() -> None:
    _, _, session_context = get_runtime()
    with session_context as session:
        repository = SeoRepository(session)
        table = Table(title="API Budget")
        table.add_column("Provider")
        table.add_column("Calls")
        table.add_column("Spend")
        table.add_column("Tokens In")
        table.add_column("Tokens Out")
        for provider in ["serpapi", "tavily", "ddgs", "bing", "yahoo", "gemini"]:
            usage = repository.get_api_usage(provider)
            table.add_row(
                provider,
                str(usage.call_count if usage else 0),
                f"${usage.spend_usd:.2f}" if usage else "$0.00",
                str(usage.tokens_in if usage else 0),
                str(usage.tokens_out if usage else 0),
            )
        _console().print(table)


@app.command("config")
def config() -> None:
    settings, site_config, _ = get_runtime()
    updated = SiteConfig(
        site_url=Prompt.ask("Site URL", default=site_config.site_url),
        site_name=Prompt.ask("Site name", default=site_config.site_name),
        site_description=Prompt.ask("Site description", default=site_config.site_description),
        target_audience=Prompt.ask("Target audience", default=site_config.target_audience),
        services=[
            item.strip()
            for item in Prompt.ask(
                "Services (comma-separated)",
                default=", ".join(site_config.services),
            ).split(",")
            if item.strip()
        ],
        primary_language=Prompt.ask("Primary language", default=site_config.primary_language),
        blog_url=Prompt.ask("Blog URL", default=site_config.blog_url),
        existing_articles=[
            item.strip()
            for item in Prompt.ask(
                "Existing articles (comma-separated URLs)",
                default=", ".join(site_config.existing_articles),
            ).split(",")
            if item.strip()
        ],
        seed_keywords=[
            item.strip()
            for item in Prompt.ask(
                "Seed keywords (comma-separated)",
                default=", ".join(site_config.seed_keywords),
            ).split(",")
            if item.strip()
        ],
        target_persona=Prompt.ask("Target persona", default=site_config.target_persona),
        competitors=[
            item.strip()
            for item in Prompt.ask(
                "Competitors (comma-separated)",
                default=", ".join(site_config.competitors),
            ).split(",")
            if item.strip()
        ],
        geographic_focus=[
            item.strip()
            for item in Prompt.ask(
                "Geographic focus (comma-separated)",
                default=", ".join(site_config.geographic_focus),
            ).split(",")
            if item.strip()
        ],
    )
    save_profile_site_config(get_active_profile() or "default", updated)
    _console().print(f"[green]Updated[/green] {settings.resolved_site_config_path}")
