import pandas as pd
import numpy as np
from scipy.stats import skew
from pathlib import Path
from .base import Issue

class MissingValuesIssue(Issue):
    id = "missing_values"
    severity = "medium"

    def __init__(self, columns):
        self.columns = columns
        self.description = f"Missing values in columns: {columns}"
        self.fix_description = "Drop rows with missing values"

    def apply_fix(self, input_path, output_path):
        df = pd.read_csv(input_path)
        df = df.dropna(subset=self.columns)
        df.to_csv(output_path, index=False)

def detect_missing_values(df):
    cols = [c for c in df.columns if df[c].isna().mean() > 0.05]
    return MissingValuesIssue(cols) if cols else None


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

def run_tabular_diagnostics(csv_path):
    df = pd.read_csv(csv_path)

    issues = []

    for fn in [
        detect_missing_values,
        detect_duplicates,
        detect_constant_columns,
        detect_skewness,
        detect_nlp_columns
    ]:
        res = fn(df)
        if res:
            if isinstance(res, list):
                issues.extend(res)
            else:
                issues.append(res)

    issues.extend(detect_mixed_types(df))

    return issues
