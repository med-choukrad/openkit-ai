"""Example: keep and render a reusable prompt template."""

from openkit_ai import PromptTemplate

summary_prompt = PromptTemplate(
    name="concise-summary",
    template=(
        "Summarize the following text for {audience} in no more than "
        "{max_sentences} sentences:\n\n{text}"
    ),
)

print(
    summary_prompt.render(
        audience="a software engineering team",
        max_sentences=3,
        text="OpenKit AI provides small utilities for AI application developers.",
    )
)
