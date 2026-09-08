"""One-off check: does the API key in .env work?

Run once after creating .env. Not part of the pipeline.
"""

from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

# Load .env from the project root, no matter where this script is run from.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

client = Anthropic()

# 1) Which models can this key reach? Free, costs no tokens.
models = client.models.list()
print("Available models:")
for m in models.data:
    print("  ", m.id)

# 2) Pick the cheapest tier available, then send the shortest possible request.
model_id = models.data[0].id
for m in models.data:
    if "haiku" in m.id:
        model_id = m.id
        break

print(f"\nCalling {model_id} ...")
response = client.messages.create(
    model=model_id,
    max_tokens=20,
    messages=[{"role": "user", "content": "Reply with exactly: key works"}],
)

print("Reply:", response.content[0].text)
print("Tokens in/out:", response.usage.input_tokens, "/", response.usage.output_tokens)
