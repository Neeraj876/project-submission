import os
from pathlib import Path
import pandas as pd
import yaml
from django.conf import settings
from .models import DataRecord

def load_config(path_or_str):
    if os.path.exists(path_or_str):
        with open(path_or_str, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return yaml.safe_load(path_or_str)

def load_input_df(source):
    path = Path(source["path"])
    if not path.is_absolute():
        path = Path(settings.BASE_DIR) / path
    if source["type"] == "csv":
        return pd.read_csv(path)
    if source["type"] == "excel":
        return pd.read_excel(path)
    raise ValueError("Unsupported source type")

def apply_steps(df, steps):
    for step in steps:
        action = step["action"]
        if action == "select":
            df = df[step["columns"]]
        elif action == "filter":
            df = df.query(step["condition"])
        elif action == "rename":
            df = df.rename(columns=step["mapping"])
        elif action == "cast":
            for col, typ in step["mapping"].items():
                df[col] = df[col].astype(typ)
        elif action == "compute":
            df[step["column"]] = df.eval(step["expression"], engine="python")
        elif action == "dedupe":
            df = df.drop_duplicates()
        elif action == "sort":
            df = df.sort_values(by=step["columns"])
        else:
            raise ValueError(f"Unknown action: {action}")
    return df

def write_output(df, dest, run=None):
    if dest["type"] == "csv":
        out_path = Path(dest["path"])
        if not out_path.is_absolute():
            out_path = Path(settings.BASE_DIR) / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_path, index=False)
        return str(out_path)

    if dest["type"] == "db":
        if run is None:
            raise ValueError("run required for db output")
        for _, row in df.iterrows():
            DataRecord.objects.create(run=run, data=row.to_dict())
        return "db"

    raise ValueError("Unsupported destination")
