"""Derived series for reporting (not used for training in this module)."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pandas as pd

from pipeline import config
from pipeline.data import load_combined


def rolling_load_stats(window_hours: int = 24 * 7) -> dict:
    df = load_combined()
    s = df["total load actual"].dropna()
    roll = s.rolling(window_hours, center=True)
    out = pd.DataFrame(
        {
            "rolling_mean_mw": roll.mean(),
            "rolling_std_mw": roll.std(),
        }
    ).dropna()
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "window_hours": window_hours,
        "rolling_mean_latest_mw": float(out["rolling_mean_mw"].iloc[-1]),
        "rolling_std_latest_mw": float(out["rolling_std_mw"].iloc[-1]),
        "rolling_mean_series_mean_mw": float(out["rolling_mean_mw"].mean()),
    }


def write_rolling_report(path=None) -> None:
    path = path or config.ROLLING_JSON
    obj = rolling_load_stats()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
