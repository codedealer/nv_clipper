<template>
  <el-container class="clipper-app">
    <!-- Header -->
    <el-header height="60px" class="app-header">
      <ClipperHeader
        :engine-status="engineStatus"
        @open-video-cache="dialogManager.openVideoCache"
        @open-settings="dialogManager.openSettings"
        @video-selected="fileHandler.selectVideoAndUpdateUI"
      />
    </el-header>

    <!-- Main Content -->
    <el-container>
      <!-- Left Sidebar: File Operations -->
      <ClipperSidebar
        :selected-files="fileHandler.selectedFiles.value"
        :parsed-clips="markupOps.parsedClips.value"
        :selected-clips="markupOps.selectedClips.value"
        :active-color-grading-clip="colorGrading.activeColorGradingClip.value"
        :is-processing="fileHandler.isProcessing.value"
        :can-process="fileHandler.canProcess.value"
        :processing-status="processingStatus"
        :processing-result="processingResult"
        :parsed-markup-data="markupOps.parsedMarkupData.value"
        :has-video-file="fileHandler.hasVideoFile.value"
        :overwrite-enabled="settingsStore.isOverwriteEnabled"
        @files-selected="fileHandler.handleSelectedFiles"
        @select-files-button="fileHandler.handleSelectFiles"
        @file-changed="fileHandler.handleFileChange"
        @clear-markup="fileHandler.clearMarkupFile"
        @clear-video="fileHandler.clearVideoFile"
        @clip-selected-for-color-grading="colorGrading.handleClipSelectedForColorGrading"
        @start-processing="handleProcessFiles"
        @update-overwrite="dialogManager.updateOverwriteSetting"
        @video-download-requested="handleVideoDownloadRequest"
        @update:selected-clips="(clips: number[]) => (markupOps.selectedClips.value = clips)"
      />

      <!-- Main Content Area -->
      <MainContent
        :has-markup-file="fileHandler.hasMarkupFile.value"
        :has-video-file="fileHandler.hasVideoFile.value"
        :video-file="fileHandler.selectedFiles.value.video"
        :clip-count="markupOps.parsedClips.value.length"
        :selected-clips="markupOps.selectedClips.value"
        :parsed-clips="markupOps.parsedClips.value"
        :active-color-grading-clip="colorGrading.activeColorGradingClip.value"
        :video-duration="videoOps.videoDuration.value"
        :video-info="videoOps.videoInfo.value"
        :is-processing="fileHandler.isProcessing.value"
        :is-mock-markup="colorGrading.isMockMarkup.value"
        :get-clip-color-grading="colorGrading.getClipColorGrading"
        @color-grading-changed="colorGrading.handleColorGradingChanged"
        @copy-to-all-clips="colorGrading.handleCopyToAllClips"
      />
    </el-container>

    <!-- Dialogs -->
    <ClipperDialogs
      :show-video-cache="dialogManager.showVideoCache.value"
      :show-settings="dialogManager.showSettings.value"
      :selected-cache-video-id="dialogManager.selectedCacheVideoId.value"
      :settings="settingsStore.generalSettings"
      :settings-loading="settingsStore.isLoading"
      :settings-error="settingsStore.lastError"
      @close-video-cache="dialogManager.closeVideoCache"
      @close-settings="dialogManager.closeSettings"
      @video-selected="(video: CachedVideo) => dialogManager.handleVideoSelected(video, fileHandler.selectVideoAndUpdateUI)"
      @update-setting="dialogManager.updateGeneralSetting"
      @reset-settings="dialogManager.handleResetSettings"
      @export-settings="dialogManager.handleExportSettings"
      @import-settings="dialogManager.handleImportSettings"
      @clear-settings-error="settingsStore.clearError"
    />
  </el-container>
</template>

<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { ElContainer, ElHeader, ElMessage } from 'element-plus'
import ClipperHeader from '@/components/ClipperHeader.vue'
import ClipperSidebar from '@/components/ClipperSidebar.vue'
import ClipperDialogs from '@/components/ClipperDialogs.vue'
import MainContent from '@/components/MainContent.vue'

import { useClipperStore } from '@/stores/counter'
import { useSettingsStore } from '@/stores/settings'
import { useCacheStore } from '@/stores/cache'

// Composables
import { useVideoOperations } from '@/composables/useVideoOperations'
import { useMarkupOperations } from '@/composables/useMarkupOperations'
import { useDialogManager } from '@/composables/useDialogManager'
import { useFileHandler } from '@/composables/useFileHandler'
import { useColorGrading } from '@/composables/useColorGrading'

// Types
import type { CachedVideo } from '@/types/cache'
import { ENGINE_STATUS } from '@/constants'

// Stores
const clipperStore = useClipperStore()
const settingsStore = useSettingsStore()
const cacheStore = useCacheStore()

// Composables
const videoOps = useVideoOperations()
const markupOps = useMarkupOperations()
const dialogManager = useDialogManager()
const fileHandler = useFileHandler(markupOps, videoOps) // Pass both shared instances
const colorGrading = useColorGrading(videoOps, markupOps) // Pass shared instances

// Computed properties from store
const engineStatus = computed(() => clipperStore.engineStatus)
const processingStatus = computed(() => clipperStore.processingStatus)
const processingResult = computed(() => clipperStore.processingResult)

// Initialize application
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

  // Set up cache video ID for dialog
  setupCacheVideoId()
})

// Setup cache video ID for dialog initialization
function setupCacheVideoId() {
  const cachedVideo = cacheStore.cachedVideos.find(
    video => video.file_path === clipperStore.selectedFiles.video
  )
  dialogManager.setSelectedCacheVideoId(cachedVideo?.id)
}

// Watch for clips changes to initialize color grading
watch(
  markupOps.parsedClips,
  (newClips) => {
    if (newClips.length > 0) {
      // Initialize active clip for color grading when clips are loaded
      colorGrading.initializeActiveClip(newClips)
    } else {
      // Reset color grading when no clips
      colorGrading.resetColorGradingState()
    }
  },
  { immediate: true }
)

// Event handlers
async function handleProcessFiles() {
  const hasModifiedMarkup = markupOps.parsedMarkupData.value !== null

  if (hasModifiedMarkup && markupOps.parsedMarkupData.value) {
    // We have markup data (either mock or modified real markup) - pass it directly
    await fileHandler.handleProcessFiles(markupOps.selectedClips.value, markupOps.parsedMarkupData.value)
  } else {
    // Use normal processing path
    await fileHandler.handleProcessFiles(markupOps.selectedClips.value)
  }
}

function handleVideoDownloadRequest() {
  ElMessage.info('Download started. Check the Video Cache for progress.')
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
</style>
