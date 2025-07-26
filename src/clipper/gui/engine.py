"""Core clipper engine that can be reused between CLI and GUI."""

import json
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from clipper import (
    argparser,
    clip_maker,
    clipper_types,
    util,
    ytc_logger,
    ytc_settings,
)
from clipper.clipper_types import ClipperState
from clipper.ffmpeg_version import getFfmpegVersion
from clipper.version import __version__
from clipper.ytc_logger import logger
from clipper.ytdl import ytdl_bin_get_version


class ClipperEngine:
    """Core clipper engine that can be reused between CLI and GUI."""

    # Class-level persistent cache for RIFE dependencies
    _PERSISTENT_RIFE_CACHE: Dict[str, Any] = {
        "__RIFE_LOADED": False
    }

    def __init__(self):
        """Initialize the clipper engine - ready to use immediately."""
        self.is_initialized = True  # Always ready since we do minimal initialization
        self.cs: Optional[ClipperState] = None
        self.logger = logging.getLogger(__name__)

    def process_files(self, markup_path: str, video_path: Optional[str] = None) -> Dict[str, Any]:
        """Process markup and optionally video files using exact CLI logic."""
        try:
            print(f"DEBUG: Starting file processing with CLI-identical logic...")

            # Validate markup file
            markup_file = Path(markup_path)
            if not markup_file.exists():
                return {"status": "error", "message": f"Markup file not found: {markup_path}"}

            # Create a fresh clipper state for this processing session
            self.cs = clipper_types.ClipperState()
            print("DEBUG: Created fresh ClipperState for processing")

            # Simulate the exact CLI argument flow
            # Build argv as if we called: yt_clipper --markers-json markup.json [--input-video video.mp4]
            simulated_argv = [
                "yt_clipper",
                "--markers-json", str(markup_file.absolute())
            ]

            if video_path:
                video_file = Path(video_path)
                if not video_file.exists():
                    return {"status": "error", "message": f"Video file not found: {video_path}"}
                simulated_argv.extend(["--input-video", str(video_file.absolute())])

            print(f"DEBUG: Simulating CLI with args: {simulated_argv}")

            # Temporarily replace sys.argv to simulate CLI call
            original_argv = sys.argv
            try:
                sys.argv = simulated_argv

                # Now run the exact CLI initialization flow
                args, unknown, argsFromArgFiles, argFiles, argsFromArgFilesMap = argparser.getArgs()

                self.cs.settings.update({"color_space": None, **args})

                # Preserve persistent RIFE cache across processing sessions
                if self._PERSISTENT_RIFE_CACHE["__RIFE_LOADED"]:
                    self.cs.settings["__RIFE_LOADED"] = True
                    print("DEBUG: Using persistent RIFE cache from previous session")

                ytc_settings.loadSettings(self.cs.settings)

                # Import the setup functions from the main CLI module
                from clipper.yt_clipper import setupDepPaths, setupOutputPaths

                setupDepPaths(self.cs)
                setupOutputPaths(self.cs)
                ytc_logger.setUpLogger(self.cs)

                print("DEBUG: Completed CLI-identical initialization")

                # Inject persistent RIFE cache into clip_maker module before processing
                self._inject_rife_cache()

                # Get input video and global settings (CLI flow)
                ytc_settings.getInputVideo(self.cs)
                ytc_settings.getGlobalSettings(self.cs)

                print("DEBUG: Starting clip processing...")

                # Process clips exactly like CLI
                if not self.cs.settings.get("preview", False):
                    clip_maker.makeClips(self.cs)
                    message = "Clips generated successfully"
                else:
                    clip_maker.previewClips(self.cs)
                    message = "Preview completed successfully"

                # Update persistent cache after processing (preserve RIFE loaded state)
                self._update_persistent_cache()

            finally:
                # Restore original argv
                sys.argv = original_argv

            # Get the report
            report = self.cs.reportStream.getvalue()

            return {
                "status": "success",
                "message": message,
                "report": report,
                "output_path": self.cs.clipper_paths.clipsPath
            }

        except Exception as e:
            error_msg = f"Processing failed: {e}"
            print(f"DEBUG ERROR: {error_msg}")
            import traceback
            traceback.print_exc()
            self.logger.error(error_msg)
            return {"status": "error", "message": str(e)}

    def get_status(self) -> Dict[str, Any]:
        """Get current status of the application."""
        return {
            "initialized": self.is_initialized,
            "engine_ready": self.is_initialized,
            "version": __version__
        }

    def _inject_rife_cache(self) -> None:
        """Inject persistent RIFE cache into clip_maker module."""
        # Only inject if we have previously loaded RIFE dependencies and have a valid clipper state
        if self._PERSISTENT_RIFE_CACHE["__RIFE_LOADED"] and self.cs:
            # Set the RIFE loaded flag in the current session settings
            # This prevents re-initialization of RIFE dependencies
            self.cs.settings["__RIFE_LOADED"] = True
            print("DEBUG: Injected persistent RIFE loaded state - skipping RIFE initialization")

    def _update_persistent_cache(self) -> None:
        """Update persistent cache with RIFE loaded state only."""
        # Only preserve the RIFE loaded state since the cache itself doesn't mutate
        # The main issue was garbage collection between processes, not cache mutation
        if self.cs and "__RIFE_LOADED" in self.cs.settings:
            self._PERSISTENT_RIFE_CACHE["__RIFE_LOADED"] = self.cs.settings["__RIFE_LOADED"]
            print(f"DEBUG: Updated persistent RIFE loaded state: {self._PERSISTENT_RIFE_CACHE['__RIFE_LOADED']}")

    def _setupDepPaths(self, cs: ClipperState) -> None:
        """Setup dependency paths (copied from yt_clipper.py)."""
        settings = cs.settings
        cp = cs.clipper_paths

        if getattr(sys, "frozen", False):
            cp.ffmpegPath = "./bin/ffmpeg"
            cp.ffprobePath = "./bin/ffprobe"
            cp.ffplayPath = "./bin/ffplay"
            cp.ytdlPath = "./bin/yt-dlp"

            if sys.platform == "win32":
                cp.ffmpegPath += ".exe"
                cp.ffprobePath += ".exe"
                cp.ffplayPath += ".exe"
                cp.ytdlPath += ".exe"

            if sys.platform == "darwin":
                cp.ytdlPath += "_macos"

                import certifi
                certifi_cacert_path = certifi.where()
                os.environ["SSL_CERT_FILE"] = certifi_cacert_path
                os.environ["REQUESTS_CA_BUNDLE"] = certifi_cacert_path

        if settings.get("ytdlLocation"):
            cp.ytdlPath = settings["ytdlLocation"]

        # Handle Topaz if needed
        self._prepareTopazFFmpeg(cs)

    def _prepareTopazFFmpeg(self, cs: ClipperState) -> None:
        """Prepare Topaz FFmpeg if configured."""
        topaz_path = cs.settings.get("topazAIPath", "")
        if not topaz_path:
            return

        topaz_dir = Path(topaz_path)
        if not topaz_dir.is_dir():
            topaz_dir = topaz_dir.parent

        ffmpeg_path = Path(str(topaz_dir / "ffmpeg.exe"))
        if not ffmpeg_path.is_file():
            raise FileNotFoundError(f"ffmpeg.exe not found in {topaz_dir}")

        cs.clipper_paths.ffmpegPath = str(ffmpeg_path).replace("\\", "/")

        model_data_dir = cs.settings.get("topazModelDataDir", "")
        model_dir = cs.settings.get("topazModelDir", "")
        if model_data_dir and model_dir:
            os.environ["TVAI_MODEL_DATA_DIR"] = model_data_dir
            os.environ["TVAI_MODEL_DIR"] = model_dir
            os.environ["CUDA_VISIBLE_DEVICES"] = "0"
            os.environ["CUDA_DEVICE_MAX_CONNECTIONS"] = "2"

    def _setupOutputPaths(self, cs: ClipperState) -> None:
        """Setup output paths (copied from yt_clipper.py)."""
        settings = cs.settings
        cp = cs.clipper_paths
        title_suffix = settings.get("titleSuffix", "")
        cp.clipsPath += f'/{title_suffix}' if title_suffix else ""

        os.makedirs(f"{cp.clipsPath}/temp", exist_ok=True)
        download_name_stem = settings.get("downloadVideoNameStem", "video")
        settings["downloadVideoPath"] = f'{cp.clipsPath}/{download_name_stem}'
