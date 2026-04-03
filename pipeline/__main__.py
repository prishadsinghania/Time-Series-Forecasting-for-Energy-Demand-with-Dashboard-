from __future__ import annotations

import argparse
import sys

from pipeline import config
from pipeline.data import (
    build_data_quality_report,
    build_dataset_summary,
    load_combined,
    validate_modeling_inputs,
    validate_raw_inputs,
    write_json,
)
from pipeline.features import write_rolling_report
from pipeline.quick_models import write_metrics_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate data and write report artifacts.")
    parser.add_argument(
        "--skip-models",
        action="store_true",
        help="Skip sklearn quick baselines (faster).",
    )
    args = parser.parse_args(argv)

    raw_errs = validate_raw_inputs()
    if raw_errs:
        print("Raw file check:")
        for e in raw_errs:
            print(f"  - {e}")

    mod_errs = validate_modeling_inputs()
    if mod_errs:
        for e in mod_errs:
            print(e, file=sys.stderr)
        return 1

    df = load_combined()
    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    write_json(config.SUMMARY_JSON, build_dataset_summary(df))
    write_json(config.QUALITY_JSON, build_data_quality_report(df))
    write_rolling_report()
    print(f"Wrote {config.SUMMARY_JSON.name}, {config.QUALITY_JSON.name}, rolling_load.json")

    if not args.skip_models:
        write_metrics_report()
        print(f"Wrote {config.METRICS_JSON.name}")

    print(f"Done. Reports: {config.REPORTS_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
