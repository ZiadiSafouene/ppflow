import pandas as pd
import numpy as np
from scipy.stats import skew, kurtosis
from .models import DatasetIdentity
from .text import profile_structured_text

COMMON_ENCODINGS = ["utf-8", "latin-1", "cp1252"]

def safe_read_csv(path, nrows=5000):
    last_error = None
    for enc in COMMON_ENCODINGS:
        try:
            return pd.read_csv(path, encoding=enc, nrows=nrows), enc
        except UnicodeDecodeError as e:
            last_error = e
    raise last_error

def identify_tabular_dataset(files, root):
    file = next(f for f in files if f.suffix.lower() in {".csv", ".tsv", ".json"})
    df, encoding = safe_read_csv(file, nrows=5000)

    form = detect_tabular_form(df)
    profile = profile_tabular(df)
    profile["encoding"] = encoding

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

    n_rows = len(df)
    n_cols = len(df.columns)

    object_cols = df.select_dtypes(include=["object", "string"]).columns

    if n_cols <= 4 and len(object_cols) >= 1:
        id_candidates = [
            col for col in object_cols
            if df[col].nunique() < n_rows * 0.5
        ]

        numeric_cols = df.select_dtypes(include=np.number).columns

        if id_candidates and len(numeric_cols) == 1:
            return "long"

    return "wide"

def detect_time_series(df, sample_size=500, min_parse_ratio=0.8):
    candidates = []

    for col in df.columns:
        series = df[col].dropna()

        # Skip small or constant columns
        if series.nunique() < 10:
            continue

        # Sample for speed
        sample = series.astype(str).head(sample_size)

        parsed = pd.to_datetime(sample, errors="coerce", infer_datetime_format=True)

        parse_ratio = parsed.notna().mean()
        if parse_ratio < min_parse_ratio:
            continue

        parsed = parsed.dropna()

        # Must be mostly ordered
        monotonic_ratio = (parsed.diff().dropna() >= pd.Timedelta(0)).mean()
        if monotonic_ratio < 0.9:
            continue

        # Temporal spacing consistency
        deltas = parsed.sort_values().diff().dropna()
        if len(deltas) < 5:
            continue

        delta_std = deltas.std().total_seconds()
        delta_mean = deltas.mean().total_seconds()

        # Avoid random / categorical dates
        if delta_mean == 0 or delta_std / delta_mean > 1.0:
            continue

        candidates.append({
            "column": col,
            "parse_ratio": round(parse_ratio, 3),
            "monotonic_ratio": round(monotonic_ratio, 3),
            "mean_delta_seconds": round(delta_mean, 2),
            "delta_variability": round(delta_std / delta_mean, 3)
        })

    if not candidates:
        return None

    # Choose the most reliable candidate
    best = max(candidates, key=lambda x: (x["parse_ratio"], x["monotonic_ratio"]))

    return {
        "time_column": best["column"],
        "confidence": {
            "parse_ratio": best["parse_ratio"],
            "monotonic_ratio": best["monotonic_ratio"]
        },
        "temporal_resolution_seconds": best["mean_delta_seconds"]
    }


def classify_tabular_semantics(df):
    text_cols = []
    total_text_chars = 0

    for col in df.select_dtypes(include=["object", "string"]).columns:
        lengths = df[col].dropna().astype(str).str.len()
        if lengths.empty:
            continue

        avg_len = lengths.mean()
        uniqueness = df[col].nunique() / len(df)

        if avg_len >= 30 and uniqueness >= 0.5:
            text_cols.append(col)
            total_text_chars += lengths.sum()

    numeric_cols = df.select_dtypes(include=np.number).columns

    if not text_cols:
        return {
            "semantic_type": "numeric_tabular"
        }

    total_chars = sum(
        df[col].dropna().astype(str).str.len().sum()
        for col in df.select_dtypes(include=["object", "string"]).columns
    )

    text_ratio = total_text_chars / max(total_chars, 1)

    if text_ratio >= 0.4 and len(numeric_cols) <= 3:
        return {
            "semantic_type": "nlp_tabular",
            "text_columns": text_cols,
            "text_detail": profile_structured_text(df)

        }

    return {
        "semantic_type": "numeric_tabular"
    }

def assess_tabular_quality(df):
    quality = {}

    # Missing values
    missing = df.isna().mean()
    quality["high_missing_columns"] = missing[missing > 0.3].index.tolist()

    # Constant columns
    quality["constant_columns"] = [
        col for col in df.columns if df[col].nunique() <= 1
    ]

    # Duplicate rows
    dup_ratio = df.duplicated().mean()
    if dup_ratio > 0:
        quality["duplicate_row_ratio"] = float(dup_ratio)

    # NLP-specific noise
    text_cols = df.select_dtypes(include=["object", "string"]).columns
    empty_text = [
        col for col in text_cols
        if (df[col].astype(str).str.strip() == "").mean() > 0.1
    ]

    if empty_text:
        quality["empty_text_columns"] = empty_text

    return quality

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
        col for col in df.columns if df[col].map(type).nunique() > 1
    ]

    ts = detect_time_series(df)
    # if ts:
    #     profile["time_series"] = ts
    
    profile.update(classify_tabular_semantics(df))
    profile["quality"] = assess_tabular_quality(df)

    return profile
