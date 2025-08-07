<template>
  <div class="video-url-extractor">
    <div v-if="hasVideoUrl" class="video-url-info">
      <el-alert
        :title="`Video URL found in markup: ${videoTitle || 'Unknown'}`"
        type="info"
        :closable="false"
        show-icon
      >
        <template #default>
          <div class="url-details">
            <p class="video-url">{{ videoUrl }}</p>
            <div class="url-actions">
              <el-button
                size="small"
                type="primary"
                @click="downloadFromUrl"
                :loading="isDownloading"
              >
                <i class="icon-download"></i>
                Download to Cache
              </el-button>
              <el-button
                size="small"
                type="default"
                @click="copyUrlToClipboard"
              >
                <i class="icon-copy"></i>
                Copy URL
              </el-button>
            </div>
          </div>
        </template>
      </el-alert>
    </div>

    <div v-if="!hasVideoSource && hasVideoUrl" class="suggestion">
      <el-alert
        title="No video file selected"
        type="warning"
        :closable="false"
        show-icon
      >
        <template #default>
          <p>Consider downloading the video from the URL found in the markup file, or select a video file manually.</p>
        </template>
      </el-alert>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useCacheStore } from '@/stores/cache'
import type { MarkupData } from '@/utils/markup'

// Props
interface Props {
  markupData: MarkupData | null
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
  margin-top: 1rem;
}

.video-url-info {
  margin-bottom: 1rem;
}

.url-details {
  margin-top: 0.5rem;
}

.video-url {
  font-family: monospace;
  font-size: 0.8rem;
  color: var(--el-color-info);
  margin: 0.5rem 0;
  word-break: break-all;
  background-color: var(--el-bg-color-page);
  padding: 0.5rem;
  border-radius: 4px;
}

.url-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.suggestion {
  margin-top: 1rem;
}
</style>
