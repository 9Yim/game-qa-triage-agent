"""Step 0: send one real report to Claude and save the raw response.

Purpose is observation, not architecture. We want to see what the model
actually does before designing the pipeline around it.

Temporary script - will be replaced by src/triage/llm.py + extract.py.
"""

import json
import sys
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from triage.models import BugReport  # noqa: E402

load_dotenv(PROJECT_ROOT / ".env")

MODEL = "claude-haiku-4-5-20251001"
REPORT_ID = "sdv-002"

SYSTEM = (
    "You are a QA intake assistant for a video game studio. "
    "Extract only what the player actually wrote. "
    "If the report does not state something, leave that field empty. "
    "Never guess or fill in plausible-sounding values."
)

raw_text = (PROJECT_ROOT / "data" / "raw_real" / f"{REPORT_ID}.txt").read_text(
    encoding="utf-8"
)

client = Anthropic()

response = client.messages.create(
    model=MODEL,
    max_tokens=2000,
    system=SYSTEM,
    tools=[
        {
            "name": "record_bug_report",
            "description": "Record the structured bug report extracted from the player's post.",
            "input_schema": BugReport.model_json_schema(),
        }
    ],
    tool_choice={"type": "tool", "name": "record_bug_report"},
    messages=[{"role": "user", "content": raw_text}],
)

extracted = response.content[0].input

out_dir = PROJECT_ROOT / "runs"
out_dir.mkdir(exist_ok=True)
out_path = out_dir / f"{REPORT_ID}.raw.json"
out_path.write_text(
    json.dumps(
        {
            "model": MODEL,
            "report_id": REPORT_ID,
            "input_text": raw_text,
            "output": extracted,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)

print(json.dumps(extracted, ensure_ascii=False, indent=2))
print("\nsaved to", out_path)
print("tokens in/out:", response.usage.input_tokens, "/", response.usage.output_tokens)
