from pathlib import Path
from .models import DatasetIdentity
from .tabular import identify_tabular_dataset
from .images import identify_image_dataset
from .text import identify_text_dataset
from .splits import infer_data_splits


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}
TABULAR_EXTS = {".csv", ".tsv", ".xlsx", ".xls", ".parquet", ".json"}

def scan_data() -> DatasetIdentity:
    data_dir = Path.cwd() / "data"
    if not data_dir.exists():
        raise FileNotFoundError("Missing required data/ directory")

    files = [f for f in data_dir.rglob("*") if f.is_file()]
    if not files:
        raise ValueError("data/ directory is empty")

    if any(f.suffix.lower() in IMAGE_EXTS for f in files):
        dataset = identify_image_dataset(data_dir)
    elif any(f.suffix.lower() in TABULAR_EXTS for f in files):
        dataset = identify_tabular_dataset(files, data_dir)
    else:
        dataset = identify_text_dataset(files, data_dir)

    splits = infer_data_splits(data_dir, files)
    dataset.details["splits"] = splits
    return dataset
