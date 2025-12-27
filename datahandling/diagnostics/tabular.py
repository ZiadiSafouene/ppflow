import pandas as pd
import numpy as np
from scipy.stats import skew
from pathlib import Path
from .base import Issue


class DuplicateRowsIssue(Issue):
    id = "duplicate_rows"
    severity = "low"

    def __init__(self, count):
        self.count = count
        self.description = f"{count} duplicate rows detected"
        self.fix_description = "Remove duplicate rows"

    def apply_fix(self, input_path, output_path):
        df = pd.read_csv(input_path)
        df = df.drop_duplicates()
        df.to_csv(output_path, index=False)

def detect_duplicates(df):
    n = df.duplicated().sum()
    return DuplicateRowsIssue(n) if n > 0 else None


class MixedTypeIssue(Issue):
    id = "mixed_types"
    severity = "medium"

    def __init__(self, column):
        self.column = column
        self.description = f"Mixed data types in column '{column}'"
        self.fix_description = "Cast column to dominant type"

    def apply_fix(self, input_path, output_path):
        df = pd.read_csv(input_path)
        dominant = df[self.column].dropna().map(type).mode()[0]
        df[self.column] = df[self.column].apply(
            lambda x: dominant(x) if not pd.isna(x) else x
        )
        df.to_csv(output_path, index=False)

def detect_mixed_types(df):
    issues = []
    for col in df.columns:
        if df[col].map(type).nunique() >= 2:
            issues.append(MixedTypeIssue(col))
    return issues

class ConstantColumnIssue(Issue):
    id = "constant_column"
    severity = "low"

    def __init__(self, column):
        self.column = column
        self.description = f"Constant or near-constant column '{column}'"
        self.fix_description = "Drop column"

    def apply_fix(self, input_path, output_path):
        df = pd.read_csv(input_path)
        df = df.drop(columns=[self.column])
        df.to_csv(output_path, index=False)

def detect_constant_columns(df):
    issues = []
    for col in df.columns:
        if df[col].nunique(dropna=True) <= 1:
            issues.append(ConstantColumnIssue(col))
    return issues


class SkewedDistributionIssue(Issue):
    id = "skewed_distribution"
    severity = "low"

    def __init__(self, column, value):
        self.column = column
        self.value = value
        self.description = f"Highly skewed column '{column}' (skew={value:.2f})"
        self.fix_description = "Apply log1p transform"

    def apply_fix(self, input_path, output_path):
        df = pd.read_csv(input_path)
        df[self.column] = np.log1p(df[self.column].clip(lower=0))
        df.to_csv(output_path, index=False)


def detect_skewness(df):
    issues = []
    for col in df.select_dtypes(include=np.number):
        if is_binary_numeric(df[col]): # ← CRITICAL FIX
            continue
        s = skew(df[col].dropna())
        if abs(s) > 2:
            issues.append(SkewedDistributionIssue(col, s))
    return issues


class NLPColumnIssue(Issue):
    id = "nlp_column"
    severity = "medium"

    def __init__(self, column):
        self.column = column
        self.description = f"Column '{column}' appears to be NLP text"
        self.fix_description = "Mark column as text (no numeric ops)"

    def apply_fix(self, input_path, output_path):
        df = pd.read_csv(input_path)
        df[self.column] = df[self.column].astype(str)
        df.to_csv(output_path, index=False)


def detect_nlp_columns(df):
    issues = []
    for col in df.select_dtypes(include="object"):
        avg_len = df[col].dropna().astype(str).str.split().map(len).mean()
        if avg_len and avg_len > 5:
            issues.append(NLPColumnIssue(col))
    return issues



class MissingValuesIssue(Issue):
    id = "missing_values"
    severity = "warning"

    def __init__(self, column: str, count: int):
        self.column = column
        self.count = count
        self.description = f"Column '{column}' has {count} missing values"
        self.fix_description = f"Fill missing values in '{column}'"

    def apply_fix(self, input_path, output_path):
        df = pd.read_csv(input_path)

        if pd.api.types.is_numeric_dtype(df[self.column]):
            df[self.column] = df[self.column].fillna(df[self.column].mean())
        else:
            df[self.column] = df[self.column].fillna("MISSING")

        df.to_csv(output_path, index=False)

def detect_missing_values(df):
    issues = []
    for col in df.columns:
        n_missing = df[col].isna().sum()
        if n_missing > 0:
            issues.append(MissingValuesIssue(col, n_missing))
    return issues

from scipy.stats import zscore
class OutliersIssue(Issue):
    id = "outliers"
    severity = "warning"

    def __init__(self, column: str, count: int, threshold: float):
        self.column = column
        self.count = count
        self.threshold = threshold
        self.description = f"Column '{column}' has {count} outliers (z > {threshold})"
        self.fix_description = f"Replace outliers in '{column}' with mean"

    def apply_fix(self, input_path, output_path):
        df = pd.read_csv(input_path)

        series = df[self.column]
        mean = series.mean()
        std = series.std()

        if std == 0 or pd.isna(std):
            df.to_csv(output_path, index=False)
            return

        z = (series - mean) / std
        df[self.column] = np.where(np.abs(z) > self.threshold, mean, series)

        df.to_csv(output_path, index=False)

def is_binary_numeric(series):
    vals = series.dropna().unique()
    return len(vals) <= 2 

def detect_outliers(df, threshold=3.0):
    issues = []

    for col in df.select_dtypes(include=np.number).columns:
        if is_binary_numeric(df[col]):
            continue  # ← CRITICAL FIX
        series = df[col].dropna()
        if series.std() == 0 or len(series) < 5:
            continue

        z = (series - series.mean()) / series.std()
        n_outliers = int((np.abs(z) > threshold).sum())

        if n_outliers > 0:
            issues.append(OutliersIssue(col, n_outliers, threshold))

    return issues


class NonNormalizedColumnIssue(Issue):
    id = "non_normalized"
    severity = "info"

    def __init__(self, column: str, col_range: float):
        self.column = column
        self.col_range = col_range
        self.description = (
            f"Column '{column}' has a large range ({col_range:.2f}), not normalized"
        )
        self.fix_description = f"Normalize '{column}' to [0,1]"

    def apply_fix(self, input_path, output_path):
        df = pd.read_csv(input_path)

        col_min = df[self.column].min()
        col_max = df[self.column].max()

        if col_max == col_min:
            df.to_csv(output_path, index=False)
            return

        df[self.column] = (df[self.column] - col_min) / (col_max - col_min)
        df.to_csv(output_path, index=False)

def detect_non_normalized(df, scale_threshold=100.0):
    issues = []

    for col in df.select_dtypes(include=np.number).columns:
        col_range = df[col].max() - df[col].min()
        if pd.notna(col_range) and col_range > scale_threshold:
            issues.append(NonNormalizedColumnIssue(col, col_range))

    return issues


def run_tabular_diagnostics(csv_path):
    df = pd.read_csv(csv_path)

    detectors = [
        detect_missing_values,
        detect_duplicates,
        detect_constant_columns,
        detect_mixed_types,
        detect_outliers,
        detect_non_normalized,
        detect_skewness,
        detect_nlp_columns
    ]

    issues = []

    for detect in detectors:
        found = detect(df)
        if isinstance(found, list):
            issues.extend(found)
        elif found is not None:
            issues.append(found)

    return issues