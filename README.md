# OpenKit AI

Small, dependency-free utilities for developers building AI-powered Python applications.

OpenKit AI currently provides three practical building blocks:

- **JSON response parsing** — extract a valid JSON object or array from plain model output, Markdown code fences, or text with surrounding explanation.
- **Retry with exponential backoff** — retry transient failures such as timeouts and connection errors.
- **Prompt templates** — define reusable prompts, inspect their required variables, and render them with strict input validation.

The project is vendor-neutral. It does not call an AI service, collect data, or require API keys at runtime.

## Installation

Python 3.10 or newer is required.

```bash
python -m pip install openkit-ai
```

## Quick start

```python
from openkit_ai import PromptTemplate, parse_json_response, call_with_retry

prompt = PromptTemplate("summary", "Summarize {text} for {audience}.")
rendered = prompt.render(text="the report", audience="engineers")
print(rendered)

data = parse_json_response('Model output: {"sentiment": "positive"}')
print(data["sentiment"])

result = call_with_retry(
    lambda: make_your_api_call(),
    retry_on=(TimeoutError, ConnectionError),
    max_attempts=3,
)
```

See the [examples](examples/) directory for complete usage examples.

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
