import os
from pathlib import Path

import pandas as pd


def save_file(df: pd.DataFrame, filename: str, datapath: str | Path) -> None:
    """Write a DataFrame to CSV under datapath; create the directory if needed."""
    datapath = Path(datapath)
    os.makedirs(datapath, exist_ok=True)
    filepath = datapath / filename
    df.to_csv(filepath, index=False)
    print(f'Writing file.  "{filepath}"')
