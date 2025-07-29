"""Main GUI application using pywebview."""

import json
import threading
import webview
from pathlib import Path
from typing import Optional
import logging
import time
import uuid

from .engine import ClipperEngine


class ClipperGUI:
    """GUI API class for pywebview."""

    def __init__(self):
        self.engine = ClipperEngine()  # Initialize immediately
        self.is_initialized = True     # Always ready since initialization is minimal
        self.logger = logging.getLogger(__name__)
        self.processing_jobs = {}      # Track processing jobs by ID
        self.job_lock = threading.Lock()

    def process_files(self, markup_path: str, video_path: Optional[str] = None):
        """Process files using the engine in a separate thread"""
        # Create a unique job ID
        job_id = str(uuid.uuid4())

        # Initialize job status
        with self.job_lock:
            self.processing_jobs[job_id] = {
                "status": "starting",
                "message": "Initializing processing...",
                "result": None,
                "started_at": time.time()
            }

        # Start processing in a separate thread
        def process_worker():
            try:
                self.logger.info(f"Starting processing job {job_id}")

                # Update status to processing
                with self.job_lock:
                    self.processing_jobs[job_id].update({
                        "status": "processing",
                        "message": "Processing files..."
                    })

                # Call the engine processing
                result = self.engine.process_files(markup_path, video_path)

                # Update with final result
                with self.job_lock:
                    self.processing_jobs[job_id].update({
                        "status": "completed",
                        "result": result,
                        "completed_at": time.time()
                    })

                self.logger.info(f"Completed processing job {job_id}: {result['status']}")

            except Exception as e:
                self.logger.error(f"Processing job {job_id} failed: {e}")

                # Update with error result
                with self.job_lock:
                    self.processing_jobs[job_id].update({
                        "status": "completed",
                        "result": {"status": "error", "message": str(e)},
                        "completed_at": time.time()
                    })

        # Start the worker thread
        thread = threading.Thread(target=process_worker, daemon=True)
        thread.start()

        # Return job ID for status tracking
        return {"status": "accepted", "job_id": job_id, "message": "Processing started"}

    def get_job_status(self, job_id: str):
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
                "job_id": job_id
            }

    def cleanup_old_jobs(self):
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

    def get_status(self):
        """Get current status of the application"""
        return self.engine.get_status()

    def select_files(self):
        """Open file dialog to select files"""
        result = webview.windows[0].create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=True,
            file_types=('JSON files (*.json)', 'Video files (*.mp4;*.webm;*.avi;*.mkv)', 'All files (*.*)')
        )
        return result

    def parse_markup_file(self, file_path: str):
        """Parse a JSON markup file and return clip information"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
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
                    'overrides': marker.get('overrides', {})
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
                    'version': data.get('version', '')
                }
            }

        except Exception as e:
            self.logger.error(f"Failed to parse markup file {file_path}: {e}")
            return {
                'status': 'error',
                'message': f"Failed to parse markup file: {str(e)}"
            }


def create_app(dev_mode=False, dev_url="http://localhost:5173"):
    """Create and configure the webview application"""
    api = ClipperGUI()

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
                "Please build the frontend first: cd src/gui-frontend && pnpm run build"
            )

        url = frontend_path.as_uri()

    window = webview.create_window(
        'NV Clipper GUI',
        url,
        js_api=api,
        width=1000,
        height=800,
        resizable=True,
        min_size=(800, 600)
    )

    return window


def main():
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

    window = create_app(dev_mode=dev_mode, dev_url=dev_url)
    webview.start(debug=True)  # Enable debug mode


def main_dev():
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
