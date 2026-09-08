"""Deterministic checks over one extracted report.

Nothing here calls the model, so the same input always gives the same verdict.

Quotes are matched as whole substrings after normalising both sides. Whole
substrings, because a model can splice two distant fragments into a sentence
made entirely of the author's own words.
"""

import re
import unicodedata

from dataclasses import dataclass

from .models import BugReport

# Fields the model is asked to support with a quote.
# Keep in sync with the evidence description in models.py.
QUOTABLE_FIELDS = (
    "build_version",
    "repro_steps",
    "actual_result",
    "attempted_solutions",
)

# Fields a player may simply never mention. Empty is a finding, not an error.
OPTIONAL_FIELDS = (
    "build_version",
    "repro_steps",
    "expected_result",
    "attempted_solutions",
)

_FIELD_BY_SHAPE = {
    re.sub(r"[^a-z0-9]", "", name.lower()): name for name in BugReport.model_fields
}


def normalise(text: str) -> str:
    """Fold away differences that are typography rather than meaning."""
    text = unicodedata.normalize("NFKC", text)
    for fancy, plain in (("’", "'"), ("‘", "'"),
                         ("“", '"'), ("”", '"'),
                         ("–", "-"), ("—", "-")):
        text = text.replace(fancy, plain)
    return re.sub(r"\s+", " ", text).strip().lower()


def canonical_field(name: str) -> str | None:
    """Map a loosely written field name onto a real one, or None if unknown.

    "actualResult", "Actual Result" and "actual_result" all resolve to the same
    field. The model's original wording stays untouched in the stored run.
    """
    return _FIELD_BY_SHAPE.get(re.sub(r"[^a-z0-9]", "", name.lower()))


def has_value(value) -> bool:
    """True when the model actually filled this field in."""
    return value not in (None, "", [], {})


@dataclass
class QuoteCheck:
    """The verdict on one quote the model supplied."""

    raw_field: str          # exactly what the model wrote
    field: str | None       # the real field it maps to, None if unrecognised
    quote: str
    grounded: bool          # found in the source after normalising both sides


@dataclass
class CheckResult:
    """Everything the deterministic checks found for one report."""

    quotes: list[QuoteCheck]
    covered: list[str]          # quotable fields backed by at least one grounded quote
    uncovered: list[str]        # quotable fields with a value but no grounded quote
    missing: list[str]          # optional fields the report left empty
    unexpected: list[str]       # quotes for fields we did not ask about
    unknown_fields: list[str]   # quote field names that match nothing

    @property
    def n_grounded(self) -> int:
        return sum(q.grounded for q in self.quotes)

    @property
    def coverage(self) -> float | None:
        total = len(self.covered) + len(self.uncovered)
        return len(self.covered) / total if total else None


def check(report: BugReport, raw_text: str) -> CheckResult:
    """Run every deterministic check over one extracted report."""
    normalised_source = normalise(raw_text)

    quotes: list[QuoteCheck] = []
    quoted_fields: set[str] = set()
    unexpected: list[str] = []
    unknown_fields: list[str] = []

    for item in report.evidence:
        resolved = canonical_field(item.field)
        quotes.append(
            QuoteCheck(
                raw_field=item.field,
                field=resolved,
                quote=item.quote,
                grounded=normalise(item.quote) in normalised_source,
            )
        )
        if resolved is None:
            unknown_fields.append(item.field)
        else:
            # A rewritten quote is not support. Only grounded quotes count as
            # coverage, otherwise a fabricated quote would make a field look
            # backed up.
            if quotes[-1].grounded:
                quoted_fields.add(resolved)
            if resolved not in QUOTABLE_FIELDS:
                unexpected.append(resolved)

    covered, uncovered = [], []
    for name in QUOTABLE_FIELDS:
        if has_value(getattr(report, name)):
            (covered if name in quoted_fields else uncovered).append(name)

    missing = [n for n in OPTIONAL_FIELDS if not has_value(getattr(report, n))]

    return CheckResult(
        quotes=quotes,
        covered=covered,
        uncovered=uncovered,
        missing=missing,
        unexpected=unexpected,
        unknown_fields=unknown_fields,
    )
