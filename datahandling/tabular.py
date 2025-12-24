import pandas as pd
import numpy as np
from scipy.stats import skew, kurtosis
from .models import DatasetIdentity

def identify_tabular_dataset(files, root):
    file = next(f for f in files if f.suffix.lower() in {".csv", ".tsv", ".json"})
    df = pd.read_csv(file, nrows=5000)

    form = detect_tabular_form(df)
    profile = profile_tabular(df)

    return DatasetIdentity(
        root=root,
        container_type="table",
        structural_form=form,
        details=profile
    )

def detect_tabular_form(df):
    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, (list, dict))).any():
            return "nested"

    if df.select_dtypes(include=["object"]).nunique().min() < len(df) * 0.05:
        return "long"

    return "wide"

def detect_time_series(df):
    for col in df.columns:
        parsed = pd.to_datetime(df[col], errors="coerce")
        if parsed.notna().mean() > 0.8:
            return {
                "time_column": col,
                "monotonic": parsed.is_monotonic_increasing
            }
    return None

def profile_tabular(df):
    profile = {}

    numeric = df.select_dtypes(include=np.number)
    profile["stats"] = {
        col: {
            "skewness": float(skew(df[col].dropna())),
            "kurtosis": float(kurtosis(df[col].dropna()))
        }
        for col in numeric
    }

    profile["type_mismatches"] = [
        col for col in df.columns if df[col].map(type).nunique() > 3
    ]

    ts = detect_time_series(df)
    if ts:
        profile["time_series"] = ts

    return profile
