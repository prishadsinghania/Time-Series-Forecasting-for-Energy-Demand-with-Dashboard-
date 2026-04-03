# Notebooks

Run **in this order** (after `pip install -r requirements.txt` and `pip install -e .` from the repo root):

1. `Data_Wrangling.ipynb`
2. `Exploratory_Data_Analysis.ipynb`
3. `Pre-Processing.ipynb`
4. `Modeling.ipynb`

Use a Jupyter kernel from the same virtualenv where the package is installed so `from energy_forecast.notebook_setup import DATA` resolves and `DATA` points at the repository `data/` folder.
