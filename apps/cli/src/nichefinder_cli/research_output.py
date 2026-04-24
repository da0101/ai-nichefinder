from typing import Any

from rich.console import Console
from rich.table import Table


def normalize_external_validation_output(result: Any) -> tuple[list[Any], list[Any], list[Any]]:
    if not isinstance(result, tuple):
        raise TypeError("Expected external validation output to be a tuple.")
    if len(result) == 3:
        shortlist, keyword_validations, problem_validations = result
        return list(shortlist), list(keyword_validations), list(problem_validations)
    if len(result) == 2:
        shortlist, problem_validations = result
        return list(shortlist), [], list(problem_validations)
    raise ValueError("Unexpected external validation output shape.")


def _value(item: Any, field: str, default: Any = "") -> Any:
    if isinstance(item, dict):
        return item.get(field, default)
    return getattr(item, field, default)


def _list_value(item: Any, field: str) -> list[Any]:
    value = _value(item, field, [])
    if isinstance(value, list):
        return value
    if value in ("", None):
        return []
    return [value]


def _source_title(validations: list[Any], suffix: str) -> str:
    source = _value(validations[0], "source", "external") if validations else "external"
    return f"{str(source).upper()} {suffix}"


def _group_by_source(items: list[Any]) -> list[list[Any]]:
    grouped: dict[str, list[Any]] = {}
    order: list[str] = []
    for item in items:
        source = str(_value(item, "source", "external"))
        if source not in grouped:
            grouped[source] = []
            order.append(source)
        grouped[source].append(item)
    return [grouped[source] for source in order]


def print_buyer_problems(console: Console, buyer_problems: list[dict]) -> None:
    if not buyer_problems:
        return
    table = Table(title="Buyer Problems")
    table.add_column("#", style="dim", width=3)
    table.add_column("Problem")
    table.add_column("Article angle")
    table.add_column("Seed")
    table.add_column("Evidence")
    for index, item in enumerate(buyer_problems, 1):
        evidence = "\n".join(_list_value(item, "evidence_queries")[:2]) or "—"
        table.add_row(
            str(index),
            _value(item, "problem", ""),
            _value(item, "article_angle", ""),
            _value(item, "keyword_seed", ""),
            evidence,
        )
    console.print(table)


def print_pre_serp_shortlist(console: Console, shortlist: list, max_keywords: int) -> None:
    if not shortlist:
        return
    table = Table(title="Pre-SERP Shortlist")
    table.add_column("#", style="dim", width=3)
    table.add_column("Keyword")
    table.add_column("Pre-score", justify="right")
    table.add_column("Signals")
    for rank, item in enumerate(shortlist[:max_keywords], 1):
        signals = ", ".join(_list_value(item, "notes")[:3]) or "fallback"
        table.add_row(str(rank), _value(item, "term", ""), f"{float(_value(item, 'score', 0.0)):.0f}", signals)
    console.print(table)


def print_article_evidence(console: Console, evidence_rows: list) -> None:
    if not evidence_rows:
        return
    table = Table(title="Free Article Evidence")
    table.add_column("Source")
    table.add_column("Primary keyword")
    table.add_column("Score", justify="right")
    table.add_column("Pages", justify="right")
    table.add_column("Recurring headings")
    table.add_column("Secondary keywords")
    table.add_column("Questions")
    for item in evidence_rows:
        headings = ", ".join(_list_value(item, "recurring_headings")[:2]) or "none"
        secondary = ", ".join(_list_value(item, "suggested_secondary_keywords")[:3]) or "none"
        questions = ", ".join(_list_value(item, "question_bank")[:2]) or "none"
        table.add_row(
            str(_value(item, "source", "external")).upper(),
            _value(item, "suggested_primary_keyword", ""),
            f"{float(_value(item, 'validation_score', 0.0)):.0f}",
            str(_value(item, "pages_scraped", 0)),
            headings,
            secondary,
            questions,
        )
    console.print(table)


def print_keyword_validations(console: Console, validations: list) -> None:
    if not validations:
        return
    for group in _group_by_source(validations):
        table = Table(title=_source_title(group, "Keyword Validation"))
        table.add_column("Keyword")
        table.add_column("Score", justify="right")
        table.add_column("Hits", justify="right")
        table.add_column("Domains")
        table.add_column("Notes")
        for item in group:
            domains = ", ".join(_list_value(item, "top_domains")[:3]) or "no sources"
            notes = ", ".join(_list_value(item, "notes")[:3]) or "—"
            table.add_row(
                _value(item, "query", ""),
                f"{float(_value(item, 'score', 0.0)):.0f}",
                str(_value(item, "result_count", 0)),
                domains,
                notes,
            )
        console.print(table)


def print_problem_validations(console: Console, validations: list) -> None:
    if not validations:
        return
    for group in _group_by_source(validations):
        table = Table(title=_source_title(group, "Buyer Problem Validation"))
        table.add_column("Query")
        table.add_column("Score", justify="right")
        table.add_column("Hits", justify="right")
        table.add_column("Domains")
        table.add_column("Notes")
        for item in group:
            domains = ", ".join(_list_value(item, "top_domains")[:3]) or "no sources"
            notes = ", ".join(_list_value(item, "notes")[:3]) or "—"
            table.add_row(
                _value(item, "query", ""),
                f"{float(_value(item, 'score', 0.0)):.0f}",
                str(_value(item, "result_count", 0)),
                domains,
                notes,
            )
        console.print(table)


def print_cross_source_patterns(console: Console, patterns: list, *, title: str, include_research_bank: bool) -> None:
    if not patterns:
        return
    table = Table(title=title)
    table.add_column("Query")
    if any(len(_list_value(item, "query_variants")) > 1 for item in patterns):
        table.add_column("Variants")
        show_variants = True
    else:
        show_variants = False
    table.add_column("Engines")
    table.add_column("Agreement")
    table.add_column("Repeated domains")
    if include_research_bank:
        table.add_column("Repeated secondary keywords")
        table.add_column("Repeated questions")
    for item in patterns:
        domains = ", ".join(_list_value(item, "repeated_domains")[:3]) or "none"
        row = [
            _value(item, "query", ""),
        ]
        if show_variants:
            variants = [value for value in _list_value(item, "query_variants") if value != _value(item, "query", "")]
            row.append(", ".join(variants[:2]) or "—")
        row.extend(
            [
                ", ".join(_list_value(item, "sources")) or "none",
                _value(item, "agreement", ""),
                domains,
            ]
        )
        if include_research_bank:
            row.extend(
                [
                    ", ".join(_list_value(item, "repeated_secondary_keywords")[:3]) or "none",
                    ", ".join(_list_value(item, "repeated_questions")[:2]) or "none",
                ]
        )
        table.add_row(*row)
    console.print(table)


def print_source_health(console: Console, validations: list[Any]) -> None:
    if not validations:
        return
    grouped = _group_by_source(validations)
    table = Table(title="Source Health")
    table.add_column("Source")
    table.add_column("Status")
    table.add_column("Healthy", justify="right")
    table.add_column("Degraded", justify="right")
    table.add_column("Unavailable", justify="right")
    table.add_column("Top signal")
    for group in grouped:
        source = str(_value(group[0], "source", "external")).upper()
        healthy = 0
        degraded = 0
        unavailable = 0
        note_counts: dict[str, int] = {}
        for item in group:
            notes = _list_value(item, "notes")
            note = notes[0] if notes else "—"
            note_counts[note] = note_counts.get(note, 0) + 1
            if bool(_value(item, "degraded", False)):
                degraded += 1
            elif int(_value(item, "result_count", 0)) == 0 or any("unavailable" in str(n).lower() for n in notes):
                unavailable += 1
            else:
                healthy += 1
        if healthy and not degraded and not unavailable:
            status = "[green]healthy[/green]"
        elif degraded or unavailable:
            status = "[yellow]mixed[/yellow]" if healthy else "[red]degraded[/red]"
        else:
            status = "[green]healthy[/green]"
        top_signal = sorted(note_counts.items(), key=lambda item: (-item[1], item[0]))[0][0]
        table.add_row(source, status, str(healthy), str(degraded), str(unavailable), top_signal)
    console.print(table)
