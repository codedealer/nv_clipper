<template>
  <el-card class="section-card" shadow="hover">
    <!-- File Selection Buttons -->
    <div class="button-group">
      <el-button
        @click="handleSelectFiles"
        :loading="isProcessing"
        type="primary"
        :icon="FolderOpened"
        style="width: 100%;"
      >
        Select Files
      </el-button>
    </div>

    <!-- Drop Zone -->
    <div class="drop-zone-container">
      <div
        ref="dropZoneOverlay"
        class="custom-drop-zone-overlay"
        @dragenter="handleDragEnter"
        @dragleave="handleDragLeave"
        @dragover="handleDragOver"
      ></div>
      <div
        class="custom-drop-zone"
        :class="{
          'drop-zone-error': setupError,
          'drop-zone-active': isDragActive
        }"
      >
        <el-icon class="upload-icon"><UploadFilled /></el-icon>
        <div class="upload-text">
          <p v-if="!setupError && !isDragActive">Drop JSON markup here</p>
          <p v-else-if="isDragActive" class="active-text">Release to drop files</p>
          <p v-else class="error-text">Drag & Drop Error: {{ setupError }}</p>
          <p class="upload-hint" v-if="!setupError && !isDragActive">Optionally include video file</p>
          <p class="upload-hint" v-else-if="!isDragActive">Please check the console for details</p>
        </div>
      </div>
    </div>    <!-- Selected Files Display -->
    <div v-if="hasMarkupFile || hasVideoFile" class="selected-files">
      <div class="files-header">Selected Files</div>
      <div class="file-tags">
        <el-tag
          v-if="selectedFiles.markup"
          type="warning"
          size="small"
          :icon="Document"
          closable
          @close="clearMarkupFile"
        >
          {{ getFileName(selectedFiles.markup) }}
        </el-tag>
        <el-tag
          v-if="selectedFiles.video"
          type="danger"
          size="small"
          :icon="VideoCamera"
          closable
          @close="clearVideoFile"
        >
          {{ getFileName(selectedFiles.video) }}
        </el-tag>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import type { UploadFile } from 'element-plus'
import { ElMessage } from 'element-plus'
import {
  FolderOpened,
  VideoCamera,
  UploadFilled,
  Document
} from '@element-plus/icons-vue'
import { waitForPywebview } from '@/utils/api'

interface Props {
  selectedFiles: {
    markup: string | null
    video: string | null
  }
  isProcessing: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'files-selected': [filePaths: string[]]
  'select-files-button': []
  'file-changed': [file: UploadFile]
  'clear-markup': []
  'clear-video': []
}>()

// Computed
const hasMarkupFile = computed(() => !!props.selectedFiles.markup)
const hasVideoFile = computed(() => !!props.selectedFiles.video)

// Methods
function getFileName(path: string): string {
  return path.split(/[\\/]/).pop() || path
}

// Types for drag and drop
interface DroppedFilesHandler {
  (filePaths: string[]): void
}

// Extend window interface for TypeScript
declare global {
  interface Window {
    handleDroppedFiles?: DroppedFilesHandler
  }
}

// State for tracking setup and drag state
const isDragDropSetup = ref(false)
const setupError = ref<string | null>(null)
const isDragActive = ref(false)
// const dragCounter = ref(0) // Track nested drag enter/leave events (prevents flicker)

async function handleSelectFiles() {
  try {
    // Emit event to request file dialog from parent
    emit('select-files-button')
  } catch (error) {
    console.error('File selection failed:', error)
    ElMessage.error('File selection failed')
  }
}

async function setupDragDrop(): Promise<void> {
  if (isDragDropSetup.value) {
    console.log('Drag and drop already setup, skipping')
    return
  }

  try {
    console.log('Setting up pywebview drag and drop...')
    setupError.value = null

    const api = await waitForPywebview()
    if (!api) {
      throw new Error('Failed to get pywebview API')
    }

    const result = await api.setup_drag_drop()
    if (!result || result.status !== 'success') {
      const errorMessage = result?.message || 'Unknown setup error'
      throw new Error(`Setup failed: ${errorMessage}`)
    }

    console.log('Pywebview drag and drop setup successful')

    // Setup secure global handler
    const handleDroppedFiles: DroppedFilesHandler = (filePaths: string[]) => {
      try {
        console.log('handleDroppedFiles called with:', filePaths)

        // Reset drag state
        isDragActive.value = false

        // Validate input
        if (!Array.isArray(filePaths) || filePaths.length === 0) {
          console.warn('Invalid file paths received:', filePaths)
          ElMessage.warning('No valid files were dropped')
          return
        }

        // Filter valid paths
        const validPaths = filePaths.filter(path =>
          typeof path === 'string' && path.trim().length > 0
        )

        if (validPaths.length === 0) {
          console.warn('No valid file paths after filtering:', filePaths)
          ElMessage.warning('No valid files were dropped')
          return
        }

        console.log(`Emitting files-selected with ${validPaths.length} files:`, validPaths)

        // Emit to parent for processing
        emit('files-selected', validPaths)

      } catch (error) {
        console.error('Error handling dropped files:', error)
        ElMessage.error('Error processing dropped files')
        // Reset drag state on error
        isDragActive.value = false
      }
    }    // Safely assign to window (replace any existing handler)
    if (window.handleDroppedFiles) {
      console.log('Replacing existing handleDroppedFiles handler')
    }
    window.handleDroppedFiles = handleDroppedFiles
    isDragDropSetup.value = true

    console.log('Drag and drop handler registered successfully')

  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error'
    console.error('Error setting up drag and drop:', errorMessage)
    setupError.value = errorMessage
    ElMessage.error(`Failed to setup drag and drop: ${errorMessage}`)
  }
}

function clearMarkupFile() {
  emit('clear-markup')
}

function clearVideoFile() {
  emit('clear-video')
}

// Drag event handlers for visual feedback only
function handleDragEnter(): void {
  isDragActive.value = true
}

function handleDragLeave(): void {
  isDragActive.value = false
}

function handleDragOver(event: DragEvent): void {
  // Prevent default to allow drop, but don't stop propagation
  // This allows pywebview to still handle the event
  event.preventDefault()
}

// Lifecycle hooks
onMounted(() => {
  setupDragDrop()
})

onUnmounted(() => {
  // Clean up global handler when component is destroyed
  if (window.handleDroppedFiles) {
    console.log('Cleaning up drag and drop handler')
    delete window.handleDroppedFiles
    isDragDropSetup.value = false
  }
})

</script>

<style scoped>
.section-card {
  margin-bottom: 0;
  border-radius: 0;
  border: none;
  box-shadow: none;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.button-group {
  margin-bottom: 16px;
}

.button-row {
  display: flex;
  gap: 0;
  width: 100%;
}

.upload-drop-zone {
  width: 100%;
}

.drop-zone-container {
  position: relative;
  width: 100%;
  height: 120px;
}

.custom-drop-zone-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 10;
}

.custom-drop-zone {
  width: 100%;
  height: 100%;
  border: 2px dashed var(--el-color-primary);
  border-radius: 6px;
  background-color: var(--el-fill-color-light);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
}

.custom-drop-zone:hover {
  border-color: var(--el-color-primary-light-3);
  background-color: var(--el-color-primary-light-9);
}

.custom-drop-zone.drop-zone-active {
  border-color: var(--el-color-success);
  background-color: var(--el-color-success-light-9);
  transform: scale(1.02);
}

.custom-drop-zone.drop-zone-error {
  border-color: var(--el-color-danger);
  background-color: var(--el-color-danger-light-9);
}

.custom-drop-zone.drop-zone-error:hover {
  border-color: var(--el-color-danger-light-3);
  background-color: var(--el-color-danger-light-8);
}

.error-text {
  color: var(--el-color-danger);
  font-weight: 500;
}

.active-text {
  color: var(--el-color-success);
  font-weight: 600;
}

.upload-icon {
  font-size: 32px;
  color: var(--el-color-primary);
  margin-bottom: 8px;
}

.upload-text {
  text-align: center;
}

.upload-text p {
  margin: 4px 0;
}

.upload-hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.selected-files {
  margin-top: 12px;
}

.files-header {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-regular);
  margin-bottom: 6px;
}

.file-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.file-item {
  margin-bottom: 8px;
}
</style>
