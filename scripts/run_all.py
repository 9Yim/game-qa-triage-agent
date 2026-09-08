"""Extract every report in data/raw_real/ and save the results to runs/."""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from triage.extract import extract, load_all  # noqa: E402

RAW_DIR = PROJECT_ROOT / "data" / "raw_real"
OUT_DIR = PROJECT_ROOT / "runs"


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    reports = load_all(RAW_DIR)
    print(f"{len(reports)} reports found in {RAW_DIR.name}/\n")

    total_in = total_out = 0
    failures = 0

    for source, raw_text in reports:
        result = extract(source, raw_text)
        total_in += result.usage["input_tokens"]
        total_out += result.usage["output_tokens"]

        if result.report is None:
            failures += 1
            status = "SCHEMA FAIL"
            summary = result.error.splitlines()[0]
        else:
            r = result.report
            status = "ok"
            summary = (
                f"conf={r.extraction_confidence:.2f} "
                f"freq={r.frequency:<7} "
                f"version={r.build_version or '-':<10} "
                f"steps={len(r.repro_steps)} "
                f"tried={len(r.attempted_solutions)} "
                f"evidence={len(r.evidence)}"
            )

        print(f"{source.source_id}  {status:<11} {summary}")

        (OUT_DIR / f"{source.source_id}.json").write_text(
            json.dumps(
                {
                    "source": source.model_dump(),
                    "input_text": raw_text,
                    "fields": result.fields,
                    "error": result.error,
                    "usage": result.usage,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    print(
        f"\n{len(reports) - failures}/{len(reports)} validated  |  "
        f"tokens in/out: {total_in} / {total_out}"
    )


if __name__ == "__main__":
    main()
