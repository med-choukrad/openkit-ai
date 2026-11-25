"""Example: parse and validate structured data from an AI response."""

from openkit_ai import JSONValidationError, validate_json_response

model_response = """
Here is the user profile:
{"name": "Ada Lovelace", "age": 36, "tags": ["math", "computing"]}
"""

try:
    profile = validate_json_response(
        model_response,
        {"name": str, "age": int, "tags": list},
    )
except JSONValidationError as error:
    print(f"The model returned invalid data: {error}")
else:
    print(f"{profile['name']} is {profile['age']} years old.")
