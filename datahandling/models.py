from dataclasses import dataclass
from pathlib import Path
from typing import Dict

@dataclass
class DatasetIdentity:
    root: Path
    container_type: str        # table | image | text
    structural_form: str
    details: Dict
    