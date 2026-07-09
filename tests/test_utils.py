import os
import time
import pytest
import numpy as np
from utils.file_manager import FileManager
from utils.timer import Timer
from utils.fps_calculator import FPSCalculator
from utils.path_utils import PathUtils
from utils.seed_initializer import init_seeds
from utils.logger import logger

def test_file_manager(tmp_path):
    """Test directory creation, file listing, and deletion."""
    test_dir = str(tmp_path / "test_folder")
    
    # Ensure dir
    created = FileManager.ensure_dir(test_dir)
    assert os.path.exists(created)
    assert os.path.isdir(created)
    
    # Write sample files
    file1 = os.path.join(created, "test1.jpg")
    file2 = os.path.join(created, "test2.png")
    file3 = os.path.join(created, "test3.txt")
    
    with open(file1, "w") as f:
        f.write("img1")
    with open(file2, "w") as f:
        f.write("img2")
    with open(file3, "w") as f:
        f.write("txt")
        
    # List files with extensions
    images = FileManager.list_files(created, [".jpg", ".png"])
    assert len(images) == 2
    assert any("test1.jpg" in f for f in images)
    assert any("test2.png" in f for f in images)
    
    # Delete file
    assert FileManager.delete_file(file1)
    assert not os.path.exists(file1)
    
    # Clean dir
    FileManager.clean_dir(created)
    assert len(os.listdir(created)) == 0

def test_timer(capsys):
    """Test timer function decorator and context manager."""
    # Context manager
    with Timer(name="test_context", print_log=True) as t:
        time.sleep(0.01)
    assert t.elapsed > 0.0
    
    # Decorator
    @Timer.decorator(name="test_decorator", print_log=True)
    def dummy_func():
        time.sleep(0.01)
        return 42
        
    res = dummy_func()
    assert res == 42

def test_fps_calculator():
    """Verify that FPSCalculator accurately reports frame timing intervals."""
    calc = FPSCalculator(window_size=5)
    calc.start()
    
    assert calc.fps == 0.0
    
    # Simulate frames
    calc.update()
    time.sleep(0.01)
    fps = calc.update()
    assert fps > 0.0
    assert calc.fps == fps

def test_path_utils():
    """Verify PathUtils correctly resolves directory paths relative to root."""
    root = PathUtils.get_project_root()
    assert os.path.exists(root)
    
    resolved = PathUtils.resolve_path("configs/config.yaml")
    assert os.path.isabs(resolved)
    assert "config.yaml" in resolved
    
    model_path = PathUtils.get_model_path("yolo11n.pt")
    assert "yolo11n.pt" in model_path

def test_seed_initializer():
    """Test seed initialization ensures reproducibility."""
    init_seeds(42)
    val1 = np.random.rand()
    
    init_seeds(42)
    val2 = np.random.rand()
    
    assert val1 == val2
