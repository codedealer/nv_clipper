"""Main GUI application using pywebview."""

import json
import logging
import subprocess
import tempfile
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import webview
from webview.dom import DOMEventHandler

# Use absolute imports so PyInstaller frozen app finds modules without package context
from clipper.cache_manager import get_cache_manager
from clipper.gui.engine import ClipperEngine
from clipper.gui.settings_manager import SettingsManager


class ClipperGUI:
    """GUI API class for pywebview."""

    def __init__(self) -> None:
        self.engine = ClipperEngine()  # Initialize immediately
        self.settings_manager = SettingsManager()  # Initialize settings manager
        self.cache_manager = get_cache_manager()  # Initialize cache manager

        # Configure cache manager with current settings
        self._update_cache_manager_settings()

        self.is_initialized = True     # Always ready since initialization is minimal
        self.logger = logging.getLogger(__name__)
        self.processing_jobs = {}      # Track processing jobs by ID
        self.job_lock = threading.Lock()

        # Drag and drop state
        self.current_files = []        # Store current dropped files for processing

    def _update_cache_manager_settings(self) -> None:
        """Update cache manager with current settings."""
        try:
            general_settings = self.settings_manager.get_general_settings()
            cache_dir = general_settings.get('cache_folder_path', '')
            max_size_mb = general_settings.get('cache_max_size_mb', 5000)

            # Use default if cache_folder_path is empty (should be handled by dataclass now)
            if not cache_dir:
                from pathlib import Path
                cache_dir = str(Path.home() / ".nv_clipper" / "cache")

            self.cache_manager.update_cache_settings(cache_dir, max_size_mb)
        except Exception as e:
            self.logger.error(f"Failed to update cache manager settings: {e}")

    def process_files(self, markup_path: str, video_path: Optional[str] = None,
                     selected_clips: Optional[List[int]] = None) -> Dict[str, Any]:
        """Process files using the engine in a separate thread"""
        # Create a unique job ID
        job_id = str(uuid.uuid4())

        # Initialize job status
        with self.job_lock:
            self.processing_jobs[job_id] = {
                "status": "starting",
                "message": "Initializing processing...",
                "result": None,
                "started_at": time.time(),
            }

        # Start processing in a separate thread
        def process_worker() -> None:
            try:
                self.logger.info(f"Starting processing job {job_id}")

                # Update status to processing
                with self.job_lock:
                    self.processing_jobs[job_id].update({
                        "status": "processing",
                        "message": "Processing files...",
                    })

                # Get current settings and convert to CLI format
                settings_overrides = self.settings_manager.get_combined_settings()

                # Add selected clips if provided
                if selected_clips is not None:
                    settings_overrides['only'] = selected_clips

                # Call the engine processing with settings
                result = self.engine.process_files(markup_path, video_path, settings_overrides)

                # Update with final result
                with self.job_lock:
                    self.processing_jobs[job_id].update({
                        "status": "completed",
                        "result": result,
                        "completed_at": time.time(),
                    })

                self.logger.info(f"Completed processing job {job_id}: {result['status']}")

            except Exception as e:
                self.logger.error(f"Processing job {job_id} failed: {e}")

                # Update with error result
                with self.job_lock:
                    self.processing_jobs[job_id].update({
                        "status": "completed",
                        "result": {"status": "error", "message": str(e)},
                        "completed_at": time.time(),
                    })

        # Start the worker thread
        thread = threading.Thread(target=process_worker, daemon=True)
        thread.start()

        # Return job ID for status tracking
        return {"status": "accepted", "job_id": job_id, "message": "Processing started"}

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of a processing job"""
        with self.job_lock:
            if job_id not in self.processing_jobs:
                return {"status": "error", "message": "Job not found"}

            job = self.processing_jobs[job_id].copy()

            # If job is completed, return the result and clean up after some time
            if job["status"] == "completed":
                result = job["result"]

                # Clean up old completed jobs (older than 10 minutes)
                current_time = time.time()
                if current_time - job.get("completed_at", current_time) > 600:
                    del self.processing_jobs[job_id]

                return result

            # Return current status for ongoing jobs
            return {
                "status": job["status"],
                "message": job["message"],
                "job_id": job_id,
            }

    def cleanup_old_jobs(self) -> Dict[str, int]:
        """Clean up old completed jobs to prevent memory leaks"""
        current_time = time.time()
        with self.job_lock:
            job_ids_to_remove = []
            for job_id, job in self.processing_jobs.items():
                if (job["status"] == "completed" and
                    current_time - job.get("completed_at", current_time) > 600):
                    job_ids_to_remove.append(job_id)

            for job_id in job_ids_to_remove:
                del self.processing_jobs[job_id]

        return {"cleaned": len(job_ids_to_remove)}

    def get_status(self) -> Dict[str, Any]:
        """Get current status of the application"""
        return self.engine.get_status()

    def select_files(self) -> Optional[List[str]]:
        """Open file dialog to select files"""
        result = webview.windows[0].create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=True,
            file_types=('JSON files (*.json)', 'Video files (*.mp4;*.webm;*.avi;*.mkv)', 'All files (*.*)'),
        )
        return list(result) if result else None

    def parse_markup_file(self, file_path: str) -> Dict[str, Any]:
        """Parse a JSON markup file and return clip information"""
        try:
            with open(file_path, encoding='utf-8') as f:
                data = json.load(f)

            # Extract clips from markerPairs
            clips = []
            marker_pairs = data.get('markerPairs', [])
            video_title = data.get('videoTitle', 'Unknown Video')
            title_suffix = data.get('titleSuffix', 'clip')

            for marker in marker_pairs:
                clip = {
                    'number': marker.get('number', len(clips) + 1),
                    'title': f"{title_suffix}-{marker.get('number', len(clips) + 1)}",
                    'start': marker.get('start', 0),
                    'end': marker.get('end', 0),
                    'duration': marker.get('end', 0) - marker.get('start', 0),
                    'speed': marker.get('speed', 1),
                    'crop': marker.get('crop', ''),
                    'enableZoomPan': marker.get('enableZoomPan', False),
                    'overrides': marker.get('overrides', {}),
                }
                clips.append(clip)

            return {
                'status': 'success',
                'clips': clips,
                'video_info': {
                    'title': video_title,
                    'video_url': data.get('videoUrl', ''),
                    'video_id': data.get('videoID', ''),
                    'platform': data.get('platform', ''),
                    'is_vertical': data.get('isVerticalVideo', False),
                    'crop_res': data.get('cropRes', ''),
                    'version': data.get('version', ''),
                },
            }

        except Exception as e:
            self.logger.error(f"Failed to parse markup file {file_path}: {e}")
            return {
                'status': 'error',
                'message': f"Failed to parse markup file: {e!s}",
            }

    # Settings Management API

    def get_general_settings(self) -> Dict[str, Any]:
        """Get current general settings"""
        return {
            'status': 'success',
            'settings': self.settings_manager.get_general_settings(),
        }

    def get_video_settings(self) -> Dict[str, Any]:
        """Get current video-specific settings"""
        return {
            'status': 'success',
            'settings': self.settings_manager.get_video_settings(),
        }

    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings (general + video)"""
        return {
            'status': 'success',
            'general': self.settings_manager.get_general_settings(),
            'video': self.settings_manager.get_video_settings(),
        }

    def get_settings_schema(self) -> Dict[str, Any]:
        """Get settings schema for the frontend"""
        return {
            'status': 'success',
            'schema': self.settings_manager.get_settings_schema(),
        }

    def update_general_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update general settings"""
        try:
            success = self.settings_manager.update_general_settings(settings)
            if success:
                # Update cache manager settings if cache-related settings changed
                if 'cache_folder_path' in settings or 'cache_max_size_mb' in settings:
                    self._update_cache_manager_settings()

                return {
                    'status': 'success',
                    'message': f'Updated {len(settings)} general settings',
                    'settings': self.settings_manager.get_general_settings(),
                }
            return {
                'status': 'error',
                'message': 'Failed to update general settings',
            }
        except Exception as e:
            self.logger.error(f"Failed to update general settings: {e}")
            return {
                'status': 'error',
                'message': f'Failed to update settings: {e!s}',
            }

    def update_video_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update video-specific settings"""
        try:
            success = self.settings_manager.update_video_settings(settings)
            if success:
                return {
                    'status': 'success',
                    'message': f'Updated {len(settings)} video settings',
                    'settings': self.settings_manager.get_video_settings(),
                }
            return {
                'status': 'error',
                'message': 'Failed to update video settings',
            }
        except Exception as e:
            self.logger.error(f"Failed to update video settings: {e}")
            return {
                'status': 'error',
                'message': f'Failed to update settings: {e!s}',
            }

    def reset_settings_to_defaults(self) -> Dict[str, Any]:
        """Reset all settings to defaults"""
        try:
            self.settings_manager.reset_to_defaults()
            return {
                'status': 'success',
                'message': 'Reset all settings to defaults',
                'general': self.settings_manager.get_general_settings(),
                'video': self.settings_manager.get_video_settings(),
            }
        except Exception as e:
            self.logger.error(f"Failed to reset settings: {e}")
            return {
                'status': 'error',
                'message': f'Failed to reset settings: {e!s}',
            }

    def export_settings_to_args_file(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Export current settings to args file"""
        try:
            path = Path(file_path) if file_path else None
            result_path = self.settings_manager.export_to_args_file(path)
            return {
                'status': 'success',
                'message': f'Exported settings to {result_path}',
                'file_path': str(result_path),
            }
        except Exception as e:
            self.logger.error(f"Failed to export settings: {e}")
            return {
                'status': 'error',
                'message': f'Failed to export settings: {e!s}',
            }

    def import_settings_from_args_file(self, file_path: str) -> Dict[str, Any]:
        """Import settings from args file"""
        try:
            success = self.settings_manager.import_from_args_file(Path(file_path))
            if success:
                return {
                    'status': 'success',
                    'message': f'Imported settings from {file_path}',
                    'general': self.settings_manager.get_general_settings(),
                    'video': self.settings_manager.get_video_settings(),
                }
            return {
                'status': 'error',
                'message': f'Failed to import settings from {file_path}',
            }
        except Exception as e:
            self.logger.error(f"Failed to import settings: {e}")
            return {
                'status': 'error',
                'message': f'Failed to import settings: {e!s}',
            }

    # Video Cache Management Methods

    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the video cache"""
        try:
            info = self.cache_manager.get_cache_info()
            return {
                'status': 'success',
                'data': info,
            }
        except Exception as e:
            self.logger.error(f"Failed to get cache info: {e}")
            return {
                'status': 'error',
                'message': f'Failed to get cache info: {e!s}',
            }

    def download_video_to_cache(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Download a video to cache"""
        try:
            # Debug: log the entire request to see what we're receiving
            self.logger.info(f"Cache download request received: {request}")

            url = request.get('url')
            if not url:
                return {
                    'status': 'error',
                    'message': 'URL is required',
                }

            # Get current settings - we ALWAYS need ytdl_location and auto_update from settings
            general_settings = self.settings_manager.get_general_settings()

            # Prepare download parameters
            download_params = {
                'url': url,
                'title': request.get('title'),
                'ytdl_location': general_settings.get('ytdl_location'),  # Always use from settings
                'auto_update': request.get('auto_update', general_settings.get('ytdl_auto_update', True)),
            }

            # Only add format settings if use_settings_format is True
            if request.get('use_settings_format', False):
                download_params['format_spec'] = general_settings.get('format')
                download_params['format_sort'] = general_settings.get('format_sort')
            else:
                # Use explicit format settings from request, or None for defaults
                download_params['format_spec'] = request.get('format')
                download_params['format_sort'] = request.get('format_sort')

            self.logger.info(f"Download parameters: {download_params}")

            result = self.cache_manager.download_video(**download_params)

            return result

        except Exception as e:
            self.logger.error(f"Failed to download video: {e}")
            return {
                'status': 'error',
                'message': f'Failed to download video: {e!s}',
            }

    def get_download_progress(self, video_id: str) -> Dict[str, Any]:
        """Get download progress for a video"""
        try:
            return self.cache_manager.get_download_progress(video_id)
        except Exception as e:
            self.logger.error(f"Failed to get download progress: {e}")
            return {
                'status': 'error',
                'message': f'Failed to get download progress: {e!s}',
            }

    def delete_cached_video(self, video_id: str) -> Dict[str, Any]:
        """Delete a cached video"""
        try:
            return self.cache_manager.delete_cached_video(video_id)
        except Exception as e:
            self.logger.error(f"Failed to delete cached video: {e}")
            return {
                'status': 'error',
                'message': f'Failed to delete cached video: {e!s}',
            }

    def purge_cache(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Purge cache based on options"""
        try:
            result = self.cache_manager.purge_cache(
                older_than_days=options.get('older_than_days'),
                size_limit_mb=options.get('size_limit_mb'),
                keep_most_recent=options.get('keep_most_recent'),
            )
            return result
        except Exception as e:
            self.logger.error(f"Failed to purge cache: {e}")
            return {
                'status': 'error',
                'message': f'Failed to purge cache: {e!s}',
            }

    def update_video_access_time(self, video_id: str) -> Dict[str, Any]:
        """Update the last accessed time for a cached video"""
        try:
            return self.cache_manager.update_video_access_time(video_id)
        except Exception as e:
            self.logger.error(f"Failed to update video access time: {e}")
            return {
                'status': 'error',
                'message': f'Failed to update video access time: {e!s}',
            }

    # Drag and Drop Support

    def on_drop(self, e: Dict[str, Any]) -> None:
        """Handle drop events and extract file paths with proper validation"""
        try:
            self.logger.info("Drop event received")

            # Validate event structure
            if not isinstance(e, dict):
                self.logger.error("Invalid drop event: not a dictionary")
                return

            data_transfer = e.get('dataTransfer')
            if not isinstance(data_transfer, dict):
                self.logger.error("Invalid drop event: no dataTransfer")
                return

            files = data_transfer.get('files')
            if not isinstance(files, list) or not files:
                self.logger.warning("No files found in drop event")
                return

            # Extract and validate file paths
            file_paths = []
            for i, file in enumerate(files):
                if not isinstance(file, dict):
                    self.logger.warning(f"Skipping invalid file entry at index {i}")
                    continue

                path = file.get('pywebviewFullPath')
                if not isinstance(path, str) or not path.strip():
                    self.logger.warning(f"Skipping file with invalid path at index {i}")
                    continue

                # Validate that the path exists
                if not Path(path).exists():
                    self.logger.warning(f"Skipping non-existent file: {path}")
                    continue

                file_paths.append(path)
                self.logger.info(f"Validated dropped file: {path}")

            if not file_paths:
                self.logger.warning("No valid files found in drop event")
                return

            # Store validated files
            self.current_files = file_paths
            self.logger.info(f"Successfully stored {len(file_paths)} valid files")

            # Safely notify frontend
            self._notify_frontend_of_dropped_files(file_paths)

        except Exception as ex:
            self.logger.error(f"Error handling drop event: {ex}", exc_info=True)

    def _notify_frontend_of_dropped_files(self, file_paths: List[str]) -> None:
        """Safely notify frontend of dropped files"""
        try:
            if not webview.windows:
                self.logger.error("No webview windows available for notification")
                return

            window = webview.windows[0]
            if not window:
                self.logger.error("Primary webview window is None")
                return

            # Safely serialize file paths for JavaScript
            try:
                files_json = json.dumps(file_paths)
            except (TypeError, ValueError) as e:
                self.logger.error(f"Failed to serialize file paths to JSON: {e}")
                return

            # Execute JavaScript with error handling
            js_code = f"""
            try {{
                if (typeof window.handleDroppedFiles === 'function') {{
                    window.handleDroppedFiles({files_json});
                }} else {{
                    console.warn('handleDroppedFiles function not available');
                }}
            }} catch (error) {{
                console.error('Error calling handleDroppedFiles:', error);
            }}
            """

            window.evaluate_js(js_code)
            self.logger.info("Successfully notified frontend of dropped files")

        except Exception as e:
            self.logger.error(f"Failed to notify frontend: {e}", exc_info=True)

    def get_current_files(self) -> Dict[str, Any]:
        """Get current dropped files with validation"""
        try:
            # Validate that stored files still exist
            valid_files = []
            for file_path in self.current_files:
                if Path(file_path).exists():
                    valid_files.append(file_path)
                else:
                    self.logger.warning(f"Stored file no longer exists: {file_path}")

            # Update stored files to only include valid ones
            if len(valid_files) != len(self.current_files):
                self.current_files = valid_files
                self.logger.info(f"Updated stored files list, {len(valid_files)} valid files remain")

            return {
                'status': 'success',
                'files': valid_files.copy(),
                'count': len(valid_files),
            }

        except Exception as e:
            self.logger.error(f"Error getting current files: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': f'Failed to get current files: {e!s}',
                'files': [],
                'count': 0,
            }

    def clear_current_files(self) -> Dict[str, Any]:
        """Clear the current dropped files"""
        try:
            previous_count = len(self.current_files)
            self.current_files = []
            self.logger.info(f"Cleared {previous_count} stored files")

            return {
                'status': 'success',
                'message': f'Cleared {previous_count} files',
                'previous_count': previous_count,
            }

        except Exception as e:
            self.logger.error(f"Error clearing current files: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': f'Failed to clear files: {e!s}',
            }

    def setup_drag_drop(self) -> Dict[str, Any]:
        """Setup drag and drop with comprehensive error handling"""
        try:
            self.logger.info("Setting up drag and drop events")

            # Validate webview state
            if not webview.windows:
                error_msg = "No webview windows available"
                self.logger.error(error_msg)
                return {'status': 'error', 'message': error_msg}

            window = webview.windows[0]
            if not window:
                error_msg = "Primary webview window is None"
                self.logger.error(error_msg)
                return {'status': 'error', 'message': error_msg}

            # Check if DOM is available
            if not hasattr(window, 'dom') or not window.dom:
                error_msg = "DOM not available on webview window"
                self.logger.error(error_msg)
                return {'status': 'error', 'message': error_msg}

            # Bind drop event with proper error handling
            try:
                window.dom.document.events.drop += DOMEventHandler(self.on_drop, True, True)  # type: ignore
                self.logger.info("Drop event handler bound successfully")
            except Exception as bind_error:
                error_msg = f"Failed to bind drop event: {bind_error}"
                self.logger.error(error_msg, exc_info=True)
                return {'status': 'error', 'message': error_msg}

            return {
                'status': 'success',
                'message': 'Drag and drop setup completed successfully',
            }

        except Exception as e:
            error_msg = f"Failed to setup drag and drop: {e}"
            self.logger.error(error_msg, exc_info=True)
            return {'status': 'error', 'message': error_msg}

    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """Get video information including duration and other properties.

        Args:
            video_path: Path to the video file

        Returns:
            Dict with status, message, and video info for success
        """
        try:
            from clipper.clipper_types import ClipperState, ClipperPaths
            from clipper.ffprobe import ffprobeVideoProperties

            self.logger.info(f"Getting video info for {video_path}")

            # Validate video file exists
            video_file = Path(video_path)
            if not video_file.exists():
                return {
                    'status': 'error',
                    'message': f'Video file not found: {video_path}'
                }

            # Create a clipper state with default paths and required settings for ffprobe
            cs = ClipperState(
                settings={
                    'platform': 'ytc_generic'  # Required for ffprobe
                },
                clipper_paths=ClipperPaths()
            )

            # Use ffprobe to get video properties
            video_properties = ffprobeVideoProperties(cs, str(video_file))

            if not video_properties:
                return {
                    'status': 'error',
                    'message': 'Failed to get video properties with ffprobe'
                }

            # Extract duration from format info if available
            duration = None
            if 'duration' in video_properties:
                duration = float(video_properties['duration'])

            # Return formatted video info
            return {
                'status': 'success',
                'message': 'Video info retrieved successfully',
                'video_info': {
                    'duration': duration,
                    'width': video_properties.get('width'),
                    'height': video_properties.get('height'),
                    'codec_name': video_properties.get('codec_name'),
                    'bit_rate': video_properties.get('bit_rate'),
                    'frame_rate': video_properties.get('r_frame_rate'),
                    'path': str(video_file)
                }
            }

        except Exception as e:
            self.logger.error(f"Error getting video info: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': f'Failed to get video info: {e!s}'
            }

    def create_temp_markup_file(self, markup_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a temporary markup file from markup data.

        Args:
            markup_data: Dictionary containing the markup structure

        Returns:
            Dict with status, message, and temp_file_path for success
        """
        try:
            import json
            import tempfile

            self.logger.info("Creating temporary markup file for processing")

            # Create a temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                json.dump(markup_data, temp_file, indent=2)
                temp_file_path = temp_file.name

            self.logger.info(f"Created temporary markup file: {temp_file_path}")

            return {
                'status': 'success',
                'message': 'Temporary markup file created',
                'temp_file_path': temp_file_path
            }

        except Exception as e:
            self.logger.error(f"Error creating temporary markup file: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': f'Failed to create temporary markup file: {e!s}'
            }

    def generate_frame_preview(self, video_path: str, timestamp: float,
                             color_grading: Optional[str] = None,
                             resolution_scale: float = 1.0) -> Dict[str, Any]:
        """Generate a frame preview with optional color grading filters.

        Args:
            video_path: Path to the video file
            timestamp: Time in seconds to extract frame from
            color_grading: Optional FFmpeg color grading filter string
            resolution_scale: Scale factor for output resolution (0.25, 0.5, 1.0)

        Returns:
            Dict with status, message, and base64_image for success
        """
        try:
            import base64
            from subprocess import PIPE

            self.logger.info(f"Generating frame preview for {video_path} at {timestamp}s")

            # Validate inputs
            video_file = Path(video_path)
            if not video_file.exists():
                return {
                    'status': 'error',
                    'message': f'Video file not found: {video_path}'
                }

            if timestamp < 0:
                return {
                    'status': 'error',
                    'message': 'Timestamp must be non-negative'
                }

            if resolution_scale not in [0.25, 0.5, 1.0]:
                return {
                    'status': 'error',
                    'message': 'Resolution scale must be 0.25, 0.5, or 1.0'
                }

            # Build FFmpeg command to output JPEG to stdout
            ffmpeg_cmd = [
                'ffmpeg',
                '-ss', str(timestamp),  # Seek to timestamp
                '-i', str(video_file),  # Input video
                '-vframes', '1',        # Extract one frame
                '-f', 'image2pipe',     # Output as image pipe
                '-vcodec', 'mjpeg',     # JPEG codec
                '-q:v', '2'             # High quality JPEG
            ]

            # Build video filter chain
            filters = []

            # Add scaling if needed
            if resolution_scale != 1.0:
                filters.append(f'scale=iw*{resolution_scale}:ih*{resolution_scale}')

            # Add color grading if provided
            if color_grading:
                from clipper.ffmpeg_filter import _validate_color_grading_filter
                if _validate_color_grading_filter(color_grading):
                    filters.append(color_grading)
                else:
                    return {
                        'status': 'error',
                        'message': 'Invalid color grading filter string'
                    }

            # Apply filters if any
            if filters:
                ffmpeg_cmd.extend(['-vf', ','.join(filters)])

            # Output to stdout (pipe)
            ffmpeg_cmd.append('pipe:1')

            # Execute FFmpeg command and capture stdout
            self.logger.debug(f"FFmpeg command: {' '.join(ffmpeg_cmd)}")
            result = subprocess.run(
                ffmpeg_cmd,
                stdout=PIPE,
                stderr=PIPE,
                timeout=30  # 30 second timeout
            )

            if result.returncode != 0:
                return {
                    'status': 'error',
                    'message': f'FFmpeg failed: {result.stderr.decode()}'
                }

            # Check if we got image data
            if not result.stdout:
                return {
                    'status': 'error',
                    'message': 'Frame extraction failed - no output generated'
                }

            # Encode the image data as base64
            image_base64 = base64.b64encode(result.stdout).decode('utf-8')

            self.logger.info(f"Frame preview generated successfully (base64, {len(image_base64)} chars)")
            return {
                'status': 'success',
                'message': 'Frame preview generated',
                'base64_image': image_base64,
                'mime_type': 'image/jpeg',
                'timestamp': timestamp,
                'resolution_scale': resolution_scale
            }

        except subprocess.TimeoutExpired:
            return {
                'status': 'error',
                'message': 'Frame extraction timed out'
            }
        except Exception as e:
            self.logger.error(f"Error generating frame preview: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': f'Failed to generate frame preview: {e!s}'
            }

    # Window State Management API

    def save_window_state(self, width: int, height: int, maximized: bool = False) -> Dict[str, Any]:
        """Save the current window state to settings"""
        try:
            success = self.settings_manager.update_general_settings({
                'window_width': width,
                'window_height': height,
                'window_maximized': maximized
            })

            if success:
                return {
                    'status': 'success',
                    'message': 'Window state saved successfully'
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Failed to save window state'
                }
        except Exception as e:
            self.logger.error(f"Error saving window state: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': f'Failed to save window state: {e!s}'
            }

    def get_window_state(self) -> Dict[str, Any]:
        """Get the saved window state from settings"""
        try:
            settings = self.settings_manager.get_general_settings()
            return {
                'status': 'success',
                'width': settings.get('window_width', 1000),
                'height': settings.get('window_height', 800),
                'maximized': settings.get('window_maximized', False)
            }
        except Exception as e:
            self.logger.error(f"Error getting window state: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': f'Failed to get window state: {e!s}',
                'width': 1000,  # fallback defaults
                'height': 800,
                'maximized': False
            }


def create_app(dev_mode: bool = False, dev_url: str = "http://localhost:5173") -> webview.Window:
    """Create and configure the webview application"""
    api = ClipperGUI()

    # Get saved window state
    window_state = api.get_window_state()
    width = window_state.get('width', 1000)
    height = window_state.get('height', 800)
    maximized = window_state.get('maximized', False)

    # Debouncing mechanism for window state changes
    window_state_timer = None
    last_saved_state = {'width': width, 'height': height, 'maximized': maximized}

    if dev_mode:
        # Development mode: use Vite dev server
        url = dev_url
        print(f"Development mode: connecting to Vite dev server at {url}")
    else:
        # Production mode: use built frontend from Vite
        frontend_path = Path(__file__).parent / "dist" / "index.html"

        if not frontend_path.exists():
            raise FileNotFoundError(
                f"Frontend not found at {frontend_path}. "
                "Please build the frontend first: cd src/gui-frontend && pnpm run build",
            )

        url = frontend_path.as_uri()

    window = webview.create_window(
        'NV Clipper GUI',
        url,
        js_api=api,
        width=width,
        height=height,
        resizable=True,
        min_size=(800, 600),
        maximized=maximized,
    )

    def save_window_state_debounced(new_width: int, new_height: int, new_maximized: bool) -> None:
        """Save window state with debouncing to avoid excessive I/O"""
        nonlocal window_state_timer, last_saved_state

        # Cancel existing timer if any
        if window_state_timer is not None:
            window_state_timer.cancel()

        # Only save if state has actually changed to avoid unnecessary I/O
        current_state = {'width': new_width, 'height': new_height, 'maximized': new_maximized}
        if current_state == last_saved_state:
            return

        def save_state():
            try:
                result = api.save_window_state(new_width, new_height, new_maximized)
                if result['status'] == 'success':
                    last_saved_state.update(current_state)
                    api.logger.debug(f"Window state saved: {new_width}x{new_height}, maximized: {new_maximized}")
                else:
                    api.logger.warning(f"Failed to save window state: {result.get('message')}")
            except Exception as e:
                api.logger.error(f"Error saving window state: {e}", exc_info=True)

        # Start new debounced timer (500ms delay)
        window_state_timer = threading.Timer(0.5, save_state)
        window_state_timer.start()

    # Define event handlers for window state management
    def on_window_resized(width: int, height: int) -> None:
        """Handle window resize events and save new size to settings (debounced)"""
        try:
            # Save the new window size (not maximized since it was resized)
            save_window_state_debounced(width, height, False)
        except Exception as e:
            api.logger.error(f"Error in window resize handler: {e}", exc_info=True)

    def on_window_maximized() -> None:
        """Handle window maximize events"""
        try:
            # When maximized, preserve the last known restored size for when it's restored later
            save_window_state_debounced(last_saved_state['width'], last_saved_state['height'], True)
        except Exception as e:
            api.logger.error(f"Error in window maximize handler: {e}", exc_info=True)

    def on_window_restored() -> None:
        """Handle window restore events (from maximized or minimized)"""
        try:
            api.logger.info("Window restored")
            # When restored from maximized, it's no longer maximized
            # The size will be updated by the resize event that typically follows
            save_window_state_debounced(last_saved_state['width'], last_saved_state['height'], False)
        except Exception as e:
            api.logger.error(f"Error in window restore handler: {e}", exc_info=True)

    def on_window_minimized() -> None:
        """Handle window minimize events"""
        try:
            api.logger.info("Window minimized")
            # Don't change maximized state when minimizing, just log the event
        except Exception as e:
            api.logger.error(f"Error in window minimize handler: {e}", exc_info=True)

    # Register window event handlers
    window.events.resized += on_window_resized
    window.events.maximized += on_window_maximized
    window.events.restored += on_window_restored
    window.events.minimized += on_window_minimized

    return window


def main() -> None:
    """Main entry point for the GUI application"""
    import sys

    # Setup logging
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Check for dev mode argument
    dev_mode = '--dev' in sys.argv
    dev_url = "http://localhost:5173"  # Default Vite dev server URL

    # Allow custom dev URL
    for i, arg in enumerate(sys.argv):
        if arg == '--dev-url' and i + 1 < len(sys.argv):
            dev_url = sys.argv[i + 1]
            break

    # Detect if running in PyInstaller frozen environment
    is_frozen = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

    create_app(dev_mode=dev_mode, dev_url=dev_url)

    # Use debug=False for PyInstaller builds to avoid timeout issues
    debug_mode = not is_frozen
    webview.start(debug=debug_mode)


def main_dev() -> None:
    """Development entry point for the GUI application - automatically connects to Vite dev server"""
    import sys

    print(f"🚀 Starting NV Clipper GUI in development mode")
    print(f"📡 Connecting to Vite dev server at http://localhost:5173")
    print(f"💡 Make sure Vite dev server is running: cd src/gui-frontend && pnpm run dev")

    # Inject --dev argument and call main()
    sys.argv.append('--dev')
    main()


if __name__ == '__main__':
    main()
