import pandas as pd
import chardet
from langdetect import detect
from collections import Counter
from .models import DatasetIdentity

COMMON_ENCODINGS = ["utf-8", "latin-1", "cp1252"]

def safe_read_csv(path, nrows=5000):
    last_error = None
    for enc in COMMON_ENCODINGS:
        try:
            return pd.read_csv(path, encoding=enc, nrows=nrows), enc
        except UnicodeDecodeError as e:
            last_error = e
    raise last_error

def identify_text_dataset(files, root):
    if all(f.suffix == ".txt" for f in files):
        form = "raw_text"
        details = profile_raw_text(files)
    else:
        form = "structured_text"
        details = profile_structured_text(files)

    return DatasetIdentity(
        root=root,
        container_type="text",
        structural_form=form,
        details=details
    )

def profile_raw_text(files):
    encodings = set()
    for f in files:
        raw = f.read_bytes()
        encodings.add(chardet.detect(raw)["encoding"])
    return {"encodings": list(encodings)}

def profile_structured_text(df):
    
    text_cols = [c for c in df.columns if df[c].astype(str).str.len().mean() > 30]

    LANG_THRESHOLD = 0.15   # 15% of detected texts in the column
    MIN_SAMPLES = 20        # avoid noise on very small columns
   
    languages = {}

    for col in text_cols:
        detections = []

        for t in df[col].dropna().astype(str).head(300):
            try:
                detections.append(detect(t))
            except Exception:
                pass

        total = len(detections)

        if total < MIN_SAMPLES:
            languages[col] = {}
            continue

        counts = Counter(detections)

        # keep only languages that pass the threshold
        filtered = {
            lang: count
            for lang, count in counts.items()
            if (count / total) >= LANG_THRESHOLD
        }

        languages[col] = filtered

    return {
        "text_columns": text_cols,
        "languages": languages[col],
        "multilingual": any(len(v) > 1 for v in languages.values()),
    }
