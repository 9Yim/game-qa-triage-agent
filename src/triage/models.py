"""The three records this project passes around.

    ReportSource - where a report came from; filled by me
    Evidence     - the sentence the model used to justify one extracted field
    BugReport    - the facts the model extracted

What reaches the model: field names, types, Field(description=...) and each
CLASS docstring - all of them end up in the JSON schema sent with the request.
`#` comments do not. Changing any of the former changes the prompt.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class ReportSource(BaseModel):
    """Platform is inferred from the source, no llm involved"""

    source_id: str
    platform: Literal["PC_Steam", "PS5", "Xbox", "Switch", "Mobile"] = "PC_Steam"
    posted_at: Optional[str] = None


class Evidence(BaseModel):
    """The sentence the model used to justify one extracted field."""

    # `field` stays a plain str on purpose: a wrong field name should not fail
    # the whole record. checks.py normalises names when comparing instead.

    field: str = Field(description="Name of the field this evidence supports, e.g. actual_result.")

    quote: str = Field(
        description="The sentence from the original report that supports this value. Copy it verbatim - do not paraphrase, reword, or translate."
    )


class BugReport(BaseModel):
    """Facts extracted from a single player bug report."""

    title: str = Field(description="One-sentence summary of the problem, at most 15 words.")

    build_version: Optional[str] = Field(
        default=None, description="Game build version, e.g. 1.6.14. Leave empty if the report does not mention it."
    )

    repro_steps: list[str] = Field(
        default_factory=list, description="Steps to reproduce, one step per item. Empty list if the report describes none."
    )

    actual_result: str = Field(description="What actually happened.")

    expected_result: Optional[str] = Field(
        default=None, description="What the player expected to happen instead. Leave empty if not stated."
    )

    attempted_solutions: list[str] = Field(
        default_factory=list,
        description="Fixes the player says they have already tried, one per item. Empty list if none are mentioned.",
    )

    frequency: Literal["always", "often", "rare", "once", "unknown"] = Field(
        description="How often the problem occurs."
    )

    evidence: list[Evidence] = Field(
        default_factory=list,
        # Only fields that can be quoted word-for-word are listed here.
        # frequency and expected_result are inferred rather than copied

        # Keep this list in sync when adding fields to this model.
        description=(
            "Provide evidence for these fields when they are not empty: "
            "build_version, repro_steps, actual_result, attempted_solutions. "
            "One entry covering the whole list is enough for repro_steps. "
            "Do not provide evidence for any other field."
        ),
    )

    extraction_confidence: float = Field(
        ge=0.0, le=1.0, description="How confident you are in this extraction, from 0 to 1."
    )
