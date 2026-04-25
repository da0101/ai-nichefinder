from typer import Typer

from nichefinder_cli.commands.content import articles_app
from nichefinder_cli.commands.discovery import keywords_app
from nichefinder_cli.commands.monitoring import monitor_app, ranks_app
from nichefinder_cli.commands.root import (
    register_content_commands,
    register_profile_commands,
    register_reporting_commands,
    register_research_commands,
    register_review_commands,
)
from nichefinder_cli.commands.system import db_app, status, view

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

register_research_commands(app)
register_review_commands(app)
register_profile_commands(app)
register_content_commands(app)
register_reporting_commands(app)
