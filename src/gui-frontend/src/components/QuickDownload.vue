<template>
  <div class="quick-download">
    <div class="quick-download-input">
      <el-input
        v-model="quickDownloadUrl"
        :placeholder="isQuickDownloading ? quickDownloadStatus : 'Paste URL to quickly download to cache...'"
        size="small"
        style="width: 300px;"
        clearable
        @keyup.enter="handleQuickDownload"
        :loading="isQuickDownloading"
        :disabled="isQuickDownloading"
      >
        <template #append>
          <el-button
            @click="handleQuickDownload"
            :disabled="(!quickDownloadUrl.trim() && !isQuickDownloading) || isQuickDownloading"
            :loading="isQuickDownloading"
            :icon="Download"
            size="small"
            :type="isQuickDownloading ? 'info' : 'primary'"
          >
            {{ isQuickDownloading ? 'Downloading...' : 'Download' }}
          </el-button>
        </template>
      </el-input>
    </div>
    <div v-if="isQuickDownloading && currentQuickDownload" class="quick-download-progress">
      <el-icon class="download-spinner" :size="16">
        <Loading />
      </el-icon>
      <span class="progress-text">{{ quickDownloadStatus }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElInput, ElButton, ElIcon, ElMessage } from 'element-plus'
import { Download, Loading } from '@element-plus/icons-vue'
import { useCacheStore } from '@/stores/cache'
import { useClipperStore } from '@/stores/counter'
import { useSettingsStore } from '@/stores/settings'
import type { CachedVideo } from '@/types/cache'

// Stores
const cacheStore = useCacheStore()
const clipperStore = useClipperStore()
const settingsStore = useSettingsStore()

// Props
interface Props {
  onVideoSelected?: (video: CachedVideo) => void
}

const props = withDefaults(defineProps<Props>(), {
  onVideoSelected: undefined
})

// Emits
const emit = defineEmits<{
  videoSelected: [video: CachedVideo]
}>()

// State
const quickDownloadUrl = ref('')
const quickDownloadVideoId = ref<string | null>(null)

// Computed
const currentQuickDownload = computed(() => {
  if (!quickDownloadVideoId.value) return null
  return cacheStore.downloadProgress.get(quickDownloadVideoId.value)
})

const isQuickDownloading = computed(() => {
  return currentQuickDownload.value?.status &&
         ['starting', 'initializing', 'downloading', 'processing', 'finalizing'].includes(currentQuickDownload.value.status)
})

const quickDownloadStatus = computed(() => {
  if (!currentQuickDownload.value) return ''

  const progress = currentQuickDownload.value
  switch (progress.status) {
    case 'starting':
      return 'Initializing download...'
    case 'initializing':
      return 'Preparing download...'
    case 'downloading':
      return `Downloading ${progress.progress.toFixed(1)}%${progress.speed ? ` (${progress.speed})` : ''}${progress.eta ? ` - ETA: ${progress.eta}` : ''}`
    case 'processing':
      return 'Processing video...'
    case 'finalizing':
      return 'Finalizing...'
    default:
      return ''
  }
})

// Methods
async function handleQuickDownload() {
  const url = quickDownloadUrl.value.trim()
  if (!url) {
    ElMessage.warning('Please enter a video URL')
    return
  }

  try {
    const result = await cacheStore.downloadVideo({
      url,
      use_settings_format: false, // Use default format for quick download
      auto_update: settingsStore.generalSettings?.ytdl_auto_update ?? true
    })

    if (result.status === 'success') {
      if (result.video_id) {
        // New download started - track progress
        quickDownloadVideoId.value = result.video_id
        quickDownloadUrl.value = '' // Clear the input

        ElMessage.success({
          message: 'Download started!',
          duration: 2000
        })
      } else if (result.video) {
        // Video already exists in cache
        quickDownloadUrl.value = '' // Clear the input

        ElMessage.info({
          message: `Video already in cache: ${result.video.title}`,
          duration: 3000
        })

        // Auto-select the existing video
        selectVideo(result.video)
      }
    } else {
      ElMessage.error(`Download failed: ${result.message}`)
    }
  } catch (error) {
    ElMessage.error('Failed to start download')
    console.error('Quick download error:', error)
  }
}

function selectVideo(video: CachedVideo) {
  // Emit to parent or use provided callback
  if (props.onVideoSelected) {
    props.onVideoSelected(video)
  } else {
    emit('videoSelected', video)
  }
}

function handleQuickDownloadComplete(progress: { title?: string; url?: string; [key: string]: unknown }) {
  const videoTitle = progress.title || progress.url
  ElMessage.success({
    message: `Download completed: ${videoTitle}`,
    duration: 5000
  })

  // Auto-select video if no files are currently selected (UX shortcut)
  const hasSelectedVideo = clipperStore.selectedFiles.video
  if (!hasSelectedVideo) {
    // Find the completed video in cache and select it
    const selectCompletedVideo = async () => {
      try {
        // Wait for cache to be updated
        await cacheStore.loadCacheInfo()
        const completedVideo = cacheStore.cachedVideos.find(v => v.id === quickDownloadVideoId.value)

        if (completedVideo) {
          selectVideo(completedVideo)
          console.log('Auto-selected video:', completedVideo.title, completedVideo.file_path)
        } else {
          console.warn('Could not find completed video in cache:', quickDownloadVideoId.value)
          console.log('Available videos:', cacheStore.cachedVideos.map(v => ({ id: v.id, video_id: v.video_id, title: v.title })))
        }
      } catch (error) {
        console.error('Failed to auto-select video:', error)
      }
    }

    // Execute immediately since the completion handler is only called when cache is ready
    selectCompletedVideo()
  } else {
    console.log('Video already selected, skipping auto-selection:', hasSelectedVideo)
  }
}

function handleQuickDownloadError(progress: { message?: string; [key: string]: unknown }) {
  const errorMessage = progress.message || 'Download failed with unknown error'
  ElMessage.error({
    message: `Download failed: ${errorMessage}`,
    duration: 10000,
    showClose: true
  })

  // Clean up tracking state
  quickDownloadVideoId.value = null
}

// Watch for download progress changes
watch(currentQuickDownload, (newProgress) => {
  if (!newProgress) return

  // Handle completion and error states
  if (newProgress.status === 'completed') {
    handleQuickDownloadComplete(newProgress)
  } else if (newProgress.status === 'error') {
    handleQuickDownloadError(newProgress)
  }
}, { immediate: false })
</script>

<style scoped>
.quick-download {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.quick-download-input {
  display: flex;
  align-items: center;
}

.quick-download-progress {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--el-color-info);
}

.download-spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.progress-text {
  font-size: 12px;
  color: var(--el-color-info);
}
</style>
