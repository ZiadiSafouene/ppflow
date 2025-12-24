from pathlib import Path
from PIL import Image
from .models import DatasetIdentity

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}

def identify_image_dataset(root_path: Path) -> dict:
    details = {}

    # --------------------------------------------------
    # 1. Detect directory-based splits
    # --------------------------------------------------
    split_dirs = [d for d in ["train", "val", "test"] if (root_path / d).is_dir()]

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

def profile_dir_as_class(root):
    classes = {}
    resolutions = set()
    modes = set()
    corrupt = []

    for d in root.iterdir():
        if not d.is_dir():
            continue
        imgs = list(d.glob("*"))
        classes[d.name] = len(imgs)

        for img in imgs:
            try:
                with Image.open(img) as im:
                    resolutions.add(im.size)
                    modes.add(im.mode)
            except Exception:
                corrupt.append(str(img))

    return {
        "class_distribution": classes,
        "resolutions": list(resolutions),
        "color_modes": list(modes),
        "corrupt_files": corrupt
    }   
