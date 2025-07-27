<template>
  <el-container class="clipper-app">
    <!-- Header -->
    <el-header height="60px" class="app-header">
      <div class="header-content">
        <h1 class="app-title">🎬 YT Clipper GUI</h1>
        <div class="status-indicator">
          <el-tag
            :type="getStatusType()"
            :icon="getStatusIcon()"
            size="large"
          >
            {{ getStatusMessage() }}
          </el-tag>
        </div>
      </div>
    </el-header>

    <!-- Main Content -->
    <el-container>
      <!-- Left Sidebar: File Operations -->
      <el-aside width="350px" class="sidebar">
        <el-scrollbar height="100%">
          <div class="sidebar-content">

            <!-- File Upload Section -->
            <el-card class="section-card" shadow="hover">
              <template #header>
                <div class="card-header">
                  <el-icon><FolderOpened /></el-icon>
                  <span>File Selection</span>
                </div>
              </template>

              <!-- File Selection Buttons -->
              <div class="button-group">
                <el-button
                  @click="handleSelectFiles"
                  :loading="isProcessing"
                  type="primary"
                  :icon="FolderOpened"
                  style="width: 100%; margin-bottom: 8px;"
                >
                  Select Files
                </el-button>

                <el-button
                  @click="showVideoCache = true"
                  type="default"
                  :icon="VideoCamera"
                  style="width: 100%;"
                  plain
                >
                  Video Cache
                </el-button>
              </div>

              <!-- Drop Zone -->
              <el-upload
                ref="uploadRef"
                class="upload-drop-zone"
                drag
                :auto-upload="false"
                :on-change="handleFileChange"
                :show-file-list="false"
                multiple
                accept=".json,.mp4,.webm,.avi,.mkv,.mov"
              >
                <el-icon class="upload-icon"><UploadFilled /></el-icon>
                <div class="upload-text">
                  <p>Drop JSON markup here</p>
                  <p class="upload-hint">Optionally include video file</p>
                </div>
              </el-upload>

              <!-- Selected Files Display -->
              <div v-if="hasMarkupFile || hasVideoFile" class="selected-files">
                <el-divider content-position="left">Selected Files</el-divider>

                <el-space direction="vertical" style="width: 100%;" size="small">
                  <div v-if="selectedFiles.markup" class="file-item">
                    <el-tag type="warning" :icon="Document" closable @close="selectedFiles.markup = null">
                      {{ getFileName(selectedFiles.markup) }}
                    </el-tag>
                  </div>

                  <div v-if="selectedFiles.video" class="file-item">
                    <el-tag type="danger" :icon="VideoCamera" closable @close="selectedFiles.video = null">
                      {{ getFileName(selectedFiles.video) }}
                    </el-tag>
                  </div>
                </el-space>
              </div>
            </el-card>

            <!-- Clip Selection Section -->
            <el-card v-if="parsedClips.length > 0" class="section-card" shadow="hover">
              <template #header>
                <div class="card-header">
                  <el-icon><VideoPlay /></el-icon>
                  <span>Clips ({{ selectedClips.length }}/{{ parsedClips.length }})</span>
                </div>
              </template>

              <div class="clip-selection">
                <el-checkbox
                  v-model="selectAllClips"
                  @change="handleSelectAllClips"
                  :indeterminate="isIndeterminate"
                  style="margin-bottom: 12px;"
                >
                  Select All
                </el-checkbox>

                <el-scrollbar max-height="300px">
                  <el-checkbox-group v-model="selectedClips" size="small">
                    <div
                      v-for="(clip, index) in parsedClips"
                      :key="index"
                      class="clip-item"
                    >
                      <el-checkbox :value="index">
                        <div class="clip-info">
                          <div class="clip-title">{{ clip.title || `Clip ${clip.number || index + 1}` }}</div>
                          <div class="clip-duration">{{ formatDuration(clip) }}</div>
                        </div>
                      </el-checkbox>
                    </div>
                  </el-checkbox-group>
                </el-scrollbar>
              </div>
            </el-card>

            <!-- Processing Controls -->
            <el-card class="section-card" shadow="hover">
              <template #header>
                <div class="card-header">
                  <el-icon><Tools /></el-icon>
                  <span>Processing</span>
                </div>
              </template>

              <el-space direction="vertical" style="width: 100%;">
                <el-checkbox v-model="overwriteFiles" size="large">
                  Overwrite existing files (-ow)
                </el-checkbox>

                <el-button
                  @click="handleProcessFiles"
                  :loading="isProcessing"
                  :disabled="!canProcess"
                  type="success"
                  :icon="VideoPlay"
                  size="large"
                  style="width: 100%;"
                >
                  {{ isProcessing ? 'Processing...' : 'Start Processing' }}
                </el-button>

                <!-- Processing Progress -->
                <div v-if="isProcessing" class="processing-progress">
                  <el-progress
                    :percentage="100"
                    :indeterminate="true"
                    :show-text="false"
                  />
                  <div class="progress-text">{{ processingStatus }}</div>
                </div>

                <!-- Processing Result -->
                <el-alert
                  v-if="processingResult"
                  :title="processingResult.message"
                  :type="processingResult.status === 'success' ? 'success' : 'error'"
                  :icon="processingResult.status === 'success' ? SuccessFilled : CircleCloseFilled"
                  show-icon
                  :closable="false"
                />
              </el-space>
            </el-card>

          </div>
        </el-scrollbar>
      </el-aside>

      <!-- Main Content Area -->
      <el-main class="main-content">
        <div v-if="!hasMarkupFile" class="welcome-area">
          <el-empty
            image-size="120"
            description="Drop a JSON markup file to get started"
          >
            <template #image>
              <el-icon size="120"><Document /></el-icon>
            </template>
          </el-empty>
        </div>

        <div v-else class="content-area">
          <!-- Future: Video Preview Area -->
          <el-card v-if="hasVideoFile" class="preview-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <el-icon><Monitor /></el-icon>
                <span>Video Preview</span>
              </div>
            </template>

            <div class="video-preview-placeholder">
              <el-icon size="60"><VideoCamera /></el-icon>
              <p>Video preview coming soon...</p>
              <p class="preview-filename">{{ getFileName(selectedFiles.video || '') }}</p>
            </div>
          </el-card>

          <!-- Future: Timeline Area -->
          <el-card v-if="parsedClips.length > 0" class="timeline-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <el-icon><Timer /></el-icon>
                <span>Timeline</span>
              </div>
            </template>

            <div class="timeline-placeholder">
              <el-icon size="60"><Timer /></el-icon>
              <p>Timeline view coming soon...</p>
              <p>{{ parsedClips.length }} clips loaded</p>
            </div>
          </el-card>
        </div>
      </el-main>
    </el-container>

    <!-- Video Cache Dialog -->
    <el-dialog
      v-model="showVideoCache"
      title="Video Cache Management"
      width="600px"
      :before-close="handleCloseCacheDialog"
    >
      <div class="cache-content">
        <el-empty description="Video cache management coming soon..." />
      </div>

      <template #footer>
        <el-button @click="showVideoCache = false">Close</el-button>
        <el-button type="primary" disabled>Manage Cache</el-button>
      </template>
    </el-dialog>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  FolderOpened,
  VideoCamera,
  UploadFilled,
  Document,
  VideoPlay,
  Tools,
  Monitor,
  Timer,
  SuccessFilled,
  CircleCloseFilled
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { UploadFile } from 'element-plus'
import { useClipperStore } from '@/stores/counter'

// Store
const clipperStore = useClipperStore()

// Local state
const showVideoCache = ref(false)
const overwriteFiles = ref(false)
const parsedClips = ref<any[]>([])
const selectedClips = ref<number[]>([])
const selectAllClips = ref(true)

// Computed properties from store
const selectedFiles = computed(() => clipperStore.selectedFiles)
const isProcessing = computed(() => clipperStore.isProcessing)
const processingStatus = computed(() => clipperStore.processingStatus)
const processingResult = computed(() => clipperStore.processingResult)
const engineStatus = computed(() => clipperStore.engineStatus)
const hasMarkupFile = computed(() => clipperStore.hasMarkupFile)
const hasVideoFile = computed(() => clipperStore.hasVideoFile)

// Local computed properties
const canProcess = computed(() =>
  hasMarkupFile.value && selectedClips.value.length > 0 && !isProcessing.value
)

const isIndeterminate = computed(() =>
  selectedClips.value.length > 0 && selectedClips.value.length < parsedClips.value.length
)

// Initialize engine status on mount
onMounted(async () => {
  try {
    await clipperStore.getEngineStatus()
  } catch (error) {
    console.error('Failed to get engine status:', error)
    ElMessage.error('Failed to initialize engine status')
  }
})

// Status helpers
function getStatusType() {
  if (!engineStatus.value) return 'info'
  return engineStatus.value.engine_ready ? 'success' : 'warning'
}

function getStatusIcon() {
  if (!engineStatus.value) return 'Loading'
  return engineStatus.value.engine_ready ? 'CircleCheckFilled' : 'WarningFilled'
}

function getStatusMessage() {
  if (!engineStatus.value) return 'Loading...'
  return engineStatus.value.engine_ready ? 'Ready' : 'Initializing...'
}

// File handling
function getFileName(path: string): string {
  return path.split(/[\\/]/).pop() || path
}

function handleSelectedFiles(filePaths: string[]) {
  const newFiles = { markup: null as string | null, video: null as string | null }

  for (const filePath of filePaths) {
    const extension = filePath.split('.').pop()?.toLowerCase()

    if (extension === 'json') {
      newFiles.markup = filePath
    } else if (['mp4', 'webm', 'avi', 'mkv', 'mov'].includes(extension || '')) {
      newFiles.video = filePath
    }
  }

  // Update store
  if (newFiles.markup) {
    clipperStore.selectedFiles.markup = newFiles.markup
    parseMarkupFile(newFiles.markup)
  }
  if (newFiles.video) {
    clipperStore.selectedFiles.video = newFiles.video
  }
}

// Parse JSON markup and extract clips via API
async function parseMarkupFile(filePath: string) {
  try {
    const result = await clipperStore.parseMarkupFile(filePath)

    if (result.status === 'success' && result.clips) {
      parsedClips.value = result.clips
      selectedClips.value = Array.from({ length: result.clips.length }, (_, i) => i)
      selectAllClips.value = true

      ElMessage.success(`Loaded ${result.clips.length} clips from markup`)
    } else {
      throw new Error(result.message || 'Failed to parse markup file')
    }
  } catch (error) {
    console.error('Failed to parse markup file:', error)
    ElMessage.error(`Failed to parse markup file: ${error}`)

    // Fallback to empty clips
    parsedClips.value = []
    selectedClips.value = []
    selectAllClips.value = false
  }
}

function formatDuration(clip: any): string {
  if (typeof clip.start === 'number' && typeof clip.end === 'number') {
    const duration = clip.end - clip.start
    return `${formatTime(clip.start)} - ${formatTime(clip.end)} (${formatTime(duration)})`
  }
  if (clip.start && clip.end) {
    return `${clip.start} - ${clip.end}`
  }
  return 'Duration unknown'
}

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = (seconds % 60).toFixed(2)
  return `${mins}:${secs.padStart(5, '0')}`
}

// Event handlers
async function handleSelectFiles() {
  try {
    const files = await clipperStore.selectFiles()
    if (files && files.length > 0) {
      handleSelectedFiles(files)
    }
  } catch (error) {
    console.error('File selection failed:', error)
    ElMessage.error('File selection failed')
  }
}

function handleFileChange(file: UploadFile) {
  if (file.raw) {
    // In a real implementation, we'd handle file paths properly
    // For now, use the file name as a placeholder
    const extension = file.name.split('.').pop()?.toLowerCase()

    if (extension === 'json') {
      clipperStore.selectedFiles.markup = file.name
      parseMarkupFile(file.name)
    } else if (['mp4', 'webm', 'avi', 'mkv', 'mov'].includes(extension || '')) {
      clipperStore.selectedFiles.video = file.name
    }

    ElMessage.success(`Added ${file.name}`)
  }
}

function handleSelectAllClips(value: boolean) {
  if (value) {
    selectedClips.value = Array.from({ length: parsedClips.value.length }, (_, i) => i)
  } else {
    selectedClips.value = []
  }
}

async function handleProcessFiles() {
  if (!canProcess.value) return

  try {
    // TODO: Pass selected clips and overwrite flag to the processing
    await clipperStore.startProcessing()
    ElMessage.success('Processing started successfully')
  } catch (error) {
    console.error('Processing failed:', error)
    ElMessage.error('Processing failed to start')
  }
}

function handleCloseCacheDialog() {
  showVideoCache.value = false
}
</script>

<style scoped>
.clipper-app {
  height: 100vh;
  background: var(--el-bg-color-page);
}

.app-header {
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color);
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.app-title {
  margin: 0;
  font-size: 24px;
  color: var(--el-text-color-primary);
}

.sidebar {
  background: var(--el-bg-color);
  border-right: 1px solid var(--el-border-color);
  padding: 0;
  height: calc(100vh - 60px);
  overflow: hidden;
}

.sidebar-content {
  padding: 16px;
  height: 100%;
}

.section-card {
  margin-bottom: 16px;
}

.section-card:last-child {
  margin-bottom: 0;
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

.upload-drop-zone {
  width: 100%;
}

.upload-drop-zone :deep(.el-upload-dragger) {
  width: 100%;
  height: 120px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
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
  margin-top: 16px;
}

.file-item {
  margin-bottom: 8px;
}

.clip-selection {
  max-height: 250px;
}

.clip-item {
  display: flex;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.clip-item:last-child {
  border-bottom: none;
}

.clip-info {
  flex: 1;
  margin-left: 8px;
}

.clip-title {
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.clip-duration {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.processing-progress {
  width: 100%;
}

.progress-text {
  text-align: center;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 8px;
}

.main-content {
  background: var(--el-bg-color-page);
  padding: 16px;
}

.welcome-area {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.content-area {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.preview-card {
  flex: 1;
  min-height: 300px;
}

.timeline-card {
  height: 200px;
}

.video-preview-placeholder,
.timeline-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--el-text-color-secondary);
}

.preview-filename {
  font-size: 12px;
  color: var(--el-color-primary);
  margin-top: 8px;
}

.cache-content {
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
