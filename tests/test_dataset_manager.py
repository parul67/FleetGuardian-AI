import os
import pytest
import numpy as np
import cv2
from datasets.dataset_manager import DatasetManager
from utils.file_manager import FileManager

@pytest.fixture
def dummy_dataset(tmp_path):
    """Creates a temporary mock dataset containing valid images and labels."""
    dataset_dir = tmp_path / "mock_dataset"
    images_dir = dataset_dir / "images"
    labels_dir = dataset_dir / "labels"
    
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(labels_dir, exist_ok=True)
    
    # Create 3 valid identical images (for duplicate check) and their labels
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.rectangle(img, (20, 20), (80, 80), (255, 255, 255), -1)
    
    img_paths = []
    lbl_paths = []
    
    for i in range(3):
        img_path = os.path.join(images_dir, f"frame_{i}.jpg")
        cv2.imwrite(img_path, img)
        img_paths.append(img_path)
        
        lbl_path = os.path.join(labels_dir, f"frame_{i}.txt")
        with open(lbl_path, "w") as f:
            # YOLO format: class_id, xc, yc, w, h
            f.write(f"0 0.5 0.5 0.6 0.6\n")
            if i == 0:
                # Add another class instance for distribution tests
                f.write(f"1 0.3 0.3 0.2 0.2\n")
        lbl_paths.append(lbl_path)
        
    # Create a corrupted image file (just empty text file instead of real image format)
    corrupt_path = os.path.join(images_dir, "corrupted.jpg")
    with open(corrupt_path, "w") as f:
        f.write("not an image")
        
    # Create an orphan image (missing annotation text file)
    orphan_img_path = os.path.join(images_dir, "orphan_img.jpg")
    cv2.imwrite(orphan_img_path, img)

    # Create an orphan label (missing matching image)
    orphan_lbl_path = os.path.join(labels_dir, "orphan_lbl.txt")
    with open(orphan_lbl_path, "w") as f:
        f.write("0 0.5 0.5 0.5 0.5\n")

    return str(dataset_dir), img_paths, lbl_paths, corrupt_path, orphan_img_path, orphan_lbl_path

def test_dataset_validation(dummy_dataset):
    dataset_dir = dummy_dataset[0]
    manager = DatasetManager(dataset_dir)
    
    assert manager.validate_structure()

def test_dataset_corruption(dummy_dataset):
    dataset_dir, _, _, corrupt_path, _, _ = dummy_dataset
    manager = DatasetManager(dataset_dir)
    
    corrupted = manager.scan_corrupted_images()
    assert len(corrupted) == 1
    assert os.path.normpath(corrupt_path) in [os.path.normpath(c) for c in corrupted]

def test_missing_annotations(dummy_dataset):
    dataset_dir, _, _, _, orphan_img_path, orphan_lbl_path = dummy_dataset
    manager = DatasetManager(dataset_dir)
    
    missing_lbl, missing_img = manager.scan_missing_annotations()
    
    # 'corrupted.jpg' also misses a label
    assert len(missing_lbl) >= 2
    assert any("orphan_img.jpg" in path for path in missing_lbl)
    assert len(missing_img) == 1
    assert any("orphan_lbl.txt" in path for path in missing_img)

def test_duplicate_detection(dummy_dataset):
    dataset_dir, img_paths, _, _, _, _ = dummy_dataset
    manager = DatasetManager(dataset_dir)
    
    duplicates = manager.scan_duplicate_images()
    # Identical images should trigger duplicate sets
    assert len(duplicates) >= 1

def test_class_distribution(dummy_dataset):
    dataset_dir = dummy_dataset[0]
    manager = DatasetManager(dataset_dir)
    
    dist = manager.get_class_distribution(["distracted", "focused"])
    assert dist["total_objects"] == 5 # 3 label files: two have 1 box, one has 2 boxes, orphan label has 1 box
    assert dist["classes"]["distracted"]["count"] == 4 # class ID 0
    assert dist["classes"]["focused"]["count"] == 1 # class ID 1

def test_dataset_split(dummy_dataset, tmp_path):
    dataset_dir = dummy_dataset[0]
    output_dir = str(tmp_path / "split_output")
    
    manager = DatasetManager(dataset_dir)
    
    # Split: 60% train, 20% val, 20% test
    manager.train_val_test_split(output_dir, 0.6, 0.2, 0.2)
    
    assert os.path.exists(os.path.join(output_dir, "images", "train"))
    assert os.path.exists(os.path.join(output_dir, "labels", "train"))
    assert os.path.exists(os.path.join(output_dir, "images", "val"))
    assert os.path.exists(os.path.join(output_dir, "images", "test"))
