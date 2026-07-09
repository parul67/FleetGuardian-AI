import os
import cv2
import shutil
import random
import numpy as np
from typing import Dict, Any, List, Tuple, Set
from utils.logger import logger
from utils.file_manager import FileManager

class DatasetManager:
    """
    Utilities for managing and validating machine learning/object detection datasets.
    Supports file validation, corruption checks, duplicate detection, splitting,
    and class distribution reports.
    """
    def __init__(self, dataset_dir: str):
        self.dataset_dir = os.path.abspath(dataset_dir)
        self.images_dir = os.path.normpath(os.path.join(self.dataset_dir, "images"))
        self.labels_dir = os.path.normpath(os.path.join(self.dataset_dir, "labels"))
        
        # Supported image formats
        self.img_extensions = [".jpg", ".jpeg", ".png", ".bmp"]

    def validate_structure(self) -> bool:
        """Verifies if the basic images/ and labels/ folder structure exists."""
        has_images = os.path.exists(self.images_dir)
        has_labels = os.path.exists(self.labels_dir)
        if not has_images or not has_labels:
            logger.error(f"Invalid dataset structure at {self.dataset_dir}. 'images' and 'labels' subfolders are required.")
            return False
        logger.info(f"Dataset structure verified at {self.dataset_dir}")
        return True

    def scan_corrupted_images(self) -> List[str]:
        """
        Scans for corrupted images that cannot be loaded by OpenCV.
        Returns a list of corrupted image paths.
        """
        if not os.path.exists(self.images_dir):
            return []

        corrupted = []
        img_paths = FileManager.list_files(self.images_dir, self.img_extensions)
        
        for path in img_paths:
            try:
                img = cv2.imread(path)
                if img is None:
                    corrupted.append(path)
            except Exception:
                corrupted.append(path)
                
        if corrupted:
            logger.warning(f"Found {len(corrupted)} corrupted images out of {len(img_paths)} total files.")
        else:
            logger.info(f"Scan complete: all {len(img_paths)} images read successfully.")
        return corrupted

    def scan_missing_annotations(self) -> Tuple[List[str], List[str]]:
        """
        Scans for:
        1. Images without a corresponding annotation file.
        2. Annotation files without a corresponding image.
        """
        missing_labels = []
        missing_images = []

        if not os.path.exists(self.images_dir) or not os.path.exists(self.labels_dir):
            return [], []

        # List all images and label files (excluding extensions)
        img_files = FileManager.list_files(self.images_dir, self.img_extensions)
        lbl_files = FileManager.list_files(self.labels_dir, [".txt"])

        img_basenames = {os.path.splitext(os.path.basename(f))[0]: f for f in img_files}
        lbl_basenames = {os.path.splitext(os.path.basename(f))[0]: f for f in lbl_files}

        # Check for missing labels
        for name, path in img_basenames.items():
            if name not in lbl_basenames:
                missing_labels.append(path)

        # Check for missing images
        for name, path in lbl_basenames.items():
            if name not in img_basenames:
                missing_images.append(path)

        logger.info(f"Missing annotations scan: {len(missing_labels)} images missing labels, {len(missing_images)} labels missing images.")
        return missing_labels, missing_images

    def scan_duplicate_images(self, hash_size: int = 8) -> List[Tuple[str, str]]:
        """
        Detects duplicate or near-duplicate images using Difference Hashing (dHash).
        Returns a list of image path pairs that are duplicates.
        """
        if not os.path.exists(self.images_dir):
            return []

        img_paths = FileManager.list_files(self.images_dir, self.img_extensions)
        hashes: Dict[str, str] = {}
        duplicates = []

        for path in img_paths:
            try:
                img = cv2.imread(path)
                if img is None:
                    continue
                # Calculate dHash
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                resized = cv2.resize(gray, (hash_size + 1, hash_size))
                diff = resized[:, 1:] > resized[:, :-1]
                # Flatten the difference array to a hex string hash
                hash_val = "".join(["1" if b else "0" for b in diff.flatten()])
                
                if hash_val in hashes:
                    duplicates.append((hashes[hash_val], path))
                else:
                    hashes[hash_val] = path
            except Exception as e:
                logger.error(f"Error hashing image {path}: {e}")

        logger.info(f"Duplicate scan complete. Found {len(duplicates)} duplicate image pairs.")
        return duplicates

    def get_class_distribution(self, class_names: List[str]) -> Dict[str, Any]:
        """
        Reads YOLO format text files to compute class frequencies.
        Returns a distribution dictionary.
        """
        distribution: Dict[int, int] = {i: 0 for i in range(len(class_names))}
        total_annotations = 0

        if not os.path.exists(self.labels_dir):
            return {}

        label_paths = FileManager.list_files(self.labels_dir, [".txt"])
        
        for path in label_paths:
            try:
                with open(path, "r") as f:
                    for line in f:
                        parts = line.strip().split()
                        if parts:
                            cls_id = int(parts[0])
                            if cls_id in distribution:
                                distribution[cls_id] += 1
                                total_annotations += 1
            except Exception as e:
                logger.error(f"Failed to read label {path}: {e}")

        # Map to readable dictionary
        report = {}
        for cls_id, count in distribution.items():
            name = class_names[cls_id] if cls_id < len(class_names) else f"Unknown-{cls_id}"
            pct = (count / total_annotations * 100.0) if total_annotations > 0 else 0.0
            report[name] = {
                "count": count,
                "percentage": round(pct, 2)
            }
            
        logger.info(f"Class distribution calculated. Total annotated boxes: {total_annotations}")
        return {
            "total_objects": total_annotations,
            "classes": report
        }

    def train_val_test_split(
        self,
        output_dir: str,
        train_ratio: float = 0.7,
        val_ratio: float = 0.2,
        test_ratio: float = 0.1,
        seed: int = 42
    ):
        """
        Splits matching images and labels into train/val/test subdirectories.
        """
        if not self.validate_structure():
            return

        # Assert sum ratio is 1
        assert abs((train_ratio + val_ratio + test_ratio) - 1.0) < 1e-5, "Ratios must sum to 1.0"

        # List all matching image names
        img_files = FileManager.list_files(self.images_dir, self.img_extensions)
        lbl_files = FileManager.list_files(self.labels_dir, [".txt"])

        img_basenames = {os.path.splitext(os.path.basename(f))[0]: f for f in img_files}
        lbl_basenames = {os.path.splitext(os.path.basename(f))[0]: f for f in lbl_files}

        # Keep only matching pairs
        matching_keys = list(img_basenames.keys() & lbl_basenames.keys())
        random.seed(seed)
        random.shuffle(matching_keys)

        total = len(matching_keys)
        if total == 0:
            logger.warning("No matching image-label pairs found for splitting.")
            return

        train_end = int(total * train_ratio)
        val_end = train_end + int(total * val_ratio)

        splits = {
            "train": matching_keys[:train_end],
            "val": matching_keys[train_end:val_end],
            "test": matching_keys[val_end:]
        }

        # Create output directory folders
        for split in ["train", "val", "test"]:
            os.makedirs(os.path.join(output_dir, "images", split), exist_ok=True)
            os.makedirs(os.path.join(output_dir, "labels", split), exist_ok=True)

        # Copy files
        for split_name, keys in splits.items():
            for key in keys:
                # Copy image
                src_img = img_basenames[key]
                dst_img = os.path.join(output_dir, "images", split_name, os.path.basename(src_img))
                shutil.copy2(src_img, dst_img)

                # Copy label
                src_lbl = lbl_basenames[key]
                dst_lbl = os.path.join(output_dir, "labels", split_name, os.path.basename(src_lbl))
                shutil.copy2(src_lbl, dst_lbl)
                
            logger.info(f"Copied {len(keys)} pairs to '{split_name}' split inside {output_dir}")

    def visualize_dataset(self, class_names: List[str], output_dir: str, num_samples: int = 5):
        """
        Draws bounding boxes from annotations onto a subset of images and exports them.
        """
        if not self.validate_structure():
            return

        img_files = FileManager.list_files(self.images_dir, self.img_extensions)
        lbl_files = FileManager.list_files(self.labels_dir, [".txt"])

        img_basenames = {os.path.splitext(os.path.basename(f))[0]: f for f in img_files}
        lbl_basenames = {os.path.splitext(os.path.basename(f))[0]: f for f in lbl_files}

        matching_keys = list(img_basenames.keys() & lbl_basenames.keys())
        if not matching_keys:
            logger.warning("No matching images/labels for visualization.")
            return

        samples = random.sample(matching_keys, min(num_samples, len(matching_keys)))
        os.makedirs(output_dir, exist_ok=True)

        for key in samples:
            img_path = img_basenames[key]
            lbl_path = lbl_basenames[key]

            img = cv2.imread(img_path)
            if img is None:
                continue

            h, w = img.shape[:2]
            
            # Read and draw YOLO labels (class_id, x_center, y_center, width, height) normalized
            try:
                with open(lbl_path, "r") as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            cls_id = int(parts[0])
                            xc, yc, nw, nh = map(float, parts[1:5])
                            
                            # Convert YOLO normalized coords to pixel bounding box coords
                            x1 = int((xc - nw / 2.0) * w)
                            y1 = int((yc - nh / 2.0) * h)
                            x2 = int((xc + nw / 2.0) * w)
                            y2 = int((yc + nh / 2.0) * h)

                            name = class_names[cls_id] if cls_id < len(class_names) else f"ID-{cls_id}"
                            
                            # Draw
                            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            cv2.putText(img, name, (x1, max(y1 - 5, 12)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)
            except Exception as e:
                logger.error(f"Error plotting labels on sample {key}: {e}")

            out_path = os.path.join(output_dir, f"visualized_{key}.jpg")
            cv2.imwrite(out_path, img)
            logger.info(f"Exported dataset visual check frame to {out_path}")
