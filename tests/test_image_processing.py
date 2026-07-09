import pytest
import numpy as np
import cv2
from cv.image_processing.preprocessor import ImagePreprocessor

@pytest.fixture
def sample_image():
    """Generates a dummy synthetic BGR image for testing."""
    # 3-channel color image, dimensions 100x200
    img = np.zeros((100, 200, 3), dtype=np.uint8)
    # Add a white rectangle in the center
    cv2.rectangle(img, (40, 20), (160, 80), (255, 255, 255), -1)
    return img

def test_resize_no_aspect(sample_image):
    """Test standard resizing without keeping aspect ratio."""
    resized = ImagePreprocessor.resize(sample_image, 120, 120, keep_aspect_ratio=False)
    assert resized.shape == (120, 120, 3)

def test_resize_keep_aspect(sample_image):
    """Test resizing with padding to maintain aspect ratio."""
    # Input is 100x200 (h=100, w=200). We resize to 100x100.
    # To keep aspect, w will scale to 100, so h will scale to 50.
    # The output will be 100x100 with padding of 25px top and bottom.
    resized = ImagePreprocessor.resize(sample_image, 100, 100, keep_aspect_ratio=True)
    assert resized.shape == (100, 100, 3)
    
    # Check top/bottom pixels are black padding
    assert np.all(resized[0, :] == 0)
    assert np.all(resized[99, :] == 0)
    # Mid section has the resized white box
    assert np.any(resized[50, :] > 0)

def test_crop(sample_image):
    """Verify crop slice indices are boundaries-safe."""
    cropped = ImagePreprocessor.crop(sample_image, 40, 20, 120, 60)
    assert cropped.shape == (60, 120, 3)
    
    # Check out-of-bound crop coordinates don't crash and clamp safely
    cropped_out = ImagePreprocessor.crop(sample_image, 150, 80, 200, 200)
    assert cropped_out.size > 0

def test_normalize(sample_image):
    """Verify pixel values normalization ranges."""
    norm = ImagePreprocessor.normalize(sample_image)
    assert norm.dtype == np.float32
    assert norm.min() >= 0.0
    assert norm.max() <= 1.0

    # With mean/std parameters
    mean = (0.5, 0.5, 0.5)
    std = (0.5, 0.5, 0.5)
    norm_param = ImagePreprocessor.normalize(sample_image, mean, std)
    assert norm_param.shape == sample_image.shape
    assert norm_param.dtype == np.float32

def test_convert_color(sample_image):
    """Test RGB/GRAY color conversions."""
    gray = ImagePreprocessor.convert_color(sample_image, cv2.COLOR_BGR2GRAY)
    assert len(gray.shape) == 2
    assert gray.shape == (100, 200)

def test_blur(sample_image):
    """Test smoothing filters."""
    blurred = ImagePreprocessor.blur(sample_image, method="gaussian", ksize=5)
    assert blurred.shape == sample_image.shape
    assert not np.array_equal(blurred, sample_image)

def test_sharpen(sample_image):
    """Test sharpening kernel application."""
    sharpened = ImagePreprocessor.sharpen(sample_image)
    assert sharpened.shape == sample_image.shape

def test_equalize_histogram(sample_image):
    """Test histogram equalization on gray and color frames."""
    # Gray
    gray = cv2.cvtColor(sample_image, cv2.COLOR_BGR2GRAY)
    eq_gray = ImagePreprocessor.equalize_histogram(gray)
    assert eq_gray.shape == gray.shape
    
    # Color BGR (via CLAHE LAB)
    eq_color = ImagePreprocessor.equalize_histogram(sample_image)
    assert eq_color.shape == sample_image.shape
