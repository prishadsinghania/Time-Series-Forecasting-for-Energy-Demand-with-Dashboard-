"""Import this from notebooks: `from energy_forecast.notebook_setup import DATA, REPO`."""

from pathlib import Path

# Repository root (parent of this package directory)
REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
REPORTS = REPO / "reports"
