"""Example: safely parse a JSON object returned in an AI response."""

from openkit_ai import JSONResponseError, parse_json_response

model_response = """
Here is the structured result:
{"summary": "The task completed successfully.", "tags": ["example", "openkit"]}
"""

try:
    result = parse_json_response(model_response)
except JSONResponseError as error:
    print(f"Could not parse model output: {error}")
else:
    print(result["summary"])
    print(", ".join(result["tags"]))
