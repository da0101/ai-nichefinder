import asyncio
from typing import Any

from rich.console import Console
from rich.table import Table

from nichefinder_cli.free_validation import run_free_validation_pipeline
from nichefinder_cli.runtime import ServiceContainer, build_services, get_runtime
from nichefinder_core.noise_memory import (
    load_noise_profile,
    summarize_noise_candidates,
    summarize_training_candidates,
)
from nichefinder_core.settings import Settings
from nichefinder_db import SeoRepository


def console() -> Console:
    return Console()


def record_gemini_usage(repository: SeoRepository, services: ServiceContainer) -> None:
    usage = services.gemini.get_usage_stats()
    repository.record_api_usage(
        provider="gemini",
        tokens_in=usage["prompt_tokens"],
        tokens_out=usage["response_tokens"],
    )


def print_serpapi_usage(repository: SeoRepository, settings: Settings) -> None:
    usage = repository.get_api_usage("serpapi")
    used = usage.call_count if usage else 0
    limit = settings.serpapi_calls_per_month
    remaining = max(0, limit - used)
    color = "green" if remaining > 30 else "yellow" if remaining > 10 else "red"
    console().print(
        f"\n[dim]SerpAPI this month:[/dim] [{color}]{used}/{limit} searches used | {remaining} remaining[/{color}]"
    )


def print_tavily_usage(repository: SeoRepository, settings: Settings) -> None:
    usage = repository.get_api_usage("tavily")
    used = usage.call_count if usage else 0
    limit = settings.tavily_credits_per_month
    remaining = max(0, limit - used)
    color = "green" if remaining > 500 else "yellow" if remaining > 200 else "red"
    console().print(
        f"[dim]Tavily this month:[/dim] [{color}]{used}/{limit} credits used | {remaining} remaining[/{color}]"
    )


def print_ddgs_usage(repository: SeoRepository, settings: Settings) -> None:
    usage = repository.get_api_usage("ddgs")
    used = usage.call_count if usage else 0
    limit = settings.ddgs_calls_per_month
    remaining = max(0, limit - used)
    color = "green" if remaining > 150 else "yellow" if remaining > 50 else "red"
    console().print(
        f"[dim]DDGS this month:[/dim] [{color}]{used}/{limit} validations used | {remaining} remaining[/{color}]"
    )


def print_bing_usage(repository: SeoRepository, settings: Settings) -> None:
    usage = repository.get_api_usage("bing")
    used = usage.call_count if usage else 0
    limit = settings.bing_calls_per_month
    remaining = max(0, limit - used)
    color = "green" if remaining > 150 else "yellow" if remaining > 50 else "red"
    console().print(
        f"[dim]Bing this month:[/dim] [{color}]{used}/{limit} validations used | {remaining} remaining[/{color}]"
    )


def print_yahoo_usage(repository: SeoRepository, settings: Settings) -> None:
    usage = repository.get_api_usage("yahoo")
    used = usage.call_count if usage else 0
    limit = settings.yahoo_calls_per_month
    remaining = max(0, limit - used)
    color = "green" if remaining > 150 else "yellow" if remaining > 50 else "red"
    console().print(
        f"[dim]Yahoo this month:[/dim] [{color}]{used}/{limit} validations used | {remaining} remaining[/{color}]"
    )


def print_usage_for_sources(repository: SeoRepository, settings: Settings, sources: tuple[str, ...]) -> None:
    printers = {
        "ddgs": print_ddgs_usage,
        "bing": print_bing_usage,
        "yahoo": print_yahoo_usage,
    }
    for source in sources:
        printer = printers.get(source)
        if printer is not None:
            printer(repository, settings)


def run_free_validation_command(keyword: str, *, sources: tuple[str, ...]) -> None:
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
                console=console(),
            )
        )
        record_gemini_usage(repository, services)
        print_usage_for_sources(repository, settings, sources)
        asyncio.run(services.scraper.close())


def print_training_candidates(
    site_config: dict[str, Any],
    settings: Settings,
    *,
    min_runs: int,
    limit: int,
    label: str | None = None,
) -> None:
    candidates = summarize_training_candidates(
        settings,
        site_config=site_config,
        min_runs=min_runs,
        limit=limit,
        label=label,
    )
    profile = load_noise_profile(settings, site_config=site_config)
    console().print(
        f"[dim]Approved training memory:[/dim] "
        f"noise={len(profile.keyword_phrases) + len(profile.secondary_phrases) + len(profile.domains)}, "
        f"validity={len(profile.valid_keyword_phrases) + len(profile.valid_secondary_phrases)}, "
        f"legitimacy={len(profile.trusted_domains)}"
    )
    if not candidates:
        console().print("[yellow]No repeated training candidates yet.[/yellow]")
        console().print("[dim]Run 3-5 validate-free probes first, then review again.[/dim]")
        return

    for candidate_label in ("validity", "legitimacy", "noise"):
        scoped_label = [item for item in candidates if item.label == candidate_label]
        if not scoped_label:
            continue
        for scope in ("keyword_phrase", "secondary_phrase", "domain"):
            scoped = [item for item in scoped_label if item.scope == scope]
            if not scoped:
                continue
            table = Table(title=f"{candidate_label.title()} | {scope.replace('_', ' ').title()}")
            table.add_column("Candidate")
            table.add_column("Runs", justify="right")
            table.add_column("Hits", justify="right")
            table.add_column("Examples")
            for item in scoped:
                table.add_row(item.value, str(item.support_runs), str(item.support_count), "; ".join(item.examples))
            console().print(table)

    console().print(
        "[dim]Approve examples:[/dim] "
        "`uv run seo approve-training --valid-keyword-phrase \"food cost percentage\"` "
        "`--trusted-domain \"restaurant.org\"` "
        "`--noise-keyword-phrase \"custom software development\"`"
    )


def print_noise_candidates(site_config: dict[str, Any], settings: Settings, *, min_runs: int, limit: int) -> None:
    candidates = summarize_noise_candidates(settings, site_config=site_config, min_runs=min_runs, limit=limit)
    profile = load_noise_profile(settings, site_config=site_config)
    console().print(
        f"[dim]Approved noise memory:[/dim] "
        f"{len(profile.keyword_phrases)} keyword phrases, "
        f"{len(profile.secondary_phrases)} secondary phrases, "
        f"{len(profile.domains)} domains"
    )
    if not candidates:
        console().print("[yellow]No repeated learning candidates yet.[/yellow]")
        console().print("[dim]Run 3-5 validate-free probes first, then review again.[/dim]")
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
        console().print(table)

    console().print(
        "[dim]Approve examples:[/dim] "
        "`uv run seo approve-noise --keyword-phrase \"web design\"` "
        "`--secondary-phrase \"mobile optimization\"` "
        "`--domain \"dictionary.com\"`"
    )
