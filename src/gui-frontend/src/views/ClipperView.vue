<template>
  <el-container class="clipper-app">
    <!-- Header -->
    <el-header height="60px" class="app-header">
      <div class="header-content">
        <div class="header-controls">
          <el-button-group>
            <el-button
              @click="showVideoCache = true"
              :icon="Coin"
            >
              Video Cache
            </el-button>
            <el-button
              @click="showSettings = true"
              :icon="Setting"
            >
              Settings
            </el-button>
          </el-button-group>
        </div>
        <QuickDownload @video-selected="selectVideoAndUpdateUI" />
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
                />

                <!-- Video URL Extractor -->
                <VideoUrlExtractor
                  v-if="parsedMarkupData"
                  :markup-data="parsedMarkupData"
                  :has-video-source="hasVideoFile"
                  @download-requested="handleVideoDownloadRequest"
                />

                <!-- Separator -->
                <div class="sidebar-separator"></div>

                <!-- Clip Selection Component -->
                <ClipSelection
                  :clips="parsedClips"
                  v-model="selectedClips"
                  :active-color-grading-clip="activeColorGradingClip"
                  @clip-selected-for-color-grading="handleClipSelectedForColorGrading"
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
        :selected-clips="selectedClips"
        :parsed-clips="parsedClips"
        :active-color-grading-clip="activeColorGradingClip"
        :video-duration="videoDuration"
        :video-info="videoInfo"
        :is-processing="isProcessing"
        @color-grading-changed="handleColorGradingChanged"
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
import { ref, computed, onMounted, watch } from 'vue'
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
  ElButtonGroup,
  ElAlert,
  ElMessage
} from 'element-plus'
import { Coin, Setting } from '@element-plus/icons-vue'
import type { UploadFile } from 'element-plus'
import QuickDownload from '@/components/QuickDownload.vue'
import { useClipperStore } from '@/stores/counter'
import { useSettingsStore } from '@/stores/settings'
import { useCacheStore } from '@/stores/cache'
import SettingsPanel from '@/components/SettingsPanel.vue'
import FileSelection from '@/components/FileSelection.vue'
import ClipSelection from '@/components/ClipSelection.vue'
import ProcessingPanel from '@/components/ProcessingPanel.vue'
import MainContent from '@/components/MainContent.vue'
import VideoCacheManager from '@/components/VideoCacheManager.vue'
import VideoUrlExtractor from '@/components/VideoUrlExtractor.vue'
import type { CachedVideo } from '@/types/cache'
import type { MarkupData } from '@/utils/markup'
import type { ClipInfo, VideoInfo } from '@/types/api'

// Store
const clipperStore = useClipperStore()
const settingsStore = useSettingsStore()
const cacheStore = useCacheStore()

// Local state
const showVideoCache = ref(false)
const showSettings = ref(false)
const parsedClips = ref<ClipInfo[]>([])
const selectedClips = ref<number[]>([])
const activeColorGradingClip = ref<number | null>(null) // Index of clip active for color grading
const parsedMarkupData = ref<MarkupData | null>(null)
const videoDuration = ref<number | null>(null) // Duration of current video in seconds
const videoInfo = ref<VideoInfo | null>(null) // Full video information from ffprobe
const isCreatingMockMarkup = ref(false) // Flag to prevent concurrent mock markup creation

// Computed properties
const selectedCacheVideoId = computed(() => {
  // Find the cached video that matches the currently selected video file
  if (!clipperStore.selectedFiles.video) return undefined

  const cachedVideo = cacheStore.cachedVideos.find(
    video => video.file_path === clipperStore.selectedFiles.video
  )
  return cachedVideo?.id
})

// Video duration watcher to update active color grading clip

// Watch for video file changes to clean up clips panel
watch(
  () => clipperStore.selectedFiles.video,
  (newVideo, oldVideo) => {
    // If video was removed (but not just changed to a different video)
    if (oldVideo && !newVideo) {
      // Clear clips panel data
      parsedClips.value = []
      selectedClips.value = []
      activeColorGradingClip.value = null
      if (!clipperStore.selectedFiles.markup) {
        // Only clear parsed markup if we don't have a real markup file
        parsedMarkupData.value = null
      }
    }
  }
)

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
  (hasMarkupFile.value || parsedClips.value.length > 0) && selectedClips.value.length > 0 && !isProcessing.value
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

    // If we have video but no markup, check if we should create a mock markup
    if (!newFiles.markup && !clipperStore.hasMarkupFile && !isCreatingMockMarkup.value) {
      createMockMarkupForVideo(newFiles.video)
    }
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
        videoDuration.value = result.video_info.duration ?? null
        videoInfo.value = result.video_info
        console.log('Video info:', result.video_info)
      }

      // Set the first valid clip as active for color grading
      activeColorGradingClip.value = findFirstValidClip(result.clips, videoDuration.value)

      ElMessage.success(`Loaded ${result.clips.length} clips from markup (replacing any mock markup)`)
    } else {
      throw new Error(result.message || 'Failed to parse markup file')
    }
  } catch (error) {
    console.error('Failed to parse markup file:', error)
    ElMessage.error(`Failed to parse markup file: ${error}`)

    // Fallback to empty clips
    parsedClips.value = []
    selectedClips.value = []
    activeColorGradingClip.value = null
    parsedMarkupData.value = null
  }
}

// Create a mock markup for video-only scenarios
async function createMockMarkupForVideo(videoPath: string) {
  // Prevent concurrent calls
  if (isCreatingMockMarkup.value) {
    console.log('Mock markup creation already in progress, skipping...')
    return
  }

  try {
    isCreatingMockMarkup.value = true
    ElMessage.info('Creating mock markup for video file...')

    // Get video information to determine duration
    const videoInfoResponse = await window.pywebview.api.get_video_info(videoPath)

    // Add debug logging
    console.log('Video info response:', videoInfoResponse)

    if (videoInfoResponse.status !== 'success') {
      throw new Error(videoInfoResponse.message || 'Failed to get video information')
    }

    // Get duration from video_info and store full video info
    const duration = videoInfoResponse.video_info?.duration
    if (!duration || duration <= 0) {
      throw new Error('Video duration not available in response')
    }

    // Store the full video info
    videoInfo.value = videoInfoResponse.video_info ?? null
    videoDuration.value = duration
    const videoName = videoPath.split(/[/\\]/).pop()?.replace(/\.[^/.]+$/, '') || 'video'

    // Create a single clip that spans the entire video
    const mockClip = {
      number: 1,
      title: `Full Video - ${videoName}`,
      start: 0,
      end: duration,
      duration: duration,
      speed: 1.0,
      crop: '',
      enableZoomPan: false,
      overrides: {}
    }

    // Set the parsed clips
    parsedClips.value = [mockClip]
    selectedClips.value = [0] // Select the mock clip by default

    // For mock clips, we know the duration matches the video, so it's always valid
    activeColorGradingClip.value = 0 // Set as active for color grading

    // Create mock markup data structure that follows the proper schema
    parsedMarkupData.value = {
      platform: 'ytc_generic',
      videoID: 'unknown',
      videoTitle: videoName,
      videoUrl: '',
      videoTag: '[ytc_generic@unknown]',
      newMarkerSpeed: 1,
      newMarkerCrop: '',
      titleSuffix: 'mock',
      version: '5.32.0',
      markerPairs: [{
        number: 1,
        start: 0,
        end: duration,
        speed: 1,
        crop: '',
        enableZoomPan: false,
        overrides: {}
      }],
      // Legacy structure for compatibility
      markers: [{
        start: 0,
        end: duration,
        title: mockClip.title
      }],
      totalDuration: duration
    }

    ElMessage.success(`Created mock markup for ${videoName} (${Math.round(duration)}s)`)

  } catch (error) {
    console.error('Failed to create mock markup:', error)
    ElMessage.error(`Failed to create mock markup: ${error}`)

    // Fallback to empty state
    parsedClips.value = []
    selectedClips.value = []
    activeColorGradingClip.value = null
    parsedMarkupData.value = null
  } finally {
    isCreatingMockMarkup.value = false
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

// Helper function to find the first clip with valid timestamps
function findFirstValidClip(clips: ClipInfo[], videoDuration: number | null): number | null {
  if (clips.length === 0) return null

  // If no video duration info, use first clip
  if (!videoDuration || videoDuration <= 0) return 0

  // Find first clip that starts within video bounds
  for (let i = 0; i < clips.length; i++) {
    const clip = clips[i]
    if (clip.start < videoDuration) {
      return i
    }
  }

  // If no valid clips found, still return 0 but the ColorGradingPanel will handle bounds
  return 0
}

function clearMarkupFile() {
  clipperStore.selectedFiles.markup = null
  parsedClips.value = []
  selectedClips.value = []
  activeColorGradingClip.value = null
  parsedMarkupData.value = null

  // If we still have a video file, create mock markup as fallback
  if (clipperStore.hasVideoFile && clipperStore.selectedFiles.video && !isCreatingMockMarkup.value) {
    ElMessage.info('Markup file removed - creating mock markup for video')
    createMockMarkupForVideo(clipperStore.selectedFiles.video)
  }
}

function clearVideoFile() {
  clipperStore.selectedFiles.video = null
  videoDuration.value = null
  videoInfo.value = null

  // Clear clips panel data when video is removed
  parsedClips.value = []
  selectedClips.value = []
  activeColorGradingClip.value = null
  parsedMarkupData.value = null
}

async function handleProcessFiles() {
  if (!canProcess.value) return

  try {
    // Handle mock markup scenario - create a temporary markup file
    let markupPath = clipperStore.selectedFiles.markup

    if (!markupPath && parsedMarkupData.value) {
      // We have mock markup data but no file - create a temporary markup file
      markupPath = await createTempMarkupFile(parsedMarkupData.value)

      if (!markupPath) {
        throw new Error('Failed to create temporary markup file for processing')
      }
    }

    if (!markupPath) {
      throw new Error('No markup file or data available for processing')
    }

    // Temporarily set the markup path for processing
    const originalMarkupPath = clipperStore.selectedFiles.markup
    clipperStore.selectedFiles.markup = markupPath

    try {
      await clipperStore.startProcessing(selectedClips.value)
      ElMessage.success('Processing started successfully')
    } finally {
      // Restore original markup path (might be null for mock scenarios)
      clipperStore.selectedFiles.markup = originalMarkupPath
    }

  } catch (error) {
    console.error('Processing failed:', error)
    ElMessage.error('Processing failed to start')
  }
}

// Create a temporary markup file for mock markup scenarios
async function createTempMarkupFile(markupData: any): Promise<string | null> {
  try {
    // Call a new API method to create a temporary markup file
    const result = await window.pywebview.api.create_temp_markup_file(markupData)

    if (result.status === 'success' && result.temp_file_path) {
      return result.temp_file_path
    } else {
      console.error('Failed to create temp markup file:', result.message)
      return null
    }
  } catch (error) {
    console.error('Error creating temp markup file:', error)
    return null
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
  // Use shared video selection logic
  selectVideoAndUpdateUI(video)
  showVideoCache.value = false
}

function handleVideoDownloadRequest() {
  // Show a message that the download has started
  ElMessage.info('Download started. Check the Video Cache for progress.')
}

// Shared function for video selection logic
function selectVideoAndUpdateUI(video: CachedVideo) {
  // Set the selected video using the proper store method
  clipperStore.setVideoFile(video.file_path)

  // Auto-select video if no files are currently selected
  const hasSelectedVideo = clipperStore.selectedFiles.video
  if (hasSelectedVideo && !clipperStore.hasMarkupFile && !isCreatingMockMarkup.value) {
    // Create mock markup for this video to enable UI functionality
    createMockMarkupForVideo(video.file_path)
  }

  ElMessage.success({
    message: `Selected: ${video.title}`,
    duration: 3000
  })
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

// Color grading handler
function handleColorGradingChanged(clipNumber: number, filter: string) {
  // Find the clip and update its color grading
  const clip = parsedClips.value.find(c => c.number === clipNumber)
  if (clip) {
    // Update the clip's color grading in the overrides
    clip.overrides = {
      ...clip.overrides,
      colorGrading: filter || undefined
    }

    ElMessage.success(filter ? 'Color grading applied to clip' : 'Color grading removed from clip')
  } else {
    ElMessage.error('Clip not found')
  }
}

// Handle clip selection for color grading (separate from processing selection)
function handleClipSelectedForColorGrading(clipIndex: number) {
  if (clipIndex >= 0 && clipIndex < parsedClips.value.length) {
    activeColorGradingClip.value = clipIndex
    ElMessage.info(`Switched to clip ${clipIndex + 1} for color grading`)
  }
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

.header-controls {
  display: flex;
  align-items: center;
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
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0;
}

.sidebar-separator {
  height: 1px;
  background-color: var(--el-border-color-light);
  margin: 0;
}

/* Responsive sidebar adjustments */
@media (min-width: 1024px) {
  .sidebar {
    width: 350px !important;
    min-width: 350px;
    max-width: 400px;
  }
}

@media (min-width: 1440px) {
  .sidebar {
    width: 350px !important;
    max-width: 400px;
  }
}

.processing-footer {
  border-top: 1px solid var(--el-border-color);
  background: var(--el-bg-color);
  padding: 0;
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
