# Pipeline CLI

From the **repository root**:

```bash
python3 -m pipeline          # full run (reports + quick sklearn models)
python3 -m pipeline --skip-models   # summary, quality, rolling stats only
```

Uses `data/combined_avg.csv`. Paths are resolved from this package’s location (`pipeline/config.py`), not from the current working directory.
