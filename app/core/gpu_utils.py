import torch
import pynvml
from typing import Optional, Tuple

def get_device() -> torch.device:
    """
    Returns the best available device (GPU if available, else CPU)
    """
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")

def get_gpu_memory_info() -> Optional[Tuple[int, int]]:
    """
    Returns tuple of (free_memory, total_memory) in MB if GPU is available
    Returns None if no GPU is available
    """
    if not torch.cuda.is_available():
        return None
    
    try:
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        return (info.free // 1024 // 1024, info.total // 1024 // 1024)
    except Exception:
        return None

def clear_gpu_memory():
    """
    Clears GPU memory cache if GPU is available
    """
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

def get_device_info() -> dict:
    """
    Returns information about available devices
    """
    info = {
        "device_type": "cpu",
        "device_name": "CPU",
        "gpu_memory": None
    }
    
    if torch.cuda.is_available():
        info["device_type"] = "cuda"
        info["device_name"] = torch.cuda.get_device_name(0)
        memory_info = get_gpu_memory_info()
        if memory_info:
            info["gpu_memory"] = {
                "free_mb": memory_info[0],
                "total_mb": memory_info[1]
            }
    
    return info 