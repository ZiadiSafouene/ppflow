import pandas as pd
import chardet
from langdetect import detect
from collections import Counter
from .models import DatasetIdentity

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

def profile_structured_text(files):
    df = pd.read_csv(files[0], nrows=5000)
    text_cols = [c for c in df.columns if df[c].astype(str).str.len().mean() > 30]

    languages = {}
    for col in text_cols:
        langs = []
        for t in df[col].dropna().astype(str).head(300):
            try:
                langs.append(detect(t))
            except Exception:
                pass
        languages[col] = dict(Counter(langs))

    return {
        "text_columns": text_cols,
        "languages": languages,
        "multilingual": any(len(v) > 1 for v in languages.values())
    }
