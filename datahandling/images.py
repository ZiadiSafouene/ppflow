from pathlib import Path
from PIL import Image
from .models import DatasetIdentity

SPLITS = {"train", "test", "val", "training", "testing", "validation"}


class ImageDirectoryProfiler:
    def __init__(self, root: Path):
        self.root = root

    def run(self) -> dict:
        profile = {
            "splits": {},
            "global": {
                "class_distribution": {},
                "resolutions": set(),
                "color_modes": set(),
                "corrupt_files": []
            }
        }

        split_dirs = [
            d for d in self.root.iterdir()
            if d.is_dir() and d.name in SPLITS
        ]
        # print ("--------------",self.root,split_dirs)

        # --------------------------------------------------
        # Case 1: Dataset has train / test / val
        # --------------------------------------------------
        if split_dirs:
            for split in split_dirs:
                split_profile = {
                    "class_distribution": {},
                    "resolutions": set(),
                    "color_modes": set(),
                    "corrupt_files": []
                }

                for class_dir in split.iterdir():
                    if not class_dir.is_dir():
                        continue

                    imgs = list(class_dir.glob("*"))
                    split_profile["class_distribution"][class_dir.name] = len(imgs)

                    # Global aggregation
                    profile["global"]["class_distribution"].setdefault(class_dir.name, 0)
                    profile["global"]["class_distribution"][class_dir.name] += len(imgs)

                    for img in imgs:
                        try:
                            with Image.open(img) as im:
                                split_profile["resolutions"].add(im.size)
                                split_profile["color_modes"].add(im.mode)

                                profile["global"]["resolutions"].add(im.size)
                                profile["global"]["color_modes"].add(im.mode)
                        except Exception:
                            split_profile["corrupt_files"].append(str(img))
                            profile["global"]["corrupt_files"].append(str(img))

                profile["splits"][split.name] = self._finalize_profile(split_profile)

        # --------------------------------------------------
        # Case 2: No splits, only class folders
        # --------------------------------------------------
        else:
            for class_dir in self.root.iterdir():
                if not class_dir.is_dir():
                    continue

                imgs = list(class_dir.glob("*"))
                profile["global"]["class_distribution"][class_dir.name] = len(imgs)

                for img in imgs:
                    try:
                        with Image.open(img) as im:
                            profile["global"]["resolutions"].add(im.size)
                            profile["global"]["color_modes"].add(im.mode)
                    except Exception:
                        profile["global"]["corrupt_files"].append(str(img))

        profile["global"] = self._finalize_profile(profile["global"])
        return profile

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------
    def _finalize_profile(self, p: dict) -> dict:
        return {
            "class_distribution": p["class_distribution"],
            "resolutions": list(p["resolutions"]),
            "color_modes": list(p["color_modes"]),
            "corrupt_files": p["corrupt_files"],
            "dataset_quality": self._quality_report(p)
        }

    def _quality_report(self, p: dict) -> dict:
        issues = []

        if len(p["resolutions"]) > 1:
            issues.append("inconsistent_image_resolutions")

        if len(p["color_modes"]) > 1:
            issues.append("mixed_color_modes")

        if p["corrupt_files"]:
            issues.append("corrupt_images_detected")

        return {
            "status": "ok" if not issues else "issues",
            "issues": issues
        }


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}

def identify_image_dataset(root_path: Path) -> dict:
    details = {}

    # --------------------------------------------------
    # 1. Detect directory-based splits
    # --------------------------------------------------
    split_dirs = [d for d in ["train", "val", "test","training","testing","validation"] if (root_path / d).is_dir()]

    if split_dirs:
        split_info = {}
        has_class_folders = False

        for split in split_dirs:
            split_path = root_path / split

            class_dirs = [
                d for d in split_path.iterdir()
                if d.is_dir()
            ]

            if class_dirs:
                
                has_class_folders = True
                count = sum(
                    len(list(c.glob("*.jpg"))) +
                    len(list(c.glob("*.png"))) +
                    len(list(c.glob("*.jpeg")))
                    for c in class_dirs
                )
            else:
                count = len(list(split_path.glob("*.jpg"))) + \
                        len(list(split_path.glob("*.png"))) + \
                        len(list(split_path.glob("*.jpeg")))

            split_info[split] = count

        details["splits"] = {
            "type": "directory",
            "splits": split_info
        }

        if has_class_folders:
            profiler = ImageDirectoryProfiler(root_path)
            details["profile"] = profiler.run()
            details["label_source"] = "directory_names"

            details["label_source"] = "directory_names"

        return DatasetIdentity(
        root=root_path,
        container_type="image",
        structural_form="hirarchical_with_splits",
        details=details 
    )

    # --------------------------------------------------
    # 2. Detect hierarchical (no splits, only classes)
    # --------------------------------------------------
    class_dirs = [d for d in root_path.iterdir() if d.is_dir()]

    if class_dirs:
        profiler = ImageDirectoryProfiler(root_path)
        details["profile"] = profiler.run()
        details["label_source"] = "directory_names"
        details["num_classes"] = len(class_dirs)

        return DatasetIdentity(
            root=root_path,
            container_type="image",
            structural_form="hirarchical_no_splits",
            details=details
        )

    # --------------------------------------------------
    # 3. Flat dataset (no splits, no class folders)
    # --------------------------------------------------
    image_files = list(root_path.glob("*.jpg")) + \
                  list(root_path.glob("*.png")) + \
                  list(root_path.glob("*.jpeg"))

    if image_files:
       return DatasetIdentity(
        root=root_path,
        container_type="image",
        structural_form="flat",
        details=details 
    )
    # --------------------------------------------------
    # 4. Unknown image layout
    # --------------------------------------------------
    return DatasetIdentity(
        root=root_path,
        container_type="image",
        structural_form="Unknown",
        details=details 
    )



def profile_dir_as_class(root: Path) -> dict:
    profile = {
        "splits": {},
        "global": {
            "class_distribution": {},
            "resolutions": set(),
            "color_modes": set(),
            "corrupt_files": []
        }
    }

    split_dirs = [d for d in root.iterdir() if d.is_dir() and d.name in SPLITS]

    # --------------------------------------------------
    # Case 1: Dataset has train / test / val
    # --------------------------------------------------
    if split_dirs:
        for split in split_dirs:
            split_profile = {
                "class_distribution": {},
                "resolutions": set(),
                "color_modes": set(),
                "corrupt_files": []
            }

            for class_dir in split.iterdir():
                if not class_dir.is_dir():
                    continue

                imgs = list(class_dir.glob("*"))
                split_profile["class_distribution"][class_dir.name] = len(imgs)

                # Global aggregation
                profile["global"]["class_distribution"].setdefault(class_dir.name, 0)
                profile["global"]["class_distribution"][class_dir.name] += len(imgs)

                for img in imgs:
                    try:
                        with Image.open(img) as im:
                            split_profile["resolutions"].add(im.size)
                            split_profile["color_modes"].add(im.mode)

                            profile["global"]["resolutions"].add(im.size)
                            profile["global"]["color_modes"].add(im.mode)
                    except Exception:
                        split_profile["corrupt_files"].append(str(img))
                        profile["global"]["corrupt_files"].append(str(img))

            # Normalize split data
            profile["splits"][split.name] = {
                "class_distribution": split_profile["class_distribution"],
                "resolutions": list(split_profile["resolutions"]),
                "color_modes": list(split_profile["color_modes"]),
                "corrupt_files": split_profile["corrupt_files"]
            }

    # --------------------------------------------------
    # Case 2: No splits, only class folders
    # --------------------------------------------------
    else:
        for class_dir in root.iterdir():
            if not class_dir.is_dir():
                continue

            imgs = list(class_dir.glob("*"))
            profile["global"]["class_distribution"][class_dir.name] = len(imgs)

            for img in imgs:
                try:
                    with Image.open(img) as im:
                        profile["global"]["resolutions"].add(im.size)
                        profile["global"]["color_modes"].add(im.mode)
                except Exception:
                    profile["global"]["corrupt_files"].append(str(img))

    # --------------------------------------------------
    # Final normalization
    # --------------------------------------------------
    profile["global"]["resolutions"] = list(profile["global"]["resolutions"])
    profile["global"]["color_modes"] = list(profile["global"]["color_modes"])

    return profile
