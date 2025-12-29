from pathlib import Path
from PIL import Image
import shutil
import hashlib
from collections import Counter
from .base import Issue

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}


# ==========================================================
# Utility helpers
# ==========================================================

def iter_images(root: Path):
    for p in root.rglob("*"):
        if p.suffix.lower() in IMAGE_EXTS and p.is_file():
            yield p


def image_hash(path: Path, algo="md5"):
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# ==========================================================
# ISSUE: Corrupt images
# ==========================================================

class CorruptImageIssue(Issue):
    id = "corrupt_images"
    severity = "high"

    def __init__(self, files):
        self.files = files
        self.description = f"{len(files)} corrupt image files detected"
        self.fix_description = "Remove corrupt image files"

    def apply_fix(self, input_path, output_path):
        shutil.copytree(input_path, output_path, dirs_exist_ok=True)
        for f in self.files:
            try:
                Path(output_path, f.relative_to(input_path)).unlink()
            except Exception:
                pass


def detect_corrupt_images(root: Path):
    corrupt = []
    for img in iter_images(root):
        try:
            with Image.open(img) as im:
                im.verify()
        except Exception:
            corrupt.append(img)

    return CorruptImageIssue(corrupt) if corrupt else None


# ==========================================================
# ISSUE: Mixed resolutions
# ==========================================================

class MixedResolutionIssue(Issue):
    id = "mixed_resolutions"
    severity = "medium"

    def __init__(self, resolutions):
        self.resolutions = resolutions
        self.description = f"Multiple image resolutions detected: {sorted(resolutions)}"
        self.fix_description = "Resize all images to the most common resolution"

    def apply_fix(self, input_path, output_path):
        shutil.copytree(input_path, output_path, dirs_exist_ok=True)

        counts = Counter()
        for img in iter_images(Path(output_path)):
            with Image.open(img) as im:
                counts[im.size] += 1

        target = counts.most_common(1)[0][0]

        for img in iter_images(Path(output_path)):
            try:
                with Image.open(img) as im:
                    if im.size != target:
                        im = im.resize(target)
                        im.save(img)
            except Exception:
                pass


def detect_mixed_resolutions(root: Path):
    resolutions = set()
    for img in iter_images(root):
        try:
            with Image.open(img) as im:
                resolutions.add(im.size)
        except Exception:
            pass

    return MixedResolutionIssue(resolutions) if len(resolutions) > 1 else None


# ==========================================================
# ISSUE: Mixed color modes
# ==========================================================

class MixedColorModeIssue(Issue):
    id = "mixed_color_modes"
    severity = "medium"

    def __init__(self, modes):
        self.modes = modes
        self.description = f"Mixed color modes detected: {sorted(modes)}"
        self.fix_description = "Convert all images to RGB"

    def apply_fix(self, input_path, output_path):
        shutil.copytree(input_path, output_path, dirs_exist_ok=True)

        for img in iter_images(Path(output_path)):
            try:
                with Image.open(img) as im:
                    if im.mode != "RGB":
                        im.convert("RGB").save(img)
            except Exception:
                pass


def detect_mixed_color_modes(root: Path):
    modes = set()
    for img in iter_images(root):
        try:
            with Image.open(img) as im:
                modes.add(im.mode)
        except Exception:
            pass

    return MixedColorModeIssue(modes) if len(modes) > 1 else None


# ==========================================================
# ISSUE: Duplicate images
# ==========================================================

class DuplicateImageIssue(Issue):
    id = "duplicate_images"
    severity = "low"

    def __init__(self, duplicates):
        self.duplicates = duplicates
        self.description = f"{len(duplicates)} duplicate images detected"
        self.fix_description = "Remove duplicate images (keep one copy)"

    def apply_fix(self, input_path, output_path):
        shutil.copytree(input_path, output_path, dirs_exist_ok=True)

        seen = set()
        for img in iter_images(Path(output_path)):
            h = image_hash(img)
            if h in seen:
                img.unlink()
            else:
                seen.add(h)


def detect_duplicate_images(root: Path):
    hashes = {}
    duplicates = []

    for img in iter_images(root):
        try:
            h = image_hash(img)
            if h in hashes:
                duplicates.append(img)
            else:
                hashes[h] = img
        except Exception:
            pass

    return DuplicateImageIssue(duplicates) if duplicates else None


# ==========================================================
# ISSUE: Class imbalance (directory-as-class)
# ==========================================================

class ClassImbalanceIssue(Issue):
    id = "class_imbalance"
    severity = "info"

    def __init__(self, distribution):
        self.distribution = distribution
        self.description = f"Class imbalance detected: {distribution}"
        self.fix_description = "No automatic fix (requires domain decision)"
    def apply_fix(self, input_path, output_path):
        # For now, just print that manual intervention is needed
        print(f"Class imbalance detected: {self.distribution}. Manual fix required.")


def detect_class_imbalance(root: Path, ratio_threshold=1.0):
    # Prefer train split if present
    if (root / "train").is_dir():
        root = root / "train"
    elif (root / "training").is_dir():
        root = root / "training"

    if not any(d.is_dir() for d in root.iterdir()):
        return None

    counts = {}
    for d in root.iterdir():
        if d.is_dir():
            counts[d.name] = len(list(d.glob("*")))

    if len(counts) < 2:
        return None

    mx, mn = max(counts.values()), min(counts.values())
    if mn > 0 and mx / mn >= ratio_threshold:
        return ClassImbalanceIssue(counts)

    return None


# ==========================================================
# Main entry point (used by runner)
# ==========================================================

def run_image_diagnostics(image_root: Path):
    detectors = [
        detect_corrupt_images,
        detect_duplicate_images,
        detect_mixed_resolutions,
        detect_mixed_color_modes,
        detect_class_imbalance,
    ]

    issues = []
    for detect in detectors:
        found = detect(image_root)
        if found:
            issues.append(found)

    return issues
