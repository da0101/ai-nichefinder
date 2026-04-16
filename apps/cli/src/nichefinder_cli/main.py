from nichefinder_cli.commands.briefs import briefs_app
from nichefinder_cli.commands.db import db_app
from nichefinder_cli.commands.keywords import keywords_app
from nichefinder_cli.commands.ranks import ranks_app
from nichefinder_cli.commands.status import status
from typer import Typer

app = Typer(
    add_completion=False,
    no_args_is_help=True,
    help="CLI-first niche SEO intelligence for localized keyword research.",
)

app.command()(status)
app.add_typer(db_app, name="db")
app.add_typer(keywords_app, name="keywords")
app.add_typer(briefs_app, name="briefs")
app.add_typer(ranks_app, name="ranks")

