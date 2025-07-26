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


def create_app():
    """Create and configure the webview application"""
    api = ClipperGUI()

    # HTML content for the GUI
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>YT Clipper GUI</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 900px;
                margin: 0 auto;
                background: white;
                border-radius: 8px;
                padding: 30px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                margin-bottom: 30px;
                text-align: center;
            }
            .drop-zone {
                border: 2px dashed #ddd;
                border-radius: 8px;
                padding: 40px;
                text-align: center;
                margin: 20px 0;
                min-height: 200px;
                transition: all 0.3s ease;
                background-color: #fafafa;
            }
            .drop-zone.dragover {
                border-color: #007acc;
                background-color: #f0f8ff;
                transform: scale(1.02);
            }
            .drop-zone.disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            .status {
                padding: 15px;
                margin: 15px 0;
                border-radius: 6px;
                border-left: 4px solid;
            }
            .status.success {
                background-color: #d4edda;
                color: #155724;
                border-left-color: #28a745;
            }
            .status.error {
                background-color: #f8d7da;
                color: #721c24;
                border-left-color: #dc3545;
            }
            .status.info {
                background-color: #d1ecf1;
                color: #0c5460;
                border-left-color: #17a2b8;
            }
            .status.warning {
                background-color: #fff3cd;
                color: #856404;
                border-left-color: #ffc107;
            }
            button {
                padding: 12px 24px;
                background-color: #007acc;
                color: white;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                transition: background-color 0.2s;
            }
            button:hover:not(:disabled) {
                background-color: #005a9e;
            }
            button:disabled {
                background-color: #ccc;
                cursor: not-allowed;
            }
            .button-group {
                display: flex;
                gap: 10px;
                margin: 20px 0;
            }
            .file-info {
                background-color: #f8f9fa;
                padding: 10px;
                border-radius: 4px;
                margin: 10px 0;
                font-family: monospace;
                font-size: 12px;
            }
            .processing-output {
                background-color: #1e1e1e;
                color: #d4d4d4;
                padding: 15px;
                border-radius: 6px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                white-space: pre-wrap;
                max-height: 400px;
                overflow-y: auto;
                margin: 15px 0;
            }
            .spinner {
                border: 2px solid #f3f3f3;
                border-top: 2px solid #007acc;
                border-radius: 50%;
                width: 20px;
                height: 20px;
                animation: spin 1s linear infinite;
                display: inline-block;
                margin-right: 10px;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎬 YT Clipper GUI</h1>

            <div id="status" class="status info">
                ✅ Ready to process files! Drop a JSON markup file or use the file picker below.
            </div>

            <div class="button-group">
                <button id="selectBtn" onclick="selectFiles()">Select Files</button>
            </div>

            <div class="drop-zone" id="dropZone">
                <p><strong>Drag and drop your files here</strong></p>
                <p>Drop a markup JSON file (required) and optionally a video file</p>
                <p>Supported formats: .json, .mp4, .webm, .avi, .mkv</p>
            </div>

            <div id="fileInfo"></div>
            <div id="processingStatus"></div>
        </div>

        <script>
            let selectedFiles = {
                markup: null,
                video: null
            };

            async function selectFiles() {
                try {
                    const files = await pywebview.api.select_files();
                    if (files && files.length > 0) {
                        handleSelectedFiles(files);
                    }
                } catch (error) {
                    console.error('File selection failed:', error);
                }
            }

            function handleSelectedFiles(filePaths) {
                selectedFiles = { markup: null, video: null };

                for (const filePath of filePaths) {
                    const fileName = filePath.split('\\\\').pop().split('/').pop();
                    const extension = fileName.split('.').pop().toLowerCase();

                    if (extension === 'json') {
                        selectedFiles.markup = filePath;
                    } else if (['mp4', 'webm', 'avi', 'mkv'].includes(extension)) {
                        selectedFiles.video = filePath;
                    }
                }

                updateFileInfo();

                if (selectedFiles.markup) {
                    processFiles();
                }
            }

            function updateFileInfo() {
                const fileInfo = document.getElementById('fileInfo');
                let html = '';

                if (selectedFiles.markup) {
                    html += `<div class="file-info">📄 Markup: ${selectedFiles.markup}</div>`;
                }
                if (selectedFiles.video) {
                    html += `<div class="file-info">🎥 Video: ${selectedFiles.video}</div>`;
                }

                fileInfo.innerHTML = html;
            }

            // Drag and drop functionality
            const dropZone = document.getElementById('dropZone');

            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropZone.classList.add('dragover');
            });

            dropZone.addEventListener('dragleave', () => {
                dropZone.classList.remove('dragover');
            });

            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropZone.classList.remove('dragover');

                const files = Array.from(e.dataTransfer.files);
                const filePaths = files.map(f => f.path || f.name);
                handleSelectedFiles(filePaths);
            });

            async function processFiles() {
                if (!selectedFiles.markup) {
                    alert('Please select a JSON markup file');
                    return;
                }

                const processingStatus = document.getElementById('processingStatus');
                const selectBtn = document.getElementById('selectBtn');

                selectBtn.disabled = true;
                processingStatus.innerHTML = '<div class="status info"><div class="spinner"></div>Starting processing...</div>';

                try {
                    // Start processing (non-blocking)
                    console.log('DEBUG: Starting file processing...');
                    const startResult = await pywebview.api.process_files(
                        selectedFiles.markup,
                        selectedFiles.video
                    );

                    console.log('DEBUG: Process start result:', startResult);

                    if (startResult.status === 'accepted') {
                        // Start polling for job status
                        const jobId = startResult.job_id;
                        processingStatus.innerHTML = '<div class="status info"><div class="spinner"></div>Processing files...</div>';

                        await pollJobStatus(jobId, processingStatus);
                    } else {
                        throw new Error(startResult.message || 'Failed to start processing');
                    }
                } catch (error) {
                    console.error('DEBUG: Processing error:', error);
                    processingStatus.innerHTML = '<div class="status error">❌ Processing failed: ' + error + '</div>';
                } finally {
                    selectBtn.disabled = false;
                }
            }

            async function pollJobStatus(jobId, statusElement) {
                const pollInterval = 1000; // Poll every 1 second
                let attempts = 0;
                const maxAttempts = 300; // 5 minutes max

                while (attempts < maxAttempts) {
                    try {
                        const statusResult = await pywebview.api.get_job_status(jobId);
                        console.log('DEBUG: Job status:', statusResult);

                        if (statusResult.status === 'processing') {
                            statusElement.innerHTML = '<div class="status info"><div class="spinner"></div>' + (statusResult.message || 'Processing...') + '</div>';
                        } else if (statusResult.status === 'success') {
                            const message = statusResult.message || 'Processing completed';
                            let html = '<div class="status success">✅ ' + message;
                            if (statusResult.output_path) {
                                html += '<br>Output saved to: ' + statusResult.output_path;
                            }
                            html += '</div>';

                            if (statusResult.report) {
                                html += '<div class="processing-output">' + statusResult.report + '</div>';
                            }

                            statusElement.innerHTML = html;
                            return; // Job completed successfully
                        } else if (statusResult.status === 'error') {
                            statusElement.innerHTML = '<div class="status error">❌ ' + (statusResult.message || 'Processing failed') + '</div>';
                            return; // Job completed with error
                        }

                        // Wait before next poll
                        await new Promise(resolve => setTimeout(resolve, pollInterval));
                        attempts++;

                    } catch (error) {
                        console.error('DEBUG: Status polling error:', error);
                        statusElement.innerHTML = '<div class="status error">❌ Failed to get job status: ' + error + '</div>';
                        return;
                    }
                }

                // Timeout reached
                statusElement.innerHTML = '<div class="status error">❌ Processing timeout - job may still be running</div>';
            }
        </script>
    </body>
    </html>
    """

    window = webview.create_window(
        'YT Clipper GUI',
        html=html_content,
        js_api=api,
        width=1000,
        height=800,
        resizable=True,
        min_size=(800, 600)
    )

    return window


def main():
    """Main entry point for the GUI application"""
    # Setup logging
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    window = create_app()
    webview.start(debug=True)  # Enable debug mode


if __name__ == '__main__':
    main()
