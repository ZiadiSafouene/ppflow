from pathlib import Path
import pandas as pd

def infer_data_splits(root: Path, files):
    splits = {}

    for split in ["train", "val", "test","training","testing","validation"]:
        d = root / split
        if d.exists():
            splits[split] = len(list(d.rglob("*")))

    if splits:
        return {"type": "directory", "splits": splits}

    for f in files:
        name = f.stem.lower()
        for s in ["train", "val", "test"]:
            if s in name:
                splits.setdefault(s, 0)
                splits[s] += 1

    if splits:
        return {"type": "file", "splits": splits}

    for f in files:
        if f.suffix == ".csv":
            df = pd.read_csv(f, nrows=1000)
            for col in df.columns:
                vals = set(df[col].astype(str).str.lower())
                if vals <= {"train", "val", "test"}:
                    return {
                        "type": "column",
                        "column": col,
                        "distribution": df[col].value_counts().to_dict()
                    }

    return {"type": "none"}
