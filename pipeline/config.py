from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
REPORTS_DIR = REPO_ROOT / "reports"

RAW_ENERGY = DATA_DIR / "energy_dataset.csv"
RAW_WEATHER = DATA_DIR / "weather_features.csv"
COMBINED = DATA_DIR / "combined_avg.csv"

SUMMARY_JSON = REPORTS_DIR / "dataset_summary.json"
QUALITY_JSON = REPORTS_DIR / "data_quality.json"
METRICS_JSON = REPORTS_DIR / "model_metrics.json"
ROLLING_JSON = REPORTS_DIR / "rolling_load.json"
