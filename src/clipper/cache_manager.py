"""
Video cache management API for the GUI frontend.
"""

import contextlib
import hashlib
import sqlite3
import subprocess
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from clipper.clipper_types import ClipperPaths, ClipperState
from clipper.ytc_logger import logger
from clipper.ytdl import ytdl_bin_get_video_info


class VideoCacheManager:
    """Manages cached video files for the GUI."""

    def __init__(self, cache_dir: Optional[str] = None, max_size_mb: int = 5000) -> None:
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".nv_clipper" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = self.cache_dir / "cache.db"

        # Handle max_size properly - avoid using float('inf') to prevent JSON serialization issues
        if max_size_mb <= 0:
            # Use 1TB as practical maximum (effectively unlimited)
            self.max_size = 1024 * 1024 * 1024 * 1024  # 1TB in bytes
        else:
            self.max_size = max_size_mb * 1024 * 1024  # Convert to bytes

        # Download progress tracking
        self._download_progress = {}
        self._download_lock = threading.Lock()
        # Optional: map of active worker threads (for observability)
        self._download_threads = {}

        self._init_database()



    def _init_database(self) -> None:
        """Initialize the cache database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cached_videos (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    duration REAL NOT NULL,
                    cached_at TEXT NOT NULL,
                    last_accessed TEXT NOT NULL,
                    video_id TEXT NOT NULL,
                    format TEXT NOT NULL,
                    thumbnail_path TEXT
                )
            """)

            # Create index for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_last_accessed ON cached_videos(last_accessed)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_cached_at ON cached_videos(cached_at)")

    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the current cache state."""
        videos = self._get_all_cached_videos()
        total_size = sum(video['file_size'] for video in videos)

        # Handle large max_size values for JSON serialization
        # If max_size is our "unlimited" value (1TB), return 0 to represent unlimited
        max_size_value = self.max_size
        if max_size_value >= 1024 * 1024 * 1024 * 1024:  # 1TB or more = unlimited
            max_size_value = 0

        return {
            'total_size': total_size,
            'total_count': len(videos),
            'max_size': max_size_value,
            'cache_dir': str(self.cache_dir),
            'videos': videos,
        }

    def _get_all_cached_videos(self) -> List[Dict[str, Any]]:
        """Get all cached videos from database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM cached_videos
                ORDER BY last_accessed DESC
            """)

            videos = []
            for row in cursor.fetchall():
                video_dict = dict(row)
                # Verify file still exists
                if Path(video_dict['file_path']).exists():
                    videos.append(video_dict)
                else:
                    # Clean up orphaned database entries
                    self._remove_from_database(video_dict['id'])

            return videos

    def download_video(self, url: str, title: Optional[str] = None,
                      format_spec: Optional[str] = None,
                      format_sort: Optional[List[str]] = None,
                      ytdl_location: Optional[str] = None,
                      auto_update: bool = True) -> Dict[str, Any]:
        """Start downloading a video to cache."""
        try:
            # Generate unique ID for this download
            video_id = hashlib.md5(url.encode()).hexdigest()

            # Check if already cached
            existing = self._get_cached_video_by_url(url)
            if existing:
                return {
                    'status': 'success',
                    'message': 'Video already cached',
                    'video': existing,
                }

            # Check if download is already in progress
            with self._download_lock:
                if video_id in self._download_progress:
                    progress_info = self._download_progress[video_id]
                    status = progress_info.get('status')
                    start_time = progress_info.get('start_time', time.time())

                    # Allow restart if previous attempt failed or was canceled or completed
                    if status in {'error', 'canceled', 'completed'}:
                        del self._download_progress[video_id]
                        logger.info(f"Restarting previous download state ({status}) for {url}")
                    elif time.time() - start_time > 1800:  # 30 minutes
                        # Clean up stuck download
                        del self._download_progress[video_id]
                        logger.warning(f"Cleaned up stuck download for {url}")
                    else:
                        return {
                            'status': 'error',
                            'code': 'ERR_IN_PROGRESS',
                            'message': 'Download already in progress',
                            'video_id': video_id,
                        }

                # Initialize progress tracking
                self._download_progress[video_id] = {
                    'video_id': video_id,
                    'url': url,
                    'title': title,
                    'status': 'starting',
                    'progress': 0,
                    'start_time': time.time(),
                    'cancel_requested': False,
                }

            # Start download in background thread
            thread = threading.Thread(
                target=self._download_worker,
                args=(video_id, url, title, format_spec, format_sort, ytdl_location, auto_update),
            )
            thread.daemon = True
            thread.start()
            with self._download_lock:
                self._download_threads[video_id] = thread

            return {
                'status': 'success',
                'message': 'Download started',
                'video_id': video_id,
            }

        except Exception as e:
            logger.error(f"Failed to start download: {e}")
            return {
                'status': 'error',
                'code': 'ERR_START_FAILED',
                'message': str(e),
            }

    def _download_worker(self, video_id: str, url: str, title: Optional[str],
                        format_spec: Optional[str], format_sort: Optional[List[str]],
                        ytdl_location: Optional[str], auto_update: bool) -> None:
        """Worker function to download video in background."""
        try:
            logger.info(f"Starting download for {url} with video_id {video_id}")

            # Step 1: initializing + early cancel check
            self._update_progress(video_id, 'initializing', 0, 'Initializing download...')
            if self._is_cancel_requested(video_id):
                self._finalize_canceled(video_id, url)
                return

            # Step 2: build ClipperState and settings
            cs = self._build_clipper_state(video_id, url, ytdl_location, format_spec, format_sort, auto_update)

            # Step 3: get info (and trigger download)
            self._update_progress(video_id, 'downloading', 10, 'Getting video information...')
            video_info = self._retrieve_video_info(cs)

            # Step 4: cancel check after info
            if self._is_cancel_requested(video_id):
                self._finalize_canceled(video_id, url)
                return

            # Step 5: file selection
            self._update_progress(video_id, 'downloading', 50, 'Downloading video file...')
            cache_path = self._select_downloaded_file(video_id)

            # Step 6: cancel check before DB write (and cleanup file if needed)
            if self._is_cancel_requested(video_id):
                with contextlib.suppress(Exception):
                    if cache_path.exists():
                        cache_path.unlink(missing_ok=True)  # type: ignore[arg-type]
                self._finalize_canceled(video_id, url)
                return

            # Step 7: process and persist
            self._update_progress(video_id, 'processing', 80, 'Processing downloaded file...')
            video_title = title or video_info.get('title', 'Unknown')
            self._update_progress(video_id, 'finalizing', 90, 'Saving to database...')
            self._persist_cache_entry(video_id, video_info, url, video_title, cache_path)

            # Step 8: finalize
            self._update_progress(video_id, 'completed', 100, f'Successfully cached: {video_title}')
            logger.info(f"Successfully cached video: {video_title}")
            self._schedule_completed_cleanup(video_id)

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Download failed for {url}: {error_msg}")
            user_error_msg = self._format_user_error(title or None, url, error_msg)
            self._update_progress(video_id, 'error', 0, user_error_msg)
            logger.info(f"Download failed for {video_id}, keeping error status for user visibility")
        finally:
            # Ensure thread map cleanup if not already removed
            with self._download_lock:
                self._download_threads.pop(video_id, None)

    def _build_clipper_state(self, video_id: str, url: str,
                              ytdl_location: Optional[str],
                              format_spec: Optional[str],
                              format_sort: Optional[List[str]],
                              auto_update: bool) -> ClipperState:
        """Prepare a minimal ClipperState for yt-dlp operations."""
        cache_filename = f"{video_id}"
        cache_path_template = self.cache_dir / cache_filename

        clipper_paths = ClipperPaths()
        # In frozen (PyInstaller) builds, point to bundled binaries by default
        if getattr(sys, "frozen", False):
            bin_dir = "./bin"
            ext = ".exe" if sys.platform == "win32" else ""
            clipper_paths.ffmpegPath = f"{bin_dir}/ffmpeg{ext}"
            clipper_paths.ffprobePath = f"{bin_dir}/ffprobe{ext}"
            clipper_paths.ffplayPath = f"{bin_dir}/ffplay{ext}"
            clipper_paths.ytdlPath = f"{bin_dir}/yt-dlp{ext}"
            # Normalize slashes for subprocess readability
            clipper_paths.ffmpegPath = clipper_paths.ffmpegPath.replace("\\", "/")
            clipper_paths.ffprobePath = clipper_paths.ffprobePath.replace("\\", "/")
            clipper_paths.ffplayPath = clipper_paths.ffplayPath.replace("\\", "/")
            clipper_paths.ytdlPath = clipper_paths.ytdlPath.replace("\\", "/")

        if ytdl_location:
            clipper_paths.ytdlPath = ytdl_location
            logger.info(f"Using custom yt-dlp location: {ytdl_location}")
        else:
            logger.info(f"No custom yt-dlp location provided, using default: {clipper_paths.ytdlPath}")

        settings = {
            'videoPageURL': url,
            'downloadVideoPath': str(cache_path_template).replace('\\', '/'),
            'format': format_spec or None,
            'formatSort': format_sort or None,
            'cookiefile': '',
            'username': '',
            'password': '',
            'downloadVideo': True,
            'ytdlLocation': ytdl_location or '',
            'ytdlAutoUpdate': auto_update,
        }
        logger.debug(f"Download settings for {video_id}: {settings}")
        return ClipperState(settings=settings, clipper_paths=clipper_paths)

    def _retrieve_video_info(self, cs: ClipperState) -> Dict[str, Any]:
        """Retrieve video info using yt-dlp and propagate friendly errors."""
        try:
            info, _ = ytdl_bin_get_video_info(cs, True)
            return info or {}
        except subprocess.CalledProcessError as e:
            error_msg = f"yt-dlp failed: {e!s}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to download video: {e!s}"
            logger.error(error_msg)
            raise Exception(error_msg) from e

    def _select_downloaded_file(self, video_id: str) -> Path:
        """Find the downloaded file for the given video_id or raise."""
        downloaded_files = list(self.cache_dir.glob(f"{video_id}.*"))
        downloaded_files = [f for f in downloaded_files if f.is_file() and not f.name.endswith('.temp.mkv')]
        if not downloaded_files:
            all_files = [f.name for f in self.cache_dir.glob(f"{video_id}*")]
            logger.error(f"No downloaded file found for {video_id}. Files in cache: {all_files}")
            raise Exception("Download failed - no file found in cache directory")
        # Use largest file when multiple present
        return max(downloaded_files, key=lambda f: f.stat().st_size)

    def _persist_cache_entry(self, video_id: str, video_info: Dict[str, Any], url: str,
                              video_title: str, cache_path: Path) -> None:
        """Write the cache metadata entry into the database."""
        platform = self._extract_platform(url)
        duration = video_info.get('duration', 0)
        file_size = cache_path.stat().st_size
        format_name = video_info.get('format_id', 'unknown')
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO cached_videos
                (id, title, url, platform, file_path, file_size, duration,
                 cached_at, last_accessed, video_id, format)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    video_id, video_title, url, platform, str(cache_path),
                    file_size, duration, now, now, video_info.get('id', video_id), format_name,
                ),
            )

    def _schedule_completed_cleanup(self, video_id: str) -> None:
        """Schedule cleanup to remove completed progress entry after a short delay."""
        def cleanup_completed_download() -> None:
            time.sleep(2)
            with self._download_lock:
                if video_id in self._download_progress:
                    del self._download_progress[video_id]
                self._download_threads.pop(video_id, None)
                logger.debug(f"Cleaned up completed download tracking for {video_id}")

        t = threading.Thread(target=cleanup_completed_download, daemon=True)
        t.start()

    def _format_user_error(self, title: Optional[str], url: str, error_msg: str) -> str:
        """Return a friendly error message with video identification."""
        video_identifier = title if title else url
        if "yt-dlp failed" in error_msg:
            return (
                f"Failed to download '{video_identifier}': Video might be private, "
                f"deleted, or not available in your region."
            )
        if "Download failed - no file found" in error_msg:
            return (
                f"Download of '{video_identifier}' completed but no file found. "
                f"This might be a temporary issue - please try again."
            )
        if "Failed to get video info" in error_msg:
            return f"Could not access video information for '{video_identifier}'. Please check the URL and try again."
        return f"Failed to download '{video_identifier}': {error_msg}"

    def _update_progress(self, video_id: str, status: str, progress: float, message: str = "") -> None:
        """Update download progress."""
        with self._download_lock:
            if video_id in self._download_progress:
                # Preserve existing title and URL when updating
                existing = self._download_progress[video_id]
                existing.update({
                    'status': status,
                    'progress': progress,
                    'message': message,
                })

    def _is_cancel_requested(self, video_id: str) -> bool:
        with self._download_lock:
            info = self._download_progress.get(video_id)
            return bool(info and info.get('cancel_requested'))

    def _finalize_canceled(self, video_id: str, url: str) -> None:
        # Mark canceled and keep entry briefly for UI to fetch status
        self._update_progress(video_id, 'canceled', 0, 'Download canceled')
        logger.info(f"Canceled download for {url}")
        # Cleanup the progress entry soon after so new attempts can proceed
        def cleanup() -> None:
            time.sleep(2)
            with self._download_lock:
                self._download_progress.pop(video_id, None)
                self._download_threads.pop(video_id, None)
        t = threading.Thread(target=cleanup, daemon=True)
        t.start()

    def get_download_progress(self, video_id: str) -> Dict[str, Any]:
        """Get download progress for a specific video."""
        with self._download_lock:
            progress = self._download_progress.get(video_id)
            if progress:
                # Check if download is stuck (over 30 minutes old)
                start_time = progress.get('start_time', time.time())
                is_stuck = time.time() - start_time > 1800

                result = progress.copy()
                result['is_stuck'] = is_stuck
                if is_stuck:
                    result['stuck_duration'] = time.time() - start_time

                # Ensure message is always available for UI display
                if 'message' not in result or not result['message']:
                    status = result.get('status', 'unknown')
                    if status == 'initializing':
                        result['message'] = 'Preparing download...'
                    elif status == 'downloading':
                        result['message'] = 'Downloading video...'
                    elif status == 'processing':
                        result['message'] = 'Processing file...'
                    elif status == 'finalizing':
                        result['message'] = 'Saving to cache...'
                    elif status == 'completed':
                        result['message'] = 'Download completed!'
                    elif status == 'error':
                        result['message'] = 'Download failed'
                    else:
                        result['message'] = f'Status: {status}'

                code_map = {
                    'initializing': 'IN_PROGRESS',
                    'downloading': 'IN_PROGRESS',
                    'processing': 'IN_PROGRESS',
                    'finalizing': 'IN_PROGRESS',
                    'completed': 'COMPLETED',
                    'error': 'ERROR',
                    'canceled': 'CANCELED',
                }

                return {
                    'status': 'success',
                    'code': code_map.get(result.get('status', 'unknown'), 'UNKNOWN'),
                    'progress': result,
                }
            return {
                'status': 'error',
                'code': 'ERR_NOT_FOUND',
                'message': 'Progress not found',
            }

    def get_all_downloads_status(self) -> Dict[str, Any]:
        """Get status of all active downloads."""
        with self._download_lock:
            downloads = {}
            current_time = time.time()

            for video_id, progress in self._download_progress.items():
                start_time = progress.get('start_time', current_time)
                is_stuck = current_time - start_time > 1800

                downloads[video_id] = {
                    **progress,
                    'is_stuck': is_stuck,
                    'duration': current_time - start_time,
                }

            return {
                'status': 'success',
                'downloads': downloads,
                'total_count': len(downloads),
            }

    def clear_stuck_downloads(self) -> Dict[str, Any]:
        """Clear all stuck downloads from progress tracking."""
        cleared_count = 0
        with self._download_lock:
            # Find downloads that are stuck (very old but not error status)
            current_time = time.time()
            to_remove = []

            for video_id, progress in self._download_progress.items():
                status = progress.get('status', '')
                start_time = progress.get('start_time', current_time)

                # Only remove non-error downloads that are old (30+ minutes)
                # Keep error status downloads so user can see them
                if status != 'error' and (current_time - start_time) > 1800:
                    to_remove.append(video_id)

            for video_id in to_remove:
                del self._download_progress[video_id]
                cleared_count += 1

        return {
            'status': 'success',
            'message': f'Cleared {cleared_count} stuck downloads',
        }

    def cancel_download(self, video_id: str) -> Dict[str, Any]:
        """Request cancellation of an active download.

        Note: Current implementation signals cancellation and cleans state; it may not stop
        a currently executing yt-dlp subprocess immediately (best-effort).
        """
        with self._download_lock:
            info = self._download_progress.get(video_id)
            if not info:
                return {
                    'status': 'error',
                    'code': 'ERR_NOT_FOUND',
                    'message': 'Download not found',
                }
            if info.get('status') in {'completed', 'error', 'canceled'}:
                # Nothing to cancel; allow frontend to clear and retry
                return {
                    'status': 'success',
                    'code': 'NOOP',
                    'message': f"Nothing to cancel (status={info.get('status')})",
                }
            info['cancel_requested'] = True
            return {
                'status': 'success',
                'code': 'CANCEL_REQUESTED',
                'message': 'Cancellation requested',
            }

    def clear_error_downloads(self) -> Dict[str, Any]:
        """Clear all downloads with error status."""
        cleared_count = 0
        with self._download_lock:
            to_remove = []
            for video_id, progress in self._download_progress.items():
                if progress.get('status') == 'error':
                    to_remove.append(video_id)

            for video_id in to_remove:
                del self._download_progress[video_id]
                cleared_count += 1

        return {
            'status': 'success',
            'message': f'Cleared {cleared_count} error downloads',
        }

    def delete_cached_video(self, video_id: str) -> Dict[str, Any]:
        """Delete a cached video."""
        try:
            video = self._get_cached_video(video_id)
            if not video:
                return {
                    'status': 'error',
                    'message': 'Video not found',
                }

            # Delete file
            file_path = Path(video['file_path'])
            if file_path.exists():
                file_path.unlink()

            # Delete thumbnail if exists
            if video.get('thumbnail_path'):
                thumb_path = Path(video['thumbnail_path'])
                if thumb_path.exists():
                    thumb_path.unlink()

            # Remove from database
            self._remove_from_database(video_id)

            return {
                'status': 'success',
                'message': 'Video deleted successfully',
            }

        except Exception as e:
            logger.error(f"Failed to delete video {video_id}: {e}")
            return {
                'status': 'error',
                'message': str(e),
            }

    def purge_cache(self, older_than_days: Optional[int] = None,  # noqa: PLR0912
                   size_limit_mb: Optional[int] = None,
                   keep_most_recent: Optional[int] = None) -> Dict[str, Any]:
        """Purge cache based on various criteria."""
        try:
            videos = self._get_all_cached_videos()
            to_delete = []

            # If no criteria specified, delete all videos
            if (older_than_days is None and
                size_limit_mb is None and
                keep_most_recent is None):
                to_delete = videos.copy()
                logger.info(f"Purging all {len(videos)} videos from cache")
            else:
                # Track videos found by different criteria for logging
                old_videos = []

                # Delete old videos
                if older_than_days:
                    cutoff_date = datetime.now() - timedelta(days=older_than_days)
                    old_videos = [
                        v for v in videos
                        if datetime.fromisoformat(v['cached_at']) < cutoff_date
                    ]
                    to_delete.extend(old_videos)
                    logger.info(f"Found {len(old_videos)} videos older than {older_than_days} days")

                # Enforce size limit
                if size_limit_mb:
                    max_size = size_limit_mb * 1024 * 1024
                    current_size = sum(v['file_size'] for v in videos)

                    if current_size > max_size:
                        # Sort by last accessed (oldest first)
                        sorted_videos = sorted(videos, key=lambda x: x['last_accessed'])

                        size_to_remove = current_size - max_size
                        size_removed = 0
                        size_limit_videos = []

                        for video in sorted_videos:
                            if size_removed >= size_to_remove:
                                break
                            if video not in to_delete:
                                to_delete.append(video)
                                size_limit_videos.append(video)
                                size_removed += video['file_size']

                        logger.info(f"Found {len(size_limit_videos)} videos to remove for size limit")

                # Keep only most recent
                if keep_most_recent:
                    sorted_videos = sorted(videos, key=lambda x: x['last_accessed'], reverse=True)
                    videos_to_remove = sorted_videos[keep_most_recent:]
                    for video in videos_to_remove:
                        if video not in to_delete:
                            to_delete.append(video)
                    logger.info(f"Found {len(videos_to_remove)} videos beyond keep_most_recent limit")

            # Remove duplicates while preserving order
            seen = set()
            unique_to_delete = []
            for video in to_delete:
                if video['id'] not in seen:
                    seen.add(video['id'])
                    unique_to_delete.append(video)

            to_delete = unique_to_delete

            # Delete videos
            deleted_count = 0
            failed_count = 0

            logger.info(f"Attempting to delete {len(to_delete)} videos from cache")

            for video in to_delete:
                result = self.delete_cached_video(video['id'])
                if result['status'] == 'success':
                    deleted_count += 1
                    logger.debug(f"Successfully deleted video: {video['title']}")
                else:
                    failed_count += 1
                    logger.warning(f"Failed to delete video {video['id']}: {result['message']}")

            message = f'Deleted {deleted_count} videos from cache'
            if failed_count > 0:
                message += f' ({failed_count} failed to delete)'

            return {
                'status': 'success',
                'message': message,
            }

        except Exception as e:
            logger.error(f"Failed to purge cache: {e}")
            return {
                'status': 'error',
                'message': str(e),
            }

    def update_video_access_time(self, video_id: str) -> Dict[str, Any]:
        """Update the last accessed time for a video."""
        try:
            now = datetime.now().isoformat()
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "UPDATE cached_videos SET last_accessed = ? WHERE id = ?",
                    (now, video_id),
                )

                if cursor.rowcount == 0:
                    return {
                        'status': 'error',
                        'message': 'Video not found',
                    }

            return {
                'status': 'success',
                'message': 'Access time updated',
            }

        except Exception as e:
            logger.error(f"Failed to update access time: {e}")
            return {
                'status': 'error',
                'message': str(e),
            }

    def _get_cached_video(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific cached video by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM cached_videos WHERE id = ?",
                (video_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def _get_cached_video_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Get a cached video by URL."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM cached_videos WHERE url = ?",
                (url,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def _remove_from_database(self, video_id: str) -> None:
        """Remove a video entry from the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM cached_videos WHERE id = ?", (video_id,))

    def update_cache_settings(self, cache_dir: Optional[str] = None, max_size_mb: Optional[int] = None) -> None:
        """Update cache settings."""
        if cache_dir:
            new_cache_dir = Path(cache_dir)
            if new_cache_dir != self.cache_dir:
                # Create new directory if it doesn't exist
                new_cache_dir.mkdir(parents=True, exist_ok=True)
                self.cache_dir = new_cache_dir
                self.db_path = self.cache_dir / "cache.db"
                self._init_database()  # Reinitialize database in new location

        if max_size_mb is not None:
            # Use a very large number instead of infinity to avoid JSON serialization issues
            # 0 means unlimited, so use a practical maximum (1TB in bytes)
            if max_size_mb <= 0:
                self.max_size = 1024 * 1024 * 1024 * 1024  # 1TB in bytes (effectively unlimited)
            else:
                self.max_size = max_size_mb * 1024 * 1024

    def _extract_platform(self, url: str) -> str:
        """Extract platform name from URL."""
        if 'youtube.com' in url or 'youtu.be' in url:
            return 'YouTube'
        if 'weverse.io' in url:
            return 'Weverse'
        if 'tv.naver.com' in url:
            return 'Naver TV'
        if 'afreecatv.com' in url:
            return 'AfreecaTV'
        return 'Unknown'


# Global cache manager instance
_cache_manager: Optional[VideoCacheManager] = None


def get_cache_manager() -> VideoCacheManager:
    """Get the global cache manager instance."""
    global _cache_manager  # noqa: PLW0603
    if _cache_manager is None:
        # Get default cache directory
        default_cache_dir = Path.home() / ".nv_clipper" / "cache"
        _cache_manager = VideoCacheManager(
            cache_dir=str(default_cache_dir),
            max_size_mb=5000,  # Default to 5GB, will be updated by app settings
        )
    return _cache_manager
