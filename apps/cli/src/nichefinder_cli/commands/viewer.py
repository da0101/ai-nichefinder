import webbrowser

from rich.console import Console
from typer import Option

from nichefinder_cli.runtime import get_runtime
from nichefinder_cli.viewer_server import serve_viewer


def view(
    host: str = Option("127.0.0.1", help="Host to bind the local viewer to."),
    port: int = Option(8765, min=1, max=65535, help="Port for the local viewer."),
) -> None:
    settings, _, _ = get_runtime()
    url = f"http://{host}:{port}"
    Console().print(f"[green]Viewer[/green] {url}")
    try:
        webbrowser.open(url, new=2)
    except Exception:
        Console().print("[yellow]Could not auto-open browser; open the URL manually.[/yellow]")
    serve_viewer(settings, host, port)
