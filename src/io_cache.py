import os, json, time
from pathlib import Path
from typing import Any, Optional, Dict, List
import pandas as pd

def ensure_dir(p: str):
    Path(p).mkdir(parents=True, exist_ok=True)

def save_json(obj: Any, path: str):
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def load_json(path: str) -> Optional[dict]:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_csv(df: pd.DataFrame, path: str, index: bool=False):
    ensure_dir(os.path.dirname(path))
    df.to_csv(path, index=index, encoding="utf-8")

def load_csv(path: str) -> Optional[pd.DataFrame]:
    if not os.path.exists(path):
        return None
    return pd.read_csv(path, encoding="utf-8")

def timestamp() -> str:
    import datetime as dt
    return dt.datetime.utcnow().isoformat() + "Z"
