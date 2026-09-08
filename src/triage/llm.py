"""Thin wrapper around the Anthropic API for structured extraction.

This module only talks to the model. It does not validate what comes back -
that is extract.py's job.
"""

from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

from .models import BugReport

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 2000
TOOL_NAME = "record_bug_report"

SYSTEM = (
    "You are a QA intake assistant for a video game studio. "
    "Extract only what the player actually wrote. "
    "If the report does not state something, leave that field empty. "
    "Never guess or fill in plausible-sounding values."
)

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
client = Anthropic()


def extract_bug_report(raw_text: str) -> tuple[dict, dict]:
    """Send one raw player report to the model.

    Returns (fields, usage). `fields` is the raw dict the model produced;
    it is NOT yet validated against BugReport.
    """
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM,
        tools=[
            {
                "name": TOOL_NAME,
                "description": (
                    "Record the structured bug report extracted from the player's post."
                ),
                "input_schema": BugReport.model_json_schema(),
            }
        ],
        tool_choice={"type": "tool", "name": TOOL_NAME},
        messages=[{"role": "user", "content": raw_text}],
    )

    usage = {
        "model": MODEL,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }
    return response.content[0].input, usage
