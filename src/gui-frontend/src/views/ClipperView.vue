<template>
  <el-container class="clipper-app">
    <!-- Header -->
    <el-header height="60px" class="app-header">
      <div class="header-content">
        <h1 class="app-title">🎬 NV Clipper GUI</h1>
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
        <el-container direction="vertical" style="height: 100%;">
          <!-- Scrollable Content Area -->
          <el-main class="sidebar-main">
            <el-scrollbar height="100%">
              <div class="sidebar-content">
                <!-- File Selection Component -->
                <FileSelection
                  :selected-files="selectedFiles"
                  :is-processing="isProcessing"
                  @files-selected="handleSelectedFiles"
                  @select-files-button="handleSelectFiles"
                  @file-changed="handleFileChange"
                  @clear-markup="clearMarkupFile"
                  @clear-video="clearVideoFile"
                  @show-video-cache="showVideoCache = true"
                  @show-settings="showSettings = true"
                />

                <!-- Video URL Extractor -->
                <VideoUrlExtractor
                  v-if="parsedMarkupData"
                  :markup-data="parsedMarkupData"
                  :has-video-source="hasVideoFile"
                  @download-requested="handleVideoDownloadRequest"
                />

                <!-- Clip Selection Component -->
                <ClipSelection
                  :clips="parsedClips"
                  v-model="selectedClips"
                />
              </div>
            </el-scrollbar>
          </el-main>

          <!-- Fixed Processing Footer -->
          <el-footer height="auto" class="processing-footer">
            <ProcessingPanel
              :can-process="canProcess"
              :is-processing="isProcessing"
              :processing-status="processingStatus"
              :processing-result="processingResult"
              :overwrite-enabled="settingsStore.isOverwriteEnabled"
              @start-processing="handleProcessFiles"
              @update-overwrite="updateOverwriteSetting"
            />
          </el-footer>
        </el-container>
      </el-aside>

      <!-- Main Content Area -->
      <MainContent
        :has-markup-file="hasMarkupFile"
        :has-video-file="hasVideoFile"
        :video-file="selectedFiles.video"
        :clip-count="parsedClips.length"
      />
    </el-container>

    <!-- Video Cache Dialog -->
    <el-dialog
      v-model="showVideoCache"
      title="Video Cache Management"
      width="80%"
      :before-close="handleCloseCacheDialog"
      :close-on-click-modal="false"
    >
      <VideoCacheManager
        :selected-video-id="selectedCacheVideoId"
        @video-selected="handleVideoSelected"
      />
    </el-dialog>

    <!-- Settings Dialog -->
    <el-dialog
      v-model="showSettings"
      title="Settings"
      width="900px"
      :before-close="handleCloseSettings"
    >
      <SettingsPanel
        :settings="settingsStore.generalSettings"
        :is-loading="settingsStore.isLoading"
        @update-setting="updateGeneralSetting"
        @reset-settings="handleResetSettings"
        @export-settings="handleExportSettings"
        @import-settings="handleImportSettings"
      />

      <div v-if="settingsStore.lastError" class="error-message">
        <el-alert
          :title="settingsStore.lastError"
          type="error"
          :closable="true"
          @close="settingsStore.clearError()"
        />
      </div>

      <template #footer>
        <el-button @click="handleCloseSettings">Close</el-button>
      </template>
    </el-dialog>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  ElContainer,
  ElHeader,
  ElTag,
  ElAside,
  ElMain,
  ElScrollbar,
  ElFooter,
  ElDialog,
  ElButton,
  ElAlert,
  ElMessage
} from 'element-plus'
import type { UploadFile } from 'element-plus'
import { useClipperStore } from '@/stores/counter'
import { useSettingsStore } from '@/stores/settings'
import SettingsPanel from '@/components/SettingsPanel.vue'
import FileSelection from '@/components/FileSelection.vue'
import ClipSelection from '@/components/ClipSelection.vue'
import ProcessingPanel from '@/components/ProcessingPanel.vue'
import MainContent from '@/components/MainContent.vue'
import VideoCacheManager from '@/components/VideoCacheManager.vue'
import VideoUrlExtractor from '@/components/VideoUrlExtractor.vue'
import type { CachedVideo } from '@/types/cache'
import type { MarkupData } from '@/utils/markup'
import type { ClipInfo } from '@/types/api'

// Store
const clipperStore = useClipperStore()
const settingsStore = useSettingsStore()

// Local state
const showVideoCache = ref(false)
const showSettings = ref(false)
const parsedClips = ref<ClipInfo[]>([])
const selectedClips = ref<number[]>([])
const selectedCacheVideoId = ref<string | undefined>(undefined)
const parsedMarkupData = ref<MarkupData | null>(null)

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

// Initialize engine status and settings on mount
onMounted(async () => {
  try {
    await Promise.all([
      clipperStore.getEngineStatus(),
      settingsStore.loadAllSettings()
    ])
  } catch (error) {
    console.error('Failed to initialize:', error)
    ElMessage.error('Failed to initialize application')
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

      // Store video info if available
      if (result.video_info) {
        // Could store video info here if needed
        console.log('Video info:', result.video_info)
      }

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
    parsedMarkupData.value = null
  }
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

function clearMarkupFile() {
  clipperStore.selectedFiles.markup = null
  parsedClips.value = []
  selectedClips.value = []
  parsedMarkupData.value = null
}

function clearVideoFile() {
  clipperStore.selectedFiles.video = null
}

async function handleProcessFiles() {
  if (!canProcess.value) return

  try {
    await clipperStore.startProcessing(selectedClips.value)
    ElMessage.success('Processing started successfully')
  } catch (error) {
    console.error('Processing failed:', error)
    ElMessage.error('Processing failed to start')
  }
}

async function updateOverwriteSetting(value: boolean) {
  try {
    await settingsStore.updateGeneralSettings({ overwrite: value })
  } catch (error) {
    ElMessage.error('Failed to update overwrite setting')
    console.error('Failed to update overwrite setting:', error)
  }
}

// Dialog handlers
function handleCloseCacheDialog() {
  showVideoCache.value = false
}

function handleVideoSelected(video: CachedVideo) {
  // Set the selected video from cache as the input video
  clipperStore.selectedFiles.video = video.file_path
  selectedCacheVideoId.value = video.id

  ElMessage.success(`Selected video: ${video.title}`)
  showVideoCache.value = false
}

function handleVideoDownloadRequest() {
  // Show a message that the download has started
  ElMessage.info('Download started. Check the Video Cache for progress.')
}

function handleCloseSettings() {
  showSettings.value = false
}

// Settings handlers
async function updateGeneralSetting(key: string, value: unknown) {
  try {
    await settingsStore.updateGeneralSettings({ [key]: value })
    ElMessage.success(`Updated ${key}`)
  } catch (error) {
    ElMessage.error(`Failed to update ${key}`)
    console.error(`Failed to update ${key}:`, error)
  }
}

async function handleResetSettings() {
  try {
    await settingsStore.resetToDefaults()
    ElMessage.success('Settings reset to defaults')
  } catch (error) {
    ElMessage.error('Failed to reset settings')
    console.error('Failed to reset settings:', error)
  }
}

async function handleExportSettings() {
  try {
    const filePath = await settingsStore.exportToArgsFile()
    ElMessage.success(`Settings exported to ${filePath}`)
  } catch (error) {
    ElMessage.error('Failed to export settings')
    console.error('Failed to export settings:', error)
  }
}

async function handleImportSettings() {
  ElMessage.info('Import from args file feature coming soon...')
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

.sidebar-main {
  padding: 0;
  overflow: hidden;
}

.sidebar-content {
  padding: 16px;
}

.processing-footer {
  border-top: 1px solid var(--el-border-color);
  background: var(--el-bg-color);
  padding: 8px;
}

.cache-content {
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.error-message {
  margin-top: 16px;
}
</style>
