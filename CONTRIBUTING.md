# Contributing

Thanks for your interest in improving this project.

## Development Setup

1. Fork and clone the repository.
2. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install "mcp[cli]>=1.6.0" "httpx>=0.28.1"
```

4. Ensure Audacity has `mod-script-pipe` enabled and is running.

## Running Locally

```bash
python audacity_mcp_server.py
```

## Pull Request Guidelines

- Keep changes focused and minimal.
- Update documentation when behavior changes.
- Add or update tests/checks when practical.
- Keep commit messages clear and specific.

## Reporting Bugs / Requesting Features

- Use GitHub Issues and include reproducible steps.
- For security-sensitive problems, follow `SECURITY.md` and avoid public disclosure.
