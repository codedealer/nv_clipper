<template>
  <div class="clipper-gui">
    <header class="header">
      <h1>🎬 YT Clipper GUI</h1>
    </header>

    <div class="container">
      <!-- Status Section -->
      <div class="status-section">
        <h2>📊 Status</h2>
        <div
          :class="['status', getStatusClass()]"
          v-text="getStatusMessage()"
        />
      </div>

      <!-- File Selection -->
      <div class="file-section">
        <h2>📁 File Selection</h2>

        <div class="button-group">
          <button
            @click="handleSelectFiles"
            :disabled="isProcessing"
            class="select-btn"
          >
            Select Files
          </button>
        </div>

        <!-- Drop Zone -->
        <div
          class="drop-zone"
          :class="{ 'dragover': isDragOver }"
          @dragover.prevent="handleDragOver"
          @dragleave="handleDragLeave"
          @drop.prevent="handleDrop"
        >
          <div class="drop-content">
            <span class="drop-icon">📁</span>
            <p>Drop JSON markup file here</p>
            <p class="drop-hint">Optionally include a video file</p>
          </div>
        </div>

        <!-- Selected Files Display -->
        <div v-if="hasMarkupFile || hasVideoFile" class="file-info">
          <h3>Selected Files:</h3>
          <div v-if="selectedFiles.markup" class="file-item">
            <span class="file-type">📄 Markup:</span>
            <span class="file-path">{{ getFileName(selectedFiles.markup) }}</span>
          </div>
          <div v-if="selectedFiles.video" class="file-item">
            <span class="file-type">🎥 Video:</span>
            <span class="file-path">{{ getFileName(selectedFiles.video) }}</span>
          </div>
        </div>
      </div>

      <!-- Processing Section -->
      <div class="processing-section">
        <h2>⚙️ Processing</h2>

        <div class="button-group">
          <button
            @click="handleProcessFiles"
            :disabled="!canProcess"
            class="process-btn"
            :class="{ 'processing': isProcessing }"
          >
            <span v-if="!isProcessing">Process Files</span>
            <span v-else class="processing-text">
              <span class="spinner"></span>
              Processing...
            </span>
          </button>
        </div>

        <!-- Processing Status -->
        <div v-if="processingStatus" class="processing-status">
          <div
            :class="['status', getProcessingStatusClass()]"
            v-text="processingStatus"
          />
        </div>

        <!-- Processing Result -->
        <div v-if="processingResult" class="processing-result">
          <div v-if="processingResult.output_path" class="output-info">
            <strong>Output saved to:</strong> {{ processingResult.output_path }}
          </div>

          <div v-if="processingResult.report" class="report">
            <details>
              <summary>Processing Report</summary>
              <pre>{{ processingResult.report }}</pre>
            </details>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useClipperStore } from '@/stores/counter'
import { storeToRefs } from 'pinia'

const clipperStore = useClipperStore()
const {
  selectedFiles,
  isProcessing,
  processingStatus,
  processingResult,
  hasMarkupFile,
  hasVideoFile,
  canProcess
} = storeToRefs(clipperStore)

const isDragOver = ref(false)

// Initialize engine status on mount
onMounted(async () => {
  try {
    await clipperStore.getEngineStatus()
  } catch (error) {
    console.error('Failed to get engine status:', error)
  }
})

// File handling
function getFileName(path: string): string {
  return path.split(/[\\/]/).pop() || path
}

function handleSelectedFiles(filePaths: string[]) {
  const newFiles = { markup: null as string | null, video: null as string | null }

  for (const filePath of filePaths) {
    const fileName = getFileName(filePath)
    const extension = fileName.split('.').pop()?.toLowerCase()

    if (extension === 'json') {
      newFiles.markup = filePath
    } else if (['mp4', 'webm', 'avi', 'mkv'].includes(extension || '')) {
      newFiles.video = filePath
    }
  }

  clipperStore.setSelectedFiles(newFiles)
}

// File selection
async function handleSelectFiles() {
  try {
    const files = await clipperStore.selectFiles()
    if (files && files.length > 0) {
      handleSelectedFiles(files)
    }
  } catch (error) {
    console.error('File selection failed:', error)
  }
}

// Drag and drop
function handleDragOver(e: DragEvent) {
  e.preventDefault()
  isDragOver.value = true
}

function handleDragLeave() {
  isDragOver.value = false
}

function handleDrop(e: DragEvent) {
  e.preventDefault()
  isDragOver.value = false

  const files = Array.from(e.dataTransfer?.files || [])
  const filePaths = files.map(f => (f as any).path || f.name)
  handleSelectedFiles(filePaths)
}

// Processing
async function handleProcessFiles() {
  try {
    await clipperStore.startProcessing()
  } catch (error) {
    console.error('Processing failed:', error)
  }
}

// Status helpers
function getStatusMessage(): string {
  if (isProcessing.value) {
    return '🔄 Processing files...'
  }
  return '✅ Ready to process files! Drop a JSON markup file or use the file picker.'
}

function getStatusClass(): string {
  if (isProcessing.value) {
    return 'info'
  }
  return 'success'
}

function getProcessingStatusClass(): string {
  if (!processingResult.value) {
    return 'info'
  }
  return processingResult.value.status === 'success' ? 'success' : 'error'
}
</script>

<style scoped>
.clipper-gui {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
  margin: 0;
  padding: 20px;
  background-color: #f5f5f5;
  min-height: 100vh;
}

.header {
  text-align: center;
  margin-bottom: 2rem;
}

.header h1 {
  color: #333;
  margin: 0;
}

.container {
  max-width: 800px;
  margin: 0 auto;
}

.status-section,
.file-section,
.processing-section {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.status-section h2,
.file-section h2,
.processing-section h2 {
  margin-top: 0;
  color: #333;
}

.status {
  padding: 12px 16px;
  border-radius: 6px;
  font-weight: 500;
}

.status.success {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.status.info {
  background-color: #d1ecf1;
  color: #0c5460;
  border: 1px solid #bee5eb;
}

.status.error {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.button-group {
  margin: 1rem 0;
}

.select-btn,
.process-btn {
  background-color: #007bff;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.select-btn:hover,
.process-btn:hover {
  background-color: #0056b3;
}

.select-btn:disabled,
.process-btn:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}

.process-btn.processing {
  background-color: #6c757d;
}

.drop-zone {
  border: 2px dashed #ccc;
  border-radius: 8px;
  padding: 3rem;
  text-align: center;
  margin: 1rem 0;
  transition: border-color 0.2s, background-color 0.2s;
}

.drop-zone:hover,
.drop-zone.dragover {
  border-color: #007bff;
  background-color: #f8f9fa;
}

.drop-content {
  pointer-events: none;
}

.drop-icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 1rem;
}

.drop-hint {
  font-size: 0.9rem;
  color: #666;
  margin: 0.5rem 0 0 0;
}

.file-info {
  background-color: #f8f9fa;
  border-radius: 6px;
  padding: 1rem;
  margin: 1rem 0;
}

.file-info h3 {
  margin-top: 0;
  margin-bottom: 0.5rem;
  color: #333;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0.5rem 0;
}

.file-type {
  font-weight: 500;
  min-width: 80px;
}

.file-path {
  font-family: monospace;
  background-color: #e9ecef;
  padding: 2px 6px;
  border-radius: 3px;
  word-break: break-all;
}

.processing-status,
.processing-result {
  margin: 1rem 0;
}

.output-info {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 1rem;
  word-break: break-all;
}

.report {
  margin-top: 1rem;
}

.report details {
  background-color: #f8f9fa;
  border-radius: 6px;
  padding: 1rem;
}

.report summary {
  cursor: pointer;
  font-weight: 500;
  margin-bottom: 0.5rem;
}

.report pre {
  background-color: #e9ecef;
  padding: 1rem;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 0.9rem;
  margin: 0;
}

.processing-text {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #ffffff40;
  border-top: 2px solid #ffffff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
