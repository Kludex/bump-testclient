<h1 align="center">
    <strong>bump-testclient</strong>
</h1>
<p align="center">
    <a href="https://pypi.org/project/bump-testclient" target="_blank">
        <img src="https://img.shields.io/pypi/v/bump-testclient" alt="Package version">
    </a>
    <img src="https://img.shields.io/pypi/pyversions/bump-testclient">
    <img src="https://img.shields.io/github/license/Kludex/bump-testclient">
</p>

Starlette 0.21.0 changed the `TestClient` implementation: it replaced the `requests` library with `httpx`.
As those libraries have different APIs, this change break tests for Starlette's users.

This [codemod](https://libcst.readthedocs.io/en/stable/codemods_tutorial.html) makes the transition to Starlette 0.21.0 easier.
It makes the changes needed to make the tests work again.

## Why?

Make your life easier. Suggested by [Sebastián Ramírez](https://twitter.com/tiangolo) as a joke, but well... I did it.

## Installation

```bash
pip install bump-testclient
```

## Usage

Run the following on the repository you want to format:

```bash
python -m bump_testclient <files>
```

You can also use the pre-commit. Add the following to your `.pre-commit-config.yaml` file:

```yaml
  - repo: https://github.com/Kludex/bump-testclient
    rev: 0.0.0
    hooks:
      - id: bump_testclient
```

## License

This project is licensed under the terms of the MIT license.
