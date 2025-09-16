"""Main GUI application using pywebview."""

import contextlib
import json
import logging
import multiprocessing
import os
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


# Top-level worker for multiprocessing (must be picklable on Windows)
def _processing_worker(job_id_local: str,
                       markup_path_local: Optional[str],
                       video_path_local: Optional[str],
                       settings_local: Dict[str, Any],
                       markup_data_local: Optional[Dict[str, Any]],
                       out_path: str) -> None:
    # Mark process as GUI worker for downstream code that may want to adapt behavior
    os.environ["YTC_GUI_WORKER"] = "1"
    result: Dict[str, Any] = {"status": "error", "message": "Unknown failure"}
    try:
        from clipper.gui.engine import ClipperEngine
        engine = ClipperEngine()
        result = engine.process_files(
            markup_path=markup_path_local,
            video_path=video_path_local,
            settings_overrides=settings_local,
            markup_data=markup_data_local,
        )
    except BaseException as e:  # Catch SystemExit too so we can return structured error JSON
        import traceback as _tb
        if isinstance(e, SystemExit):
            code = e.code
            msg = f"Processing terminated (exit {code})"
        else:
            msg = str(e)
        result = {
            "status": "error",
            "message": msg,
            "details": _tb.format_exc(limit=10),
        }
    finally:
        # Always write a result to avoid frontend JSON parse errors
        try:
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(result, f)
        except Exception:
            pass


class ClipperGUI:
    """GUI API class for pywebview."""

    # Type hints for instance dictionaries
    _job_processes: Dict[str, multiprocessing.Process]
    _job_result_files: Dict[str, str]

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
        # Processing job process management
        self._proc_lock = threading.Lock()
        self._job_processes = {}
        self._job_result_files = {}

        # Drag and drop state
        self.current_files = []        # Store current dropped files for processing

        # Preview frame cache (single-entry MRU)
        # Stores last extracted JPEG frame to avoid repeat video decode for filter tweaks
        # Keys: video_path (str), timestamp (rounded float), scale (float)
        # Data: bytes (JPEG), mime (str)
        self._preview_frame_cache = {
            'video_path': None,
            'timestamp': None,
            'scale': None,
            'image_bytes': None,
            'mime': 'image/jpeg',
        }
        # Preview subprocess management (hard cancel support)
        self._preview_proc_lock = threading.Lock()
        self._active_preview_proc = None
        # Idempotent preview in-progress & result cache for color-graded outputs
        # key: (video_path|timestamp_ms|scale|filter or 'base') -> {'status': 'success', 'image_bytes': b'..', 'mime': 'image/jpeg'}
        self._preview_result_cache = {}
        self._preview_inflight = {}

    # ---------------------
    # Preview cache helpers
    # ---------------------
    @staticmethod
    def _norm_ts(ts: float) -> float:
        """Normalize timestamp key to milliseconds precision to avoid float noise."""
        return round(ts, 3)

    def _cache_matches(self, video_path: str, timestamp: float, scale: float) -> bool:
        c = self._preview_frame_cache
        return (
            c.get('image_bytes') is not None
            and c.get('video_path') == video_path
            and c.get('timestamp') == self._norm_ts(timestamp)
            and c.get('scale') == scale
        )

    def _store_cached_frame(self, video_path: str, timestamp: float, scale: float, image_bytes: bytes) -> None:
        self._preview_frame_cache.update({
            'video_path': video_path,
            'timestamp': self._norm_ts(timestamp),
            'scale': scale,
            'image_bytes': image_bytes,
            'mime': 'image/jpeg',
        })

    def _clear_cached_frame(self) -> None:
        self._preview_frame_cache.update({
            'video_path': None,
            'timestamp': None,
            'scale': None,
            'image_bytes': None,
        })

    # --------- New helper methods to simplify generate_frame_preview (reduce branching) ---------
    def _validate_preview_inputs(self, video_path: str, timestamp: float, resolution_scale: float,
                                 color_grading: Optional[str]) -> Optional[Dict[str, Any]]:
        """Validate basic preview inputs. Return error dict if invalid, else None."""
        is_http = str(video_path).startswith(('http://', 'https://'))
        if not is_http:
            video_file = Path(video_path)
            if not video_file.exists():
                return {'status': 'error', 'message': f'Video file not found: {video_path}'}
        if timestamp < 0:
            return {'status': 'error', 'message': 'Timestamp must be non-negative'}
        if resolution_scale not in [0.1, 0.25, 0.5, 1.0]:
            return {'status': 'error', 'message': 'Resolution scale must be 0.1, 0.25, 0.5, or 1.0'}
        if color_grading:
            from clipper.ffmpeg_filter import _validate_color_grading_filter
            if not _validate_color_grading_filter(color_grading):
                return {'status': 'error', 'message': 'Invalid color grading filter string'}
        return None

    def _get_cached_preview(self, full_key: str, timestamp: float, resolution_scale: float) -> Optional[Dict[str, Any]]:
        """Return cached preview result (already base64 encoded) if available."""
        with self._preview_proc_lock:
            cached = self._preview_result_cache.get(full_key)
            if cached and cached.get('status') == 'success':
                image_bytes_cached = cached.get('image_bytes')
                if isinstance(image_bytes_cached, (bytes, bytearray)):
                    import base64
                    return {
                        'status': 'success',
                        'message': 'Frame preview (cached)',
                        'base64_image': base64.b64encode(image_bytes_cached).decode('utf-8'),
                        'mime_type': cached.get('mime', 'image/jpeg'),
                        'timestamp': timestamp,
                        'resolution_scale': resolution_scale,
                        'cached': True,
                    }
        return None

    def _register_inflight_or_wait(self, full_key: str) -> Optional[threading.Event]:
        """Register request as in-flight or attach as waiter. Returns wait_event if should wait."""
        wait_event: Optional[threading.Event] = None
        if full_key not in self._preview_result_cache:
            with self._preview_proc_lock:
                if full_key in self._preview_inflight:
                    wait_event = threading.Event()
                    self._preview_inflight[full_key].append(wait_event)
                else:
                    self._preview_inflight[full_key] = []  # This caller becomes producer
        return wait_event

    def _wait_for_inflight(self, full_key: str, wait_event: threading.Event, timestamp: float,
                            resolution_scale: float) -> Optional[Dict[str, Any]]:
        """Wait for existing in-flight result and return standardized response if success."""
        wait_event.wait(timeout=30)
        with self._preview_proc_lock:
            cached = self._preview_result_cache.get(full_key)
        if cached and cached.get('status') == 'success':
            import base64
            return {
                'status': 'success',
                'message': 'Frame preview (deduped)',
                'base64_image': base64.b64encode(cached['image_bytes']).decode('utf-8'),  # type: ignore[index]
                'mime_type': cached.get('mime', 'image/jpeg'),
                'timestamp': timestamp,
                'resolution_scale': resolution_scale,
                'deduped': True,
            }
        return None

    def _ensure_base_frame(self, video_path: str, normalized_ts: float, resolution_scale: float) -> Optional[bytes]:
        """Ensure a cached base frame exists (no color grading). Return bytes or None."""
        cache_key_path = str(video_path)
        if self._cache_matches(cache_key_path, normalized_ts, resolution_scale):
            self.logger.debug("Using cached base frame for preview")
            return self._preview_frame_cache.get('image_bytes')

        base_cmd = [
            'ffmpeg', '-ss', str(normalized_ts), '-i', str(video_path),
            '-vframes', '1', '-f', 'image2pipe', '-vcodec', 'mjpeg', '-pix_fmt', 'yuvj420p', '-q:v', '2',
        ]
        vf_parts = []
        if resolution_scale != 1.0:
            vf_parts.append(f'scale=iw*{resolution_scale}:ih*{resolution_scale}:force_original_aspect_ratio=decrease')
            vf_parts.append('pad=ceil(iw/2)*2:ceil(ih/2)*2:(ow-iw)/2:(oh-ih)/2:color=black')
        if vf_parts:
            base_cmd.extend(['-vf', ','.join(vf_parts)])
        base_cmd.append('pipe:1')

        self.logger.debug(f"FFmpeg (cache base) command: {' '.join(base_cmd)}")
        with self._preview_proc_lock:
            if self._active_preview_proc and self._active_preview_proc.poll() is None:
                self.logger.debug("Terminating previous preview ffmpeg process")
                with contextlib.suppress(Exception):
                    self._active_preview_proc.terminate()
                try:
                    self._active_preview_proc.wait(timeout=0.5)
                except Exception:
                    with contextlib.suppress(Exception):
                        self._active_preview_proc.kill()
            proc = subprocess.Popen(base_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self._active_preview_proc = proc

        try:
            stdout, stderr = proc.communicate(timeout=30)
        except Exception:
            with contextlib.suppress(Exception):
                proc.kill()
            return None
        if proc.returncode != 0 or not stdout:
            self.logger.error("Failed to generate base frame for cache")
            if stderr:
                self.logger.error(stderr.decode(errors='ignore'))
            return None
        with self._preview_proc_lock:
            self._store_cached_frame(cache_key_path, normalized_ts, resolution_scale, stdout)
            if self._active_preview_proc is proc:
                self._active_preview_proc = None
        return stdout

    def _apply_color_grading_filters(self, base_frame: bytes, color_grading: str) -> Optional[bytes]:
        """Apply ffmpeg color grading filters to a base JPEG frame."""
        filter_cmd = [
            'ffmpeg', '-f', 'image2pipe', '-vcodec', 'mjpeg', '-i', 'pipe:0',
            '-vframes', '1', '-f', 'image2pipe', '-vcodec', 'mjpeg', '-pix_fmt', 'yuvj420p', '-q:v', '2',
            '-vf', color_grading, 'pipe:1',
        ]
        self.logger.debug(f"FFmpeg (apply filters) command: {' '.join(filter_cmd)}")
        result2 = subprocess.run(filter_cmd, input=base_frame, capture_output=True, timeout=30, check=False)
        if result2.returncode != 0 or not result2.stdout:
            self.logger.error("FFmpeg filter application failed")
            if result2.stderr:
                self.logger.error(result2.stderr.decode(errors='ignore'))
            return None
        return result2.stdout

    # Finalization helpers to reduce branching in main preview method
    def _finalize_preview_success(self, full_key: str, image_bytes: bytes, timestamp: float, resolution_scale: float) -> Dict[str, Any]:
        import base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        success_obj = {
            'status': 'success', 'message': 'Frame preview generated', 'base64_image': image_base64,
            'mime_type': 'image/jpeg', 'timestamp': timestamp, 'resolution_scale': resolution_scale,
        }
        with self._preview_proc_lock:
            self._preview_result_cache[full_key] = {'status': 'success', 'image_bytes': image_bytes, 'mime': 'image/jpeg'}
            waiters = self._preview_inflight.pop(full_key, [])
            for ev in waiters:
                ev.set()
        return success_obj

    def _finalize_preview_failure(self, full_key: str, message: str) -> Dict[str, Any]:
        with self._preview_proc_lock:
            waiters = self._preview_inflight.pop(full_key, [])
            for ev in waiters:
                ev.set()
        return {'status': 'error', 'message': message}

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

    def process_files(self, markup_path: Optional[str] = None, video_path: Optional[str] = None,
                     selected_clips: Optional[List[int]] = None,
                     markup_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process files using the engine in a separate process (supports cancel)."""
        if markup_path is None and markup_data is None:
            return {"status": "error", "message": "Either markup_path or markup_data must be provided"}

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

        # Prepare settings for worker process
        settings_overrides = self.settings_manager.get_combined_settings()
        if selected_clips is not None:
            settings_overrides['only'] = selected_clips

        # Create a temp result file for IPC
        result_tmp = tempfile.NamedTemporaryFile(prefix=f"ytc_job_{job_id}_", suffix=".json", delete=False)
        result_path = result_tmp.name
        result_tmp.close()

        # Save result file path for later cleanup
        with self._proc_lock:
            self._job_result_files[job_id] = result_path

        # Notify frontend that processing is starting
        self._notify_processing_update({
            'job_id': job_id,
            'status': 'starting',
            'message': 'Starting processing...',
        })

        # Spawn the worker process
        proc = multiprocessing.Process(
            target=_processing_worker,
            args=(job_id, markup_path, video_path, settings_overrides, markup_data, result_path),
            daemon=True,
        )
        proc.start()
        with self._proc_lock:
            self._job_processes[job_id] = proc

        # Update status to processing and notify
        with self.job_lock:
            self.processing_jobs[job_id].update({
                "status": "processing",
                "message": "Processing files...",
            })
        self._notify_processing_update({
            'job_id': job_id,
            'status': 'processing',
            'message': 'Processing files...',
        })

        # Watcher thread to collect result when process exits
        def _watch_and_finalize() -> None:
            try:
                proc.join()
                # Read result
                result: Dict[str, Any]
                try:
                    with open(result_path, encoding='utf-8') as f:
                        result = json.load(f)
                except Exception as e:
                    result = {"status": "error", "message": f"Failed to read job result: {e}"}

                with self.job_lock:
                    self.processing_jobs[job_id].update({
                        "status": "completed",
                        "result": result,
                        "completed_at": time.time(),
                    })

                # Notify frontend of completion
                payload = {"job_id": job_id, **result}
                self._notify_processing_update(payload)

            finally:
                # Cleanup
                with self._proc_lock:
                    self._job_processes.pop(job_id, None)
                    self._job_result_files.pop(job_id, None)
                with contextlib.suppress(Exception):
                    Path(result_path).unlink(missing_ok=True)  # type: ignore[arg-type]

            self.logger.info(f"Completed processing job {job_id}")

        threading.Thread(target=_watch_and_finalize, daemon=True).start()

        # Return job ID for status tracking (frontend can switch to event-driven updates)
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

    def cancel_processing(self, job_id: str) -> Dict[str, Any]:
        """Cancel an ongoing processing job by terminating its worker process."""
        with self._proc_lock:
            proc = self._job_processes.get(job_id)
        if proc is None:
            # Maybe already finished
            with self.job_lock:
                job = self.processing_jobs.get(job_id)
            if not job:
                return {"status": "error", "message": "Job not found"}
            if job.get("status") == "completed":
                return {"status": "success", "message": "Job already completed"}
            # No process handle but not completed => treat as not cancelable
            return {"status": "error", "message": "Job not cancelable"}

        # Terminate the process
        try:
            if proc.is_alive():
                proc.terminate()
                proc.join(timeout=2.0)
        except Exception as e:
            self.logger.error(f"Failed to terminate job {job_id}: {e}")
            return {"status": "error", "message": f"Failed to terminate job: {e!s}"}

        # Mark as canceled
        with self.job_lock:
            self.processing_jobs[job_id].update({
                "status": "completed",
                "result": {"status": "canceled", "message": "Processing canceled by user"},
                "completed_at": time.time(),
            })

        # Notify frontend
        self._notify_processing_update({
            'job_id': job_id,
            'status': 'canceled',
            'message': 'Processing canceled by user',
        })

        # Cleanup handles
        with self._proc_lock:
            self._job_processes.pop(job_id, None)
            result_path = self._job_result_files.pop(job_id, None)
        if result_path:
            with contextlib.suppress(Exception):
                Path(result_path).unlink(missing_ok=True)  # type: ignore[arg-type]

        return {"status": "success", "message": "Cancel requested"}

    # ---------------------------
    # Push notifications to front
    # ---------------------------
    def _notify_processing_update(self, payload: Dict[str, Any]) -> None:
        """Notify frontend of processing status changes via JS callback."""
        try:
            if not webview.windows:
                return
            window = webview.windows[0]
            js = f"""
            try {{
                if (typeof window.__ytc_onProcessingEvent === 'function') {{
                    window.__ytc_onProcessingEvent({json.dumps(payload)});
                }} else {{
                    console.warn('Processing event handler not registered');
                }}
            }} catch (e) {{
                console.error('Error delivering processing event', e);
            }}
            """
            window.evaluate_js(js)
        except Exception:
            # Best-effort; ignore errors
            pass

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

            result = {
                'status': 'success',
                'clips': clips,
                'markup_info': {
                    'title': video_title,
                    'video_url': data.get('videoUrl', ''),
                    'video_id': data.get('videoID', ''),
                    'platform': data.get('platform', ''),
                    'is_vertical': data.get('isVerticalVideo', False),
                    'crop_res': data.get('cropRes', ''),
                    'version': data.get('version', ''),
                },
            }

            # If there's a selected video file, always probe it for actual video properties
            # This ensures the GUI displays current, accurate video information
            from clipper.clipper_types import ClipperPaths, ClipperState
            from clipper.ffprobe import ffprobeVideoProperties

            # Check if we have a current video file from the GUI state
            # We need to check the current_files list which stores dropped files
            video_file_path = None
            for p in self.current_files:
                if any(Path(p).suffix.lower().endswith(ext) for ext in ['.mp4', '.webm', '.avi', '.mkv', '.mov']):
                    video_file_path = p
                    break

            if video_file_path and Path(video_file_path).exists():
                try:
                    # Create minimal clipper state for ffprobe
                    cs = ClipperState(
                        settings={'platform': 'ytc_generic'},
                        clipper_paths=ClipperPaths(),
                    )

                    # Probe the actual video file
                    video_properties = ffprobeVideoProperties(cs, str(video_file_path))

                    if video_properties:
                        duration = None
                        if 'duration' in video_properties:
                            duration = float(video_properties['duration'])

                        result['video_info'] = {
                            'duration': duration,
                            'width': video_properties.get('width'),
                            'height': video_properties.get('height'),
                            'codec_name': video_properties.get('codec_name'),
                            'bit_rate': video_properties.get('bit_rate'),
                            'frame_rate': video_properties.get('r_frame_rate'),
                            'path': str(video_file_path),
                        }
                        self.logger.info(f"Successfully probed video file: {video_file_path}")
                    else:
                        self.logger.warning(f"Failed to probe video file: {video_file_path}")

                except Exception as e:
                    self.logger.warning(f"Error probing video file {video_file_path}: {e}")

            return result

        except Exception as e:
            self.logger.error(f"Failed to parse markup file {file_path}: {e}")
            return {
                'status': 'error',
                'message': f"Failed to parse markup file: {e!s}",
            }

    def load_markup_file_data(self, file_path: str) -> Dict[str, Any]:
        """Load the complete markup file data structure for color grading tracking"""
        try:
            with open(file_path, encoding='utf-8') as f:
                data = json.load(f)

            return {
                'status': 'success',
                'data': data,
            }

        except Exception as e:
            self.logger.error(f"Failed to load markup file data {file_path}: {e}")
            return {
                'status': 'error',
                'message': f"Failed to load markup file data: {e!s}",
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

    def cancel_download(self, video_id: str) -> Dict[str, Any]:
        """Cancel an in-progress cache download"""
        try:
            return self.cache_manager.cancel_download(video_id)
        except Exception as e:
            self.logger.error(f"Failed to cancel download: {e}")
            return {
                'status': 'error',
                'message': f'Failed to cancel download: {e!s}',
            }

    def clear_stuck_cache_downloads(self) -> Dict[str, Any]:
        """Clear stuck cache downloads from tracking"""
        try:
            return self.cache_manager.clear_stuck_downloads()
        except Exception as e:
            self.logger.error(f"Failed to clear stuck downloads: {e}")
            return {
                'status': 'error',
                'message': f'Failed to clear stuck downloads: {e!s}',
            }

    def clear_error_cache_downloads(self) -> Dict[str, Any]:
        """Clear error cache downloads from tracking"""
        try:
            return self.cache_manager.clear_error_downloads()
        except Exception as e:
            self.logger.error(f"Failed to clear error downloads: {e}")
            return {
                'status': 'error',
                'message': f'Failed to clear error downloads: {e!s}',
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
            from clipper.clipper_types import ClipperPaths, ClipperState
            from clipper.ffprobe import ffprobeVideoProperties

            self.logger.info(f"Getting video info for {video_path}")

            # Validate video file exists
            video_file = Path(video_path)
            if not video_file.exists():
                return {
                    'status': 'error',
                    'message': f'Video file not found: {video_path}',
                }

            # Create a clipper state with default paths and required settings for ffprobe
            cs = ClipperState(
                settings={
                    'platform': 'ytc_generic',  # Required for ffprobe
                },
                clipper_paths=ClipperPaths(),
            )

            # Use ffprobe to get video properties
            video_properties = ffprobeVideoProperties(cs, str(video_file))

            if not video_properties:
                return {
                    'status': 'error',
                    'message': 'Failed to get video properties with ffprobe',
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
                    'path': str(video_file),
                },
            }

        except Exception as e:
            self.logger.error(f"Error getting video info: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': f'Failed to get video info: {e!s}',
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
                'temp_file_path': temp_file_path,
            }

        except Exception as e:
            self.logger.error(f"Error creating temporary markup file: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': f'Failed to create temporary markup file: {e!s}',
            }

    def generate_frame_preview(self, video_path: str, timestamp: float,
                               color_grading: Optional[str] = None,
                               resolution_scale: float = 1.0,
                               request_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate a frame preview with optional color grading filters.

        Args:
            video_path: Path to the video file or a direct HTTP(S) URL
            timestamp: Time in seconds to extract frame from
            color_grading: Optional FFmpeg color grading filter string
            resolution_scale: Scale factor for output resolution (0.1, 0.25, 0.5, 1.0)
            request_id: Deprecated (ignored).

        Returns:
            Dict with status, message, and base64_image for success
        """
        try:
            self.logger.info(f"Generating frame preview for {video_path} at {timestamp}s")

            # Basic validation
            err = self._validate_preview_inputs(video_path, timestamp, resolution_scale, color_grading)
            if err:
                return err

            normalized_ts = self._norm_ts(timestamp)
            key_base = f"{video_path}|{normalized_ts}|{resolution_scale}"
            full_key = f"{key_base}|{color_grading or 'base'}"

            # Fast cached lookup
            cached = self._get_cached_preview(full_key, timestamp, resolution_scale)
            if cached:
                return cached

            # Dedup logic (may return or proceed)
            wait_event = self._register_inflight_or_wait(full_key)
            if wait_event and (deduped := self._wait_for_inflight(full_key, wait_event, timestamp, resolution_scale)):
                return deduped

            # Obtain base frame (cached or freshly extracted)
            base_frame = self._ensure_base_frame(video_path, normalized_ts, resolution_scale)
            if not base_frame:
                return self._finalize_preview_failure(full_key, 'Failed to generate base frame for preview')

            # If no color grading requested
            if not color_grading:
                return self._finalize_preview_success(full_key, base_frame, timestamp, resolution_scale)

            # Apply color grading filters to cached base frame
            graded_bytes = self._apply_color_grading_filters(base_frame, color_grading)
            if not graded_bytes:
                return self._finalize_preview_failure(full_key, 'Failed to apply color grading to cached frame')
            return self._finalize_preview_success(full_key, graded_bytes, timestamp, resolution_scale)

        except subprocess.TimeoutExpired:
            return {'status': 'error', 'message': 'Frame extraction timed out'}
        except Exception as e:
            self.logger.error(f"Error generating frame preview: {e}", exc_info=True)
            return {'status': 'error', 'message': f'Failed to generate frame preview: {e!s}'}

    def cancel_frame_preview(self, request_id: Optional[str] = None) -> Dict[str, Any]:
        """Cancel the active frame preview ffmpeg process.

        request_id parameter is deprecated and ignored.
        """
        with self._preview_proc_lock:
            proc = self._active_preview_proc
            if not proc or proc.poll() is not None:
                return {'status': 'success', 'message': 'No active preview process'}
            try:
                self.logger.debug('Canceling active preview process')
                proc.terminate()
                try:
                    proc.wait(timeout=0.5)
                except Exception:
                    with contextlib.suppress(Exception):
                        proc.kill()
                self._active_preview_proc = None
                return {'status': 'success', 'message': 'Preview process canceled'}
            except Exception as e:
                return {'status': 'error', 'message': f'Failed to cancel preview: {e!s}'}

    def get_direct_video_url(self, page_url: str) -> Dict[str, Any]:
        """Resolve a direct media URL using yt-dlp based on GUI settings.

        This mirrors the technique used in core processing when inputVideo is not present.
        Returns a URL string that can be passed directly to ffmpeg as input.
        """
        try:
            from clipper.clipper_types import ClipperState
            from clipper.ytdl import ytdl_bin_get_video_info

            # Load GUI settings to configure yt-dlp path/format options
            settings_overrides = self.settings_manager.get_combined_settings()

            cs = ClipperState()
            # Map required settings keys expected by ytdl helpers
            # Provide only minimal keys used by ytdl_bin_get_args_base
            cs.settings.update({
                'platform': 'ytc_gui',
                'videoPageURL': page_url,
                'downloadVideoPath': str(Path(tempfile.gettempdir()) / 'nvclipper_temp'),
                'format': settings_overrides.get('format'),
                'formatSort': settings_overrides.get('format_sort'),
                'cookiefile': settings_overrides.get('cookiefile', ''),
                'username': settings_overrides.get('ytdl_username', ''),
                'password': settings_overrides.get('ytdl_password', ''),
                'downloadVideo': False,
                'ytdlLocation': settings_overrides.get('ytdl_location', ''),
                'ytdlAutoUpdate': settings_overrides.get('ytdl_auto_update', True),
            })

            # Ensure internal paths are set correctly (use default ClipperPaths)
            # If user provided a custom yt-dlp location, update paths accordingly
            if settings_overrides.get('ytdl_location'):
                with contextlib.suppress(Exception):
                    cs.clipper_paths.ytdlPath = str(settings_overrides['ytdl_location'])

            # Query yt-dlp for info (without formats table for speed)
            info, _ = ytdl_bin_get_video_info(cs, no_list_formats=True, no_get_info=False)

            # Find the best video-only or combined format URL
            url = None
            if isinstance(info, dict):
                # Prefer url field directly if present
                url = info.get('url')
                if not url:
                    # Fallback: pick best format entry
                    fmts = info.get('formats') or []
                    # Choose the last (often best) http(s) format with video
                    for f in reversed(fmts):
                        if f.get('url') and (f.get('vcodec') != 'none'):
                            url = f['url']
                            break

            if not url:
                return {
                    'status': 'error',
                    'message': 'Failed to obtain direct video URL from yt-dlp metadata',
                }

            return {
                'status': 'success',
                'url': url,
            }
        except Exception as e:
            self.logger.error(f"Error resolving direct video URL: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': f'Failed to resolve direct video URL: {e!s}',
            }

    # Window State Management API

    def save_window_state(self, width: int, height: int, maximized: bool = False) -> Dict[str, Any]:
        """Save the current window state to settings"""
        try:
            success = self.settings_manager.update_general_settings({
                'window_width': width,
                'window_height': height,
                'window_maximized': maximized,
            })

            if success:
                return {
                    'status': 'success',
                    'message': 'Window state saved successfully',
                }
            return {
                'status': 'error',
                'message': 'Failed to save window state',
            }
        except Exception as e:
            self.logger.error(f"Error saving window state: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': f'Failed to save window state: {e!s}',
            }

    def get_window_state(self) -> Dict[str, Any]:
        """Get the saved window state from settings"""
        try:
            settings = self.settings_manager.get_general_settings()
            return {
                'status': 'success',
                'width': settings.get('window_width', 1000),
                'height': settings.get('window_height', 800),
                'maximized': settings.get('window_maximized', False),
            }
        except Exception as e:
            self.logger.error(f"Error getting window state: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': f'Failed to get window state: {e!s}',
                'width': 1000,  # fallback defaults
                'height': 800,
                'maximized': False,
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

        def save_state() -> None:
            try:
                result = api.save_window_state(new_width, new_height, new_maximized)
                if result['status'] == 'success':
                    last_saved_state.update(current_state)
                    api.logger.debug(
                        f"Window state saved: {new_width}x{new_height}, maximized: {new_maximized}",
                    )
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
    # IMPORTANT for PyInstaller + multiprocessing on Windows:
    # Ensure child processes do not relaunch the full GUI when spawned.
    import multiprocessing as _mp
    _mp.freeze_support()
    with contextlib.suppress(RuntimeError):
        _mp.set_start_method('spawn', force=True)
    main()
