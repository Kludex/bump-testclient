import contextlib
import time
from os import devnull
from pathlib import Path
from typing import List

from libcst.codemod import CodemodContext, parallel_exec_transform_with_prettyprint
from packaging import version
from typer import Argument, Exit, Typer, secho

from bump_testclient.command import BumpTestClientCommand

app = Typer(add_completion=False)


@app.command()
def command(
    files: List[Path] = Argument(..., exists=True, dir_okay=True, allow_dash=True)
) -> None:
    """Replace Starlette's old TestClient (<0.21.0) by the new one (>=0.21.0)."""
    try:
        import httpx
    except ModuleNotFoundError:
        secho("You need to install httpx to bump.", fg="red", err=True)
        raise Exit(1)

    if version.parse(httpx.__version__) < version.parse("0.22.0"):
        secho("You need to install httpx >=0.22.0 to bump.", fg="red", err=True)
        raise Exit(1)

    transformer = BumpTestClientCommand(CodemodContext())
    start_time = time.time()

    with open(devnull, "w") as null:
        with contextlib.redirect_stderr(null):
            parallel_exec_transform_with_prettyprint(
                transformer,
                [str(file) for file in files],
                include_generated=True,
                show_successes=True,
                jobs=1,
            )

    modified = [f for f in files if f.stat().st_mtime > start_time]
    for file in modified:
        secho(f"refactored {file.relative_to('.')}", bold=True)

    if modified:
        raise Exit(1)


if __name__ == "__main__":
    app()
