import torch
import pynvml
from typing import Dict, Optional

def initialize_gpu() -> None:
    """Initialize GPU settings and optimizations."""
    if torch.cuda.is_available():
        # Enable cuDNN benchmarking for better performance
        torch.backends.cudnn.benchmark = True
        # Enable TF32 for better performance on Ampere GPUs
        torch.backends.cuda.matmul.allow_tf32 = True
        # Initialize NVIDIA Management Library
        pynvml.nvmlInit()

def get_gpu_info() -> Dict[str, Optional[str]]:
    """Get information about available GPUs."""
    info = {
        "cuda_available": str(torch.cuda.is_available()),
        "cuda_version": torch.version.cuda if torch.cuda.is_available() else None,
        "gpu_count": str(torch.cuda.device_count()) if torch.cuda.is_available() else "0",
        "current_device": str(torch.cuda.current_device()) if torch.cuda.is_available() else None,
        "device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
    }
    
    try:
        if torch.cuda.is_available():
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            info.update({
                "total_memory": f"{memory_info.total / 1024**2:.2f} MB",
                "free_memory": f"{memory_info.free / 1024**2:.2f} MB",
                "used_memory": f"{memory_info.used / 1024**2:.2f} MB"
            })
    except Exception as e:
        info["error"] = str(e)
    
    return info

def set_device(device_id: int = 0) -> torch.device:
    """Set the default CUDA device."""
    if torch.cuda.is_available():
        torch.cuda.set_device(device_id)
        return torch.device(f"cuda:{device_id}")
    return torch.device("cpu") 