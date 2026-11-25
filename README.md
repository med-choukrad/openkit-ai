# OpenKit AI

Small, dependency-free utilities for developers building AI-powered Python applications.

OpenKit AI starts with two practical building blocks:

- **JSON response parsing** — extract a valid JSON object or array from plain model output, Markdown code fences, or text with surrounding explanation.
- **Retry with exponential backoff** — retry transient failures such as timeouts and connection errors without adding a third-party runtime dependency.

The project is intentionally small and vendor-neutral. It does not call an AI service, collect data, or require API keys.

## Installation

Python 3.10 or newer is required.

```bash
python -m pip install openkit-ai
```

## Quick start

```python
from openkit_ai import parse_json_response, call_with_retry

data = parse_json_response('Model output: {"sentiment": "positive"}')
print(data["sentiment"])

result = call_with_retry(
    lambda: make_your_api_call(),
    retry_on=(TimeoutError, ConnectionError),
    max_attempts=3,
)
```

See [examples/parse_model_json.py](examples/parse_model_json.py) for a complete parsing example.

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest
ruff check .
```

## Project status

OpenKit AI is in early development. The public API may evolve before the first stable release. Bug reports, focused feature proposals, documentation improvements, and tested pull requests are welcome.

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

## License

MIT. See [LICENSE](LICENSE).
