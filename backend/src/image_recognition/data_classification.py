import os
import shutil
import random
import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

THIS_FOLDER = Path(__file__).resolve().parent
src = THIS_FOLDER / "datasets"
original_data = src / "original" / "augmented"


def parse_args():
    parser = argparse.ArgumentParser(description="Split augmented images into train/val folders")
    parser.add_argument("--split-ratio", type=float, default=0.8, help="Train split ratio")
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 1) * 2), help="Number of parallel file workers")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible split")
    parser.add_argument("--dry-run", action="store_true", help="Print planned moves without moving files")
    return parser.parse_args()


def list_image_files(images_dir):
    return [entry.name for entry in os.scandir(images_dir) if entry.is_file() and entry.name.lower().endswith(".jpg")]


def move_or_replace(src_path, dst_path):
    try:
        os.replace(src_path, dst_path)
    except OSError:
        shutil.move(src_path, dst_path)


def move_pair(file_name, direction, dry_run=False):
    image_src = original_data / "images" / file_name
    label_src = original_data / "labeled" / file_name.replace(".jpg", ".txt")

    image_dest = src / direction / "images" / file_name
    label_dest = src / direction / "labels" / file_name.replace(".jpg", ".txt")

    if dry_run:
        return f"[{direction}] {file_name}"

    move_or_replace(str(image_src), str(image_dest))
    if label_src.exists():
        move_or_replace(str(label_src), str(label_dest))
    return None


def move_files_parallel(files, direction, workers=1, dry_run=False):
    if not files:
        return

    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(lambda name: move_pair(name, direction, dry_run=dry_run), files))

    if dry_run:
        for line in results[:10]:
            if line:
                print(line)
        if len(results) > 10:
            print(f"... and {len(results) - 10} more {direction} moves")


def ensure_destination_dirs():
    (src / "train" / "images").mkdir(parents=True, exist_ok=True)
    (src / "train" / "labels").mkdir(parents=True, exist_ok=True)
    (src / "val" / "images").mkdir(parents=True, exist_ok=True)
    (src / "val" / "labels").mkdir(parents=True, exist_ok=True)


def main():
    args = parse_args()
    ensure_destination_dirs()

    images_dir = original_data / "images"
    image_files = list_image_files(str(images_dir))

    rng = random.Random(args.seed)
    rng.shuffle(image_files)

    split_ratio = min(max(args.split_ratio, 0.0), 1.0)
    split_index = int(len(image_files) * split_ratio)

    train_images = image_files[:split_index]
    val_images = image_files[split_index:]

    workers = max(1, args.workers)
    move_files_parallel(train_images, "train", workers=workers, dry_run=args.dry_run)
    move_files_parallel(val_images, "val", workers=workers, dry_run=args.dry_run)

    print(f"Total images: {len(image_files)}")
    print(f"Train: {len(train_images)}, Val: {len(val_images)}")
    print(f"Workers: {workers}, Dry run: {args.dry_run}")


# python data_classification.py --workers 8 --split-ratio 0.8
if __name__ == "__main__":
    main()