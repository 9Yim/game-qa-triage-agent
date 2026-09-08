"""Read a stored player report and turn it into a validated BugReport."""

from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from .llm import extract_bug_report
from .models import BugReport, ReportSource


@dataclass
class ExtractionResult:
    """Everything one extraction produced, successful or not."""

    source: ReportSource
    raw_text: str
    report: BugReport | None      # None when validation failed
    error: str | None             # the validation error, if any
    fields: dict                  # what the model returned, before validation
    usage: dict


def load_report(path: Path) -> tuple[ReportSource, str]:
    """One .txt file -> its source metadata and its full text."""
    return ReportSource(source_id=path.stem), path.read_text(encoding="utf-8").strip()


def load_all(directory: Path) -> list[tuple[ReportSource, str]]:
    """Every .txt file in a directory, in file-name order."""
    return [load_report(p) for p in sorted(directory.glob("*.txt"))]


def extract(source: ReportSource, raw_text: str) -> ExtractionResult:
    """Send one report to the model and validate the answer."""
    fields, usage = extract_bug_report(raw_text)

    report = None
    error = None
    try:
        report = BugReport(**fields)
    except ValidationError as exc:
        error = str(exc)

    return ExtractionResult(
        source=source,
        raw_text=raw_text,
        report=report,
        error=error,
        fields=fields,
        usage=usage,
    )
