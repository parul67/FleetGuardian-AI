import random
import numpy as np
from utils.logger import logger

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

def init_seeds(seed: int = 42):
    """
    Sets reproducible random seeds across standard Python libraries, numpy, and torch.
    """
    random.seed(seed)
    np.random.seed(seed)
    
    if HAS_TORCH:
        try:
            torch.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            # Ensure deterministic algorithms if possible
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
            logger.info(f"Initialized PyTorch and NumPy random seeds to {seed}")
        except Exception as e:
            logger.warning(f"Failed to fully configure PyTorch determinism: {e}")
    else:
        logger.info(f"Initialized standard random and NumPy seeds to {seed} (PyTorch not available)")
