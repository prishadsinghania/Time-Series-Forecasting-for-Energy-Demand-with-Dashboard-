from __future__ import annotations

import json
from datetime import datetime, timezone

import pandas as pd

from pipeline import config


def load_combined(path=None) -> pd.DataFrame:
    p = path or config.COMBINED
    df = pd.read_csv(p, index_col="time", parse_dates=True)
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    return df.sort_index()


def validate_raw_inputs() -> list[str]:
    errors = []
    if not config.RAW_ENERGY.is_file():
        errors.append(f"Missing raw energy CSV: {config.RAW_ENERGY}")
    if not config.RAW_WEATHER.is_file():
        errors.append(f"Missing raw weather CSV: {config.RAW_WEATHER}")
    return errors


def validate_modeling_inputs() -> list[str]:
    errors = []
    if not config.COMBINED.is_file():
        errors.append(
            f"Missing combined dataset: {config.COMBINED}. "
            "Run notebooks in order: Data_Wrangling → Exploratory_Data_Analysis."
        )
    return errors


def build_dataset_summary(df: pd.DataFrame) -> dict:
    load = df["total load actual"]
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "row_count": int(len(df)),
        "time_start_utc": df.index.min().isoformat(),
        "time_end_utc": df.index.max().isoformat(),
        "columns": list(df.columns),
        "total_load_actual": {
            "mean_mw": float(load.mean()),
            "std_mw": float(load.std()),
            "min_mw": float(load.min()),
            "max_mw": float(load.max()),
        },
    }


def write_json(path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)


def build_data_quality_report(df: pd.DataFrame) -> dict:
    null_pct = (df.isna().mean() * 100).round(2)
    worst = null_pct.sort_values(ascending=False).head(15)
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "missing_pct_by_column": {str(k): float(v) for k, v in worst.items()},
        "duplicate_index_rows": int(df.index.duplicated().sum()),
    }
