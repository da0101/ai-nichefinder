from typer import Argument, Option, Typer
from typing import Annotated

from nichefinder_cli.commands.root import shared
from nichefinder_cli.runtime import get_runtime, list_profiles, resolve_runtime_settings
from nichefinder_core.noise_memory import (
    approve_noise_entries,
    approve_training_entries,
    learning_memory_stats,
    load_noise_profile,
)
from rich.table import Table


def register_review_commands(app: Typer) -> None:
    app.command("review-noise")(review_noise)
    app.command("review-training")(review_training)
    app.command("approve-noise")(approve_noise)
    app.command("approve-training")(approve_training)
    app.command("final-review")(final_review)


def review_noise(
    min_runs: Annotated[int, Option("--min-runs", help="Minimum distinct runs before suggesting a candidate")] = 2,
    limit: Annotated[int, Option("--limit", help="Maximum candidates to print")] = 12,
) -> None:
    settings, site_config, _ = get_runtime()
    shared.print_noise_candidates(site_config.model_dump(), settings, min_runs=min_runs, limit=limit)


def review_training(
    min_runs: Annotated[int, Option("--min-runs", help="Minimum distinct runs before suggesting a candidate")] = 2,
    limit: Annotated[int, Option("--limit", help="Maximum candidates to print")] = 18,
) -> None:
    settings, site_config, _ = get_runtime()
    shared.print_training_candidates(site_config.model_dump(), settings, min_runs=min_runs, limit=limit)


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
    shared.console().print(
        f"[green]Updated[/green] approved noise memory: "
        f"{len(profile.keyword_phrases)} keyword phrases, "
        f"{len(profile.secondary_phrases)} secondary phrases, "
        f"{len(profile.domains)} domains"
    )


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
    shared.console().print(
        f"[green]Updated[/green] training memory: "
        f"noise={len(profile.keyword_phrases) + len(profile.secondary_phrases) + len(profile.domains)}, "
        f"validity={len(profile.valid_keyword_phrases) + len(profile.valid_secondary_phrases)}, "
        f"legitimacy={len(profile.trusted_domains)}"
    )


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
    shared.console().print(summary)

    if shared_valid_keywords:
        shared.console().print(f"[dim]Shared valid keyword phrases:[/dim] {', '.join(sorted(shared_valid_keywords))}")
    if shared_trusted_domains:
        shared.console().print(f"[dim]Shared trusted domains:[/dim] {', '.join(sorted(shared_trusted_domains))}")

    for slug in selected:
        settings, site_config, _ = get_runtime(slug)
        shared.console().print(f"\n[bold]{slug}[/bold]")
        shared.print_training_candidates(site_config.model_dump(), settings, min_runs=min_runs, limit=limit)
