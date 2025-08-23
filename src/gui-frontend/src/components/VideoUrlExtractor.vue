<template>
  <div class="video-url-extractor">
    <div v-if="hasVideoUrl" class="video-source-compact">
      <div class="source-info">
        <div class="source-title">{{ videoTitle || 'Video from URL' }}</div>
        <div class="source-url">{{ truncatedUrl }}</div>
      </div>
      <div class="source-actions">
        <el-tooltip content="Download video to cache" placement="top">
          <el-button
            size="small"
            type="primary"
            @click="downloadFromUrl"
            :loading="isDownloading"
            circle
          >
            <el-icon><Download /></el-icon>
          </el-button>
        </el-tooltip>
        <el-tooltip content="Copy URL" placement="top">
          <el-button
            size="small"
            @click="copyUrlToClipboard"
            circle
          >
            <el-icon><CopyDocument /></el-icon>
          </el-button>
        </el-tooltip>
        <el-tooltip v-if="!hasVideoSource" content="No video file selected. Consider downloading from URL or selecting manually." placement="left">
          <el-icon class="warning-icon" color="var(--el-color-warning)">
            <Warning />
          </el-icon>
        </el-tooltip>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ElMessage, ElButton, ElTooltip, ElIcon } from 'element-plus'
import { Download, CopyDocument, Warning } from '@element-plus/icons-vue'
import { useCacheStore } from '@/stores/cache'

// Props
interface Props {
  markupData: { videoUrl?: string; title?: string; [key: string]: unknown } | null
  hasVideoSource: boolean
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  downloadRequested: [url: string, title?: string]
}>()

// Store
const cacheStore = useCacheStore()

// Computed
const hasVideoUrl = computed(() => {
  return Boolean(props.markupData?.videoUrl)
})

const videoUrl = computed(() => {
  return props.markupData?.videoUrl || ''
})

const videoTitle = computed(() => {
  return props.markupData?.title || ''
})

const truncatedUrl = computed(() => {
  const url = videoUrl.value
  if (url.length <= 50) return url
  return url.substring(0, 47) + '...'
})

const isDownloading = computed(() => {
  return cacheStore.isDownloading
})

// Methods
async function downloadFromUrl() {
  if (!videoUrl.value) return

  try {
    const result = await cacheStore.downloadVideo({
      url: videoUrl.value,
      title: videoTitle.value || undefined,
      use_settings_format: true,  // Use settings format to get ytdl_location and other settings
      auto_update: undefined      // Let the backend decide based on settings
    })

    if (result.status === 'success') {
      ElMessage.success('Download started. Check the cache manager for progress.')
      emit('downloadRequested', videoUrl.value, videoTitle.value)
    } else {
      ElMessage.error(`Download failed: ${result.message}`)
    }
  } catch (error) {
    console.error('Download error:', error)
    ElMessage.error('Failed to start download')
  }
}

async function copyUrlToClipboard() {
  try {
    await navigator.clipboard.writeText(videoUrl.value)
    ElMessage.success('URL copied to clipboard')
  } catch (error) {
    console.error('Failed to copy URL:', error)
    ElMessage.error('Failed to copy URL')
  }
}
</script>

<style scoped>
.video-url-extractor {
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background: var(--el-bg-color-page);
}

.video-source-compact {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 36px;
}

.source-info {
  flex: 1;
  min-width: 0;
}

.source-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 2px;
}

.source-url {
  font-family: 'SFMono-Regular', 'Monaco', 'Inconsolata', 'Fira Code', 'Droid Sans Mono', 'Courier New', monospace;
  font-size: 10px;
  color: var(--el-color-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.source-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.warning-icon {
  font-size: 16px;
  cursor: help;
}
</style>
