# Contributing to Pandora Bot

Thank you for your interest! Here's how to get started.

## Development Setup

1. Fork and clone the repository.
2. Create a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS / Linux

pip install -r requirements.txt
pip install -r requirements-dev.txt
```

3. Copy `.env.example` → `.env` and fill in test credentials.

## Code Standards

- **Python 3.11+**
- **Linter:** [Ruff](https://docs.astral.sh/ruff/) — `ruff check bot.py`
- **Tests:** [pytest](https://docs.pytest.org/) — all changes must include tests
- **Async:** use `async/await` for I/O

## Pull Request Process

1. Branch from `main`: `git checkout -b feat/your-feature`
2. Make clear, atomic commits.
3. Run tests: `pytest tests/ -v`
4. Run linter: `ruff check bot.py`
5. Open a PR with a clear description.

## Adding New Intents

Edit `intents.json` — no code changes needed. The bot loads intents at startup.

## Reporting Issues

Use GitHub Issues. Include steps to reproduce, expected vs actual behavior.

## Code of Conduct

Be respectful. This project follows the [Contributor Covenant](https://www.contributor-covenant.org/).
