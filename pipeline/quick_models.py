from __future__ import annotations

import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from pipeline import config

TARGET = "total load actual"
DROP_FOR_FEATURES = [
    "total load actual",
    "total load forecast",
    "price day ahead",
    "price actual",
]


def _feature_matrix(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    y = df[TARGET]
    X = df.drop(columns=[c for c in DROP_FOR_FEATURES if c in df.columns], errors="ignore")
    X = X.select_dtypes(include=[np.number]).ffill().bfill()
    mask = y.notna() & X.notna().all(axis=1)
    return X.loc[mask], y.loc[mask]


def run_quick_baselines(test_size: float = 0.15, random_state: int = 42) -> dict:
    """Temporal-style holdout via ordered split (last test_size fraction as test)."""
    df = pd.read_csv(config.COMBINED, index_col="time", parse_dates=True)
    X, y = _feature_matrix(df)
    n = len(X)
    split = int(n * (1 - test_size))
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    results = []
    for name, model in [
        ("linear_regression", LinearRegression()),
        (
            "random_forest_quick",
            RandomForestRegressor(
                n_estimators=80,
                max_depth=12,
                random_state=random_state,
                n_jobs=-1,
            ),
        ),
    ]:
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
        mae = float(mean_absolute_error(y_test, pred))
        results.append(
            {
                "model": name,
                "rmse_mw": round(rmse, 2),
                "mae_mw": round(mae, 2),
                "test_rows": int(len(y_test)),
                "feature_count": int(X.shape[1]),
            }
        )

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "split": "chronological_last_fraction",
        "test_fraction": test_size,
        "note": "Quick sklearn baselines on numeric exogenous + generation columns; "
        "full study uses notebooks (Prophet, SARIMAX, XGBoost, search CV).",
        "results": results,
    }


def append_notebook_models_stub() -> dict:
    """Placeholder rows for models evaluated only in Modeling.ipynb (fill after runs)."""
    return {
        "notebook_models": [
            {
                "model": "year_over_year_baseline",
                "rmse_mw": None,
                "note": "See Modeling.ipynb — repeat prior-year load.",
            },
            {
                "model": "prophet_exogenous",
                "rmse_mw": None,
                "note": "See Modeling.ipynb — primary long-horizon candidate.",
            },
            {
                "model": "xgboost",
                "rmse_mw": None,
                "note": "See Modeling.ipynb — tuned gradient boosting.",
            },
            {
                "model": "sarimax_fourier",
                "rmse_mw": None,
                "note": "See Modeling.ipynb — shorter horizons with Fourier exog.",
            },
        ]
    }


def write_metrics_report() -> None:
    report = run_quick_baselines()
    report.update(append_notebook_models_stub())
    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(config.METRICS_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
