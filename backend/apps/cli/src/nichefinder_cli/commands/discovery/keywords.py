import json

from rich.console import Console
from rich.table import Table
from typer import Argument, Typer

from nichefinder_db import SeoRepository

keywords_app = Typer(help="Keyword discovery and enrichment workflows.")


@keywords_app.command("list")
def list_keywords() -> None:
    from nichefinder_cli.runtime import get_runtime

    _, _, session_context = get_runtime()
    with session_context as session:
        repository = SeoRepository(session)
        table = Table(title="Keywords")
        table.add_column("Keyword")
        table.add_column("Volume")
        table.add_column("Difficulty")
        table.add_column("Trend")
        table.add_column("Intent")
        table.add_column("Score")
        table.add_column("Action")
        for keyword in repository.list_keywords():
            brief = repository.get_latest_content_brief(keyword.id)
            table.add_row(
                keyword.term,
                str(keyword.monthly_volume or "-"),
                str(keyword.difficulty_score or "-"),
                keyword.trend_direction or "-",
                keyword.search_intent.value if keyword.search_intent else "-",
                str(keyword.opportunity_score or "-"),
                "briefed" if brief else "-",
            )
        Console().print(table)


@keywords_app.command("cluster")
def cluster_keywords() -> None:
    from nichefinder_cli.runtime import get_runtime

    _, _, session_context = get_runtime()
    with session_context as session:
        repository = SeoRepository(session)
        clusters = repository.cluster_keywords()
        table = Table(title="Keyword Clusters")
        table.add_column("Cluster")
        table.add_column("Volume")
        table.add_column("Primary Keyword ID")
        for cluster in clusters:
            table.add_row(cluster.cluster_name, str(cluster.total_cluster_volume), cluster.primary_keyword_id)
        Console().print(table)


@keywords_app.command("inspect")
def inspect_keyword(keyword_id: str = Argument(..., help="Keyword ID")) -> None:
    from nichefinder_cli.runtime import get_runtime

    _, _, session_context = get_runtime()
    with session_context as session:
        repository = SeoRepository(session)
        keyword = repository.get_keyword(keyword_id)
        if keyword is None:
            raise SystemExit(f"Keyword not found: {keyword_id}")

        console = Console()
        keyword_table = Table(title="Keyword")
        keyword_table.add_column("Field")
        keyword_table.add_column("Value")
        keyword_table.add_row("ID", keyword.id)
        keyword_table.add_row("Term", keyword.term)
        keyword_table.add_row("Source", keyword.source)
        keyword_table.add_row("Intent", keyword.search_intent.value if keyword.search_intent else "-")
        keyword_table.add_row("Trend", keyword.trend_direction or "-")
        keyword_table.add_row("Volume", str(keyword.monthly_volume or "-"))
        keyword_table.add_row("Difficulty", str(keyword.difficulty_score or "-"))
        keyword_table.add_row("Opportunity", str(keyword.opportunity_score or "-"))
        console.print(keyword_table)

        serp_result = repository.get_latest_serp_result(keyword.id)
        if serp_result is None:
            console.print("[yellow]No SERP analysis saved for this keyword yet.[/yellow]")
            return

        competition = json.loads(serp_result.competition_analysis)
        summary = Table(title="Latest SERP Analysis")
        summary.add_column("Field")
        summary.add_column("Value")
        summary.add_row("Fetched", str(serp_result.fetched_at))
        summary.add_row("Rankable", str(bool(competition.get("rankable"))))
        summary.add_row("Competition", competition.get("competition_level", "-"))
        summary.add_row("Dominant type", competition.get("dominant_content_type", "-"))
        summary.add_row("Angle", competition.get("recommended_content_angle", "-"))
        console.print(summary)

        pages_table = Table(title="Top SERP Pages")
        pages_table.add_column("Pos")
        pages_table.add_column("Domain")
        pages_table.add_column("Title")
        pages_table.add_column("URL")
        for page in json.loads(serp_result.pages_json)[:10]:
            pages_table.add_row(
                str(page.get("position", "-")),
                page.get("domain", "-"),
                page.get("title", "-"),
                page.get("url", "-"),
            )
        console.print(pages_table)

        competitor_pages = repository.list_competitor_pages(serp_result.id)
        if competitor_pages:
            competitor_table = Table(title="Scraped Competitor Pages")
            competitor_table.add_column("Title")
            competitor_table.add_column("Words")
            competitor_table.add_column("Reading min")
            competitor_table.add_column("URL")
            for page in competitor_pages:
                competitor_table.add_row(
                    page.title,
                    str(page.word_count),
                    str(page.estimated_reading_time_min),
                    page.url,
                )
            console.print(competitor_table)

        brief = repository.get_latest_content_brief(keyword.id)
        if brief is not None:
            brief_table = Table(title="Latest Brief")
            brief_table.add_column("Field")
            brief_table.add_column("Value")
            brief_table.add_row("Title", brief.suggested_title)
            brief_table.add_row("Type", brief.content_type.value)
            brief_table.add_row("Word count", str(brief.word_count_target))
            brief_table.add_row("Tone", brief.tone)
            brief_table.add_row("H2s", "\n".join(brief.suggested_h2_structure) or "-")
            brief_table.add_row("Questions", "\n".join(brief.questions_to_answer) or "-")
            console.print(brief_table)
