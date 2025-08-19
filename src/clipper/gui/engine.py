"""Core clipper engine that can be reused between CLI and GUI."""

import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, ClassVar, Dict, Optional

from clipper import (
    argparser,
    clip_maker,
    clipper_types,
    ytc_logger,
    ytc_settings,
)
from clipper.clipper_types import ClipperState
from clipper.version import __version__


class ClipperEngine:
    """Core clipper engine that can be reused between CLI and GUI."""

    # Class-level persistent cache for RIFE dependencies
    _PERSISTENT_RIFE_CACHE: ClassVar[Dict[str, Any]] = {
        "__RIFE_LOADED": False,
    }

    def __init__(self) -> None:
        """Initialize the clipper engine - ready to use immediately."""
        self.is_initialized = True  # Always ready since we do minimal initialization
        self.cs: Optional[ClipperState] = None
        self.logger = logging.getLogger(__name__)

    def process_files(self, markup_path: Optional[str] = None, video_path: Optional[str] = None,  # noqa: PLR0912
                     settings_overrides: Optional[Dict[str, Any]] = None,
                     markup_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process markup and optionally video files using exact CLI logic with GUI settings.

        Args:
            markup_path: Path to the markup JSON file (optional if markup_data provided)
            video_path: Optional path to input video file
            settings_overrides: Dict containing ONLY specific overrides not in GUI settings:
                - 'only': List of clip indices to process (0-indexed, will be converted to 1-indexed)
                - 'overwrite': Boolean to force overwrite existing clips
                - 'preview': Boolean to enable preview mode
            markup_data: Direct markup data (alternative to markup_path)
        """
        if markup_path is None and markup_data is None:
            return {"status": "error", "message": "Either markup_path or markup_data must be provided"}

        try:
            print(f"DEBUG: Starting file processing with CLI-identical logic and GUI settings...")

            # Validate inputs - either markup_path OR markup_data must be provided
            if markup_path:
                markup_file = Path(markup_path)
                if not markup_file.exists():
                    return {"status": "error", "message": f"Markup file not found: {markup_path}"}
                print(f"DEBUG: Using markup file: {markup_path}")
            elif markup_data:
                print("DEBUG: Using direct markup data")
            else:
                return {"status": "error", "message": "Either markup_path or markup_data must be provided"}

            # Create a fresh clipper state for this processing session
            self.cs = clipper_types.ClipperState()
            print("DEBUG: Created fresh ClipperState for processing")

            # Get comprehensive GUI settings
            from clipper.gui.settings_manager import SettingsManager
            settings_manager = SettingsManager()
            gui_settings = settings_manager.get_combined_settings()
            print(f"DEBUG: Loaded GUI settings: {len(gui_settings)} settings")

            # Build minimal argv for required arguments only (no settings)
            simulated_argv = ["yt_clipper"]

            # Add markup file argument if using file path, otherwise we'll inject data later
            if markup_path:
                simulated_argv.extend(["--markers-json", str(Path(markup_path).absolute())])
            else:
                # For markup_data, we need a placeholder that won't be used
                simulated_argv.extend(["--markers-json", "placeholder.json"])

            if video_path:
                video_file = Path(video_path)
                if not video_file.exists():
                    return {"status": "error", "message": f"Video file not found: {video_path}"}
                simulated_argv.extend(["--input-video", str(video_file.absolute())])

            # Handle ONLY the specific overrides that aren't part of GUI settings
            if settings_overrides:
                # Handle selected clips (convert list to comma-separated string)
                # Note: GUI clips are 0-indexed, but CLI expects 1-indexed values
                if 'only' in settings_overrides:
                    selected_clips = settings_overrides['only']
                    if isinstance(selected_clips, list) and len(selected_clips) > 0:
                        # Convert 0-indexed GUI clips to 1-indexed CLI format
                        one_indexed_clips = [str(i + 1) for i in selected_clips]
                        only_string = ','.join(one_indexed_clips)
                        simulated_argv.extend(["--only", only_string])
                        print(f"DEBUG: Added --only parameter: {only_string} (converted from 0-indexed {selected_clips})")

                # Handle overwrite flag (if explicitly set to True)
                if settings_overrides.get('overwrite') is True:
                    simulated_argv.append("--overwrite")

                # Handle preview mode (if explicitly set to True)
                if settings_overrides.get('preview') is True:
                    simulated_argv.append("--preview")

            # Pass empty argFiles arg to ignore arg files in GUI mode so they don't interfere
            simulated_argv.extend(["--arg-files", "''"])

            print(f"DEBUG: Simulating CLI with minimal args: {simulated_argv}")

            # Temporarily replace sys.argv to simulate CLI call
            original_argv = sys.argv
            try:
                sys.argv = simulated_argv

                # Run the CLI initialization flow (minimal args only)
                args, unknown, argsFromArgFiles, argFiles, argsFromArgFilesMap = argparser.getArgs()

                # Apply CLI arguments first to get the json path and other required settings
                self.cs.settings.update({"color_space": None, **args})

                # Apply GUI settings directly to clipper state BEFORE loading JSON
                # This ensures GUI settings serve as the base, with JSON able to override them
                print(f"DEBUG: Applying GUI settings to clipper state...")
                self._apply_gui_settings_to_clipper_state(gui_settings)

                # Load settings - either from markup data or JSON file
                if markup_data:
                    print("DEBUG: Loading settings with direct markup data")
                    # Handle custom output directory from markup data before setting up paths
                    if 'outputDirectory' in markup_data:
                        self.cs.settings['outputDirectory'] = markup_data['outputDirectory']
                    ytc_settings.loadSettings(self.cs.settings, markup_data)
                else:
                    print("DEBUG: Loading settings from JSON file")
                    ytc_settings.loadSettings(self.cs.settings)

                # Preserve persistent RIFE cache across processing sessions
                if self._PERSISTENT_RIFE_CACHE["__RIFE_LOADED"]:
                    self.cs.settings["__RIFE_LOADED"] = True
                    print("DEBUG: Using persistent RIFE cache from previous session")

                # Import the setup functions from the main CLI module
                from clipper.yt_clipper import setupDepPaths, setupOutputPaths

                setupDepPaths(self.cs)

                # Handle custom output directory from mock markup before setting up paths
                if 'outputDirectory' in self.cs.settings and self.cs.settings['outputDirectory']:
                    # Use the custom output directory instead of default webms
                    self.cs.clipper_paths.clipsPath = self.cs.settings['outputDirectory']
                    self.cs.settings["titleSuffix"] = self.cs.settings.get("videoTitle", "standalone-video")
                    self.cs.settings["downloadVideoNameStem"] = f"{self.cs.settings["titleSuffix"]}"
                    self.cs.settings["downloadVideoPath"] = f'{self.cs.clipper_paths.clipsPath}/{self.cs.settings["downloadVideoNameStem"]}'
                    os.makedirs(f"{self.cs.clipper_paths.clipsPath}/temp", exist_ok=True)
                else:
                    setupOutputPaths(self.cs)

                ytc_logger.setUpLogger(self.cs)

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
                "output_path": self.cs.clipper_paths.clipsPath,
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
            "version": __version__,
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

    def _apply_gui_settings_to_clipper_state(self, gui_settings: Dict[str, Any]) -> None:
        """Apply GUI settings directly to clipper state.

        This method applies GUI settings as the base configuration.
        The markup JSON will be loaded afterward and can override these settings.
        Only applies settings that should come from GUI, not from markup JSON.
        """
        if not self.cs:
            return

        # Map of GUI settings to clipper state keys that are safe to apply
        # These are settings that control processing behavior, not video metadata
        safe_gui_settings = {
            # Logging settings
            'log_level': 'logLevel',
            'no_rich_logs': 'noRichLogs',

            # Input settings
            'download_video': 'downloadVideo',
            'format': 'format',
            'format_sort': 'formatSort',
            'no_auto_find_input_video': 'noAutoFindInputVideo',
            'enable_video_streaming_protocol_hls': 'enableVideoStreamingProtocolHLS',

            # Output settings
            'audio': 'audio',
            'fast_trim': 'fastTrim',
            'target_max_bitrate': 'targetMaxBitrate',
            'h264_disable_reduce_stutter': 'h264DisableReduceStutter',
            'auto_subs_lang': 'autoSubsLang',
            'subs_file_path': 'subsFilePath',
            'subs_style': 'subsStyle',
            'no_auto_scale_crop_res': 'noAutoScaleCropRes',
            'remove_metadata': 'removeMetadata',
            'extra_ffmpeg_args': 'extraFfmpegArgs',
            'extra_video_filters': 'extraVideoFilters',
            'extra_audio_filters': 'extraAudioFilters',
            'target_size': 'targetSize',
            'overwrite': 'overwrite',

            # AI/GPU settings
            'gpu_id': 'gpuId',
            'rife_model_path': 'rifeModelPath',
            'rife_worker_threads': 'rifeWorkerThreads',
            'topaz_ai_path': 'topazAIPath',
            'topaz_model_dir': 'topazModelDir',
            'topaz_model_data_dir': 'topazModelDataDir',

            # Other settings
            'preview': 'preview',
            'notify_on_completion': 'notifyOnCompletion',

            # yt-dlp settings
            'ytdl_location': 'ytdlLocation',
            'ytdl_username': 'username',
            'ytdl_password': 'password',
            'ytdl_auto_update': 'ytdlAutoUpdate',
            'cookiefile': 'cookiefile',
        }

        applied_count = 0
        for gui_key, clipper_key in safe_gui_settings.items():
            if gui_key in gui_settings:
                value = gui_settings[gui_key]
                # Only apply non-None, non-empty values
                if value is not None and value != '':
                    self.cs.settings[clipper_key] = value
                    applied_count += 1

        print(f"DEBUG: Applied {applied_count} GUI settings to clipper state (safe settings only)")
        print(f"DEBUG: Markup JSON will load next and can override these settings")
