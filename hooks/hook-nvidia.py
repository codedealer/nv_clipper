# This hook handles NVIDIA CUDA library bundling for yt_clipper
# Environment variables:
# - SKIP_GPU_LIBS=1: Skip all GPU libraries (CPU-only build)
# - CACHED_GPU_LIBS=1: Use cached GPU libraries approach
# - RUNTIME_GPU_LIBS=1: Exclude NVIDIA DLLs from executable for runtime loading
# - Default: Bundle required NVIDIA GPU libraries directly

import os
import shutil
import sys
from pathlib import Path

from PyInstaller.utils.hooks import get_package_paths
import logging

logger = logging.getLogger(__name__)

# Required DLLs for RIFE on ONNX CUDA engine
REQUIRED_CUDA_DLLS = [
    "cublasLt64_12.dll",
    "cublas64_12.dll",
    "cufft64_11.dll",
    "cudart64_12.dll",
    "cudnn_engines_runtime_compiled64_9.dll",
    "cudnn_engines_precompiled64_9.dll",
    "cudnn_heuristic64_9.dll",
    "cudnn_ops64_9.dll",
    "cudnn_adv64_9.dll",
    "cudnn_graph64_9.dll",
    "cudnn64_9.dll"
]

def cache_gpu_libraries():
    """Cache only the required NVIDIA CUDA libraries for RIFE"""
    cache_dir = Path("./cache/gpu-libs")
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Required DLLs for RIFE on ONNX CUDA engine
    REQUIRED_CUDA_DLLS = [
        "cublasLt64_12.dll",
        "cublas64_12.dll",
        "cufft64_11.dll",
        "cudart64_12.dll",
        "cudnn_engines_runtime_compiled64_9.dll",
        "cudnn_engines_precompiled64_9.dll",
        "cudnn_heuristic64_9.dll",
        "cudnn_ops64_9.dll",
        "cudnn_adv64_9.dll",
        "cudnn_graph64_9.dll",
        "cudnn64_9.dll"
    ]

    binaries = []

    try:
        # Cache only required NVIDIA libraries
        nvidia_pkg_paths = get_package_paths("nvidia")
        nvidia_src = Path(nvidia_pkg_paths[0]) / "nvidia"
        nvidia_cache = cache_dir / "nvidia"

        if nvidia_src.exists():
            logger.info(f"Caching required NVIDIA CUDA libraries from {nvidia_src} to {nvidia_cache}")
            if nvidia_cache.exists():
                shutil.rmtree(nvidia_cache)

            # Copy only the required DLLs
            NVIDIA_PACKAGES = ["cublas", "cuda_nvrtc", "cuda_runtime", "cudnn", "cufft", "curand", "nvjitlink"]
            for package in NVIDIA_PACKAGES:
                package_src = nvidia_src / package / "bin"
                if package_src.exists():
                    package_cache = nvidia_cache / package / "bin"
                    package_cache.mkdir(parents=True, exist_ok=True)

                    for dll_file in package_src.glob("*.dll"):
                        if dll_file.name in REQUIRED_CUDA_DLLS:
                            dest_file = package_cache / dll_file.name
                            shutil.copy2(dll_file, dest_file)
                            binaries.append((str(dest_file), f"nvidia/{package}/bin"))
                            logger.info(f"Cached required DLL: {dll_file.name}")

        # Create a marker file to indicate cache is complete
        (cache_dir / ".cache_complete").touch()
        logger.info(f"Required CUDA libraries cached successfully to {cache_dir}")

    except Exception as e:
        logger.error(f"Error caching CUDA libraries: {e}")
        return []

    return binaries

def get_cached_binaries():
    """Get only required NVIDIA CUDA binaries from cache directory"""
    cache_dir = Path("./cache/gpu-libs")
    binaries = []

    if not cache_dir.exists():
        logger.warning("Cache directory does not exist, falling back to direct bundling")
        return None

    # Add only cached NVIDIA binaries (no ONNX Runtime - let PyInstaller handle it)
    nvidia_cache = cache_dir / "nvidia"
    if nvidia_cache.exists():
        for subdir in nvidia_cache.iterdir():
            if subdir.is_dir() and (subdir / "bin").exists():
                for dll_file in (subdir / "bin").glob("*.dll"):
                    binaries.append((str(dll_file), f"nvidia/{subdir.name}/bin"))
                    logger.info(f"Using cached NVIDIA {subdir.name}: {dll_file}")

    return binaries

# Main hook logic
cached_mode = os.environ.get('CACHED_GPU_LIBS', '').lower() in ('1', 'true', 'yes')
skip_gpu_libs = os.environ.get('SKIP_GPU_LIBS', '').lower() in ('1', 'true', 'yes')
runtime_gpu_libs = os.environ.get('RUNTIME_GPU_LIBS', '').lower() in ('1', 'true', 'yes')

binaries = []

if skip_gpu_libs:
    logger.info("SKIP_GPU_LIBS is set, skipping all GPU libraries")
elif runtime_gpu_libs:
    logger.info("RUNTIME_GPU_LIBS is set, excluding only NVIDIA CUDA DLLs from executable for runtime loading")
    # Don't add NVIDIA binaries - they will be loaded at runtime from lib-cuda folder
    # Let PyInstaller handle ONNX Runtime normally - don't exclude it
    binaries = []
elif cached_mode:
    logger.info("CACHED_GPU_LIBS is set, using cached library approach")

    cache_dir = Path("./cache/gpu-libs")
    cache_complete = cache_dir / ".cache_complete"

    if not cache_complete.exists():
        logger.info("Cache not found or incomplete, creating cache...")
        binaries = cache_gpu_libraries()
    else:
        logger.info("Using existing cache...")
        cached_binaries = get_cached_binaries()
        if cached_binaries is not None:
            binaries = cached_binaries
        else:
            # Fallback to creating cache
            binaries = cache_gpu_libraries()
else:
    logger.info("Standard mode: bundling NVIDIA libraries directly (ONNX Runtime handled by PyInstaller)")
    # Standard direct bundling - only add NVIDIA binaries, let PyInstaller handle ONNX Runtime
    try:
        # Add only required NVIDIA binaries
        nvidia_pkg_paths = get_package_paths("nvidia")
        nvidia_base_path = Path(nvidia_pkg_paths[0]) / "nvidia"

        # Required DLLs for RIFE on ONNX CUDA engine
        REQUIRED_CUDA_DLLS = [
            "cublasLt64_12.dll",
            "cublas64_12.dll",
            "cufft64_11.dll",
            "cudart64_12.dll",
            "cudnn_engines_runtime_compiled64_9.dll",
            "cudnn_engines_precompiled64_9.dll",
            "cudnn_heuristic64_9.dll",
            "cudnn_ops64_9.dll",
            "cudnn_adv64_9.dll",
            "cudnn_graph64_9.dll",
            "cudnn64_9.dll"
        ]

        NVIDIA_PACKAGES = ["cublas", "cuda_nvrtc", "cuda_runtime", "cudnn", "cufft", "curand", "nvjitlink"]
        for package in NVIDIA_PACKAGES:
            package_path = nvidia_base_path / package
            bin_path = package_path / "bin"
            if bin_path.exists():
                for dll_file in bin_path.glob("*.dll"):
                    if dll_file.name in REQUIRED_CUDA_DLLS:
                        binaries.append((str(dll_file), f"nvidia/{package}/bin"))
                        logger.info(f"Adding required NVIDIA DLL: {dll_file.name}")

    except Exception as e:
        logger.error(f"Error in standard bundling: {e}")

logger.info(f"Hook completed. Total binaries: {len(binaries)}")