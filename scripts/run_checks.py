"""Run the deterministic checks over everything already stored in runs/.

Calls no API, so it is free and instant: re-run it as often as you like.
"""

import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from triage.checks import check  # noqa: E402
from triage.models import BugReport  # noqa: E402

RUNS_DIR = PROJECT_ROOT / "runs"


def main() -> None:
    files = sorted(RUNS_DIR.glob("sdv-[0-9][0-9][0-9].json"))
    if not files:
        print(f"no runs found in {RUNS_DIR} - run scripts/run_all.py first")
        return

    n_quotes = n_grounded = 0
    n_covered = n_uncovered = 0
    all_unknown: list[str] = []
    all_unexpected: list[str] = []
    missing_tally: Counter[str] = Counter()

    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        report = BugReport(**data["fields"])
        result = check(report, data["input_text"])

        n_quotes += len(result.quotes)
        n_grounded += result.n_grounded
        n_covered += len(result.covered)
        n_uncovered += len(result.uncovered)
        all_unknown += result.unknown_fields
        all_unexpected += result.unexpected
        missing_tally.update(result.missing)

        coverage = "  -  " if result.coverage is None else f"{result.coverage:.0%}"
        print(
            f"{data['source']['source_id']}  "
            f"grounded {result.n_grounded}/{len(result.quotes)}  "
            f"cov {coverage:>5}  "
            f"missing: {', '.join(result.missing) or '-'}"
        )

        for q in result.quotes:
            if not q.grounded:
                print(f"           REWRITTEN  {q.raw_field}: {q.quote[:80]}")

    total_cov = n_covered + n_uncovered
    print("\n" + "-" * 60)
    print(f"quotes            : {n_quotes}")
    print(f"  grounded        : {n_grounded} ({n_grounded / n_quotes:.0%})")
    print(f"  rewritten       : {n_quotes - n_grounded}")
    print(f"evidence coverage : {n_covered}/{total_cov} ({n_covered / total_cov:.0%})")
    print(f"unknown field names: {len(all_unknown)}")
    print(f"quotes for fields we did not ask about: {len(all_unexpected)}")

    print(f"\nfields the player never mentioned, across {len(files)} reports:")
    for name, count in missing_tally.most_common():
        print(f"  {name:<22}{count:>3}")


if __name__ == "__main__":
    main()
