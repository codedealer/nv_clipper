"""Main GUI application using pywebview."""

import json
import threading
import webview
from pathlib import Path
from typing import Optional
import logging

from .engine import ClipperEngine


class ClipperGUI:
    """GUI API class for pywebview."""

    def __init__(self):
        self.engine = ClipperEngine()  # Initialize immediately
        self.is_initialized = True     # Always ready since initialization is minimal
        self.logger = logging.getLogger(__name__)

    def process_files(self, markup_path: str, video_path: Optional[str] = None):
        """Process files using the engine"""
        try:
            result = self.engine.process_files(markup_path, video_path)
            return result
        except Exception as e:
            self.logger.error(f"Processing failed: {e}")
            return {"status": "error", "message": str(e)}

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
                processingStatus.innerHTML = '<div class="status info"><div class="spinner"></div>Processing files...</div>';

                try {
                    const result = await pywebview.api.process_files(selectedFiles.markup, selectedFiles.video);

                    if (result.status === 'success') {
                        let html = '<div class="status success">✅ ' + result.message;
                        if (result.output_path) {
                            html += '<br>Output saved to: ' + result.output_path;
                        }
                        html += '</div>';

                        if (result.report) {
                            html += '<div class="processing-output">' + result.report + '</div>';
                        }

                        processingStatus.innerHTML = html;
                    } else {
                        processingStatus.innerHTML = '<div class="status error">❌ ' + result.message + '</div>';
                    }
                } catch (error) {
                    processingStatus.innerHTML = '<div class="status error">❌ Processing failed: ' + error + '</div>';
                }
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
