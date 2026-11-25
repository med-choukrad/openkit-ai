# Contributing to OpenKit AI

Thanks for considering a contribution.

## Getting started

1. Fork the repository and create a focused branch.
2. Set up a development environment:

   python -m venv .venv
   source .venv/bin/activate

   On Windows, activate with .venv\Scripts\activate.

3. Install development tools:

   python -m pip install -e ".[dev]"

4. Run the checks:

   python -m pytest
   ruff check .

5. Open a pull request describing the problem, solution, and tests.

## Contribution principles

- Keep the core package dependency-free where practical.
- Prefer small, composable functions with clear type hints.
- Include tests for bug fixes and new behavior.
- Never include API keys, credentials, or private user data.
- Be respectful and constructive in discussions.

Contributions are made under the repository's MIT license.
