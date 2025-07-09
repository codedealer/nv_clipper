# filepath: hooks/hook-onnxruntime.py
import os
import sys
from pathlib import Path

from PyInstaller.utils.hooks import get_package_paths
import logging

logger = logging.getLogger(__name__)

# onnxruntime-gpu ships with a lot of dlls that need to be bundled.
# This hook is a master-hook that bundles all required onnxruntime
# dlls, as well as all required cuda/cudnn/cublas etc dlls.
# It is also responsible for bundling the tensorrt dlls if they are
# available.

# This hook is executed by pyinstaller, and is not part of the
# main application.

# Add the onnxruntime package path to the path, so that we can
# import the version module.
pkg_path = get_package_paths("onnxruntime")[0]
sys.path.append(str(pkg_path))
# We can now import the version module.
from onnxruntime import __version__ as onnxruntime_version

logger.info(f"Discovered onnxruntime version: {onnxruntime_version}")

# Get the onnxruntime package path.
onnxruntime_pkg_paths = get_package_paths("onnxruntime")
logger.info(f"onnxruntime package paths: {onnxruntime_pkg_paths}")

# Find the actual onnxruntime directory within site-packages
site_packages = Path(onnxruntime_pkg_paths[0])
onnxruntime_path = site_packages / "onnxruntime"
logger.info(f"onnxruntime package path: {onnxruntime_path}")

# Add the onnxruntime binaries to the bundle.
binaries = [(str(onnxruntime_path / "capi" / "*.dll"), "onnxruntime/capi")]

# Add the nvidia package paths to the path.
# The NVIDIA packages install into a shared nvidia/ namespace directory
NVIDIA_PACKAGES = [
    "cublas",
    "cuda_nvrtc",
    "cuda_runtime",
    "cudnn",
    "cufft",
    "curand",
    "nvjitlink",
]

# Get the nvidia namespace directory path
try:
    nvidia_pkg_paths = get_package_paths("nvidia")
    logger.info(f"nvidia package paths: {nvidia_pkg_paths}")

    # The nvidia directory is within site-packages
    site_packages = Path(nvidia_pkg_paths[0])
    nvidia_base_path = site_packages / "nvidia"
    logger.info(f"nvidia namespace path: {nvidia_base_path}")

    for package in NVIDIA_PACKAGES:
        package_path = nvidia_base_path / package
        bin_path = package_path / "bin"
        if bin_path.exists():
            logger.info(f"Adding binaries from {package_path}")
            binaries.append((str(bin_path / "*.dll"), f"nvidia/{package}/bin"))
        else:
            logger.info(f"No bin folder found for {package}, skipping.")

except (ImportError, IndexError):
    logger.info("nvidia namespace package not found, skipping cuda/cudnn/cublas etc dlls.")
    pass