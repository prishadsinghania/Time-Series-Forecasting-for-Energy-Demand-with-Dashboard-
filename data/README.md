# Data directory

| File | Role |
|------|------|
| `energy_dataset.csv` | Raw hourly system generation, load, prices (Kaggle export). |
| `weather_features.csv` | Raw hourly weather features for multiple cities. |
| `energy_data.csv` | Produced by `notebooks/Data_Wrangling.ipynb` (cleaned energy table). |
| `weather_wide.csv` | Wide-format weather (wrangling). |
| `weather_avg.csv` | City-averaged weather (wrangling). |
| `combined_avg.csv` | Energy + averaged weather, merged in EDA notebook; used by preprocessing, modeling, dashboard, and pipeline. |

Large CSVs are tracked here so the project runs after clone. Replace with your own exports if you refresh from Kaggle.
