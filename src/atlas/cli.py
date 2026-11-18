import typer

app = typer.Typer(help="ATLAS research and paper-trading CLI.")


@app.command()
def status() -> None:
    """Show the configured operating mode."""
    typer.echo("ATLAS v0.1.0 | execution_mode=paper | live_execution=disabled")


if __name__ == "__main__":
    app()
