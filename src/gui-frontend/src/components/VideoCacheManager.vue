<template>
  <el-card class="video-cache-manager" shadow="hover">
    <template #header>
      <div class="cache-header">
        <div class="cache-info">
          <h3>Video Cache</h3>
          <div class="cache-stats">
            <el-tag size="small" type="info">
              {{ cacheStore.totalCachedCount }} videos
            </el-tag>
            <el-tag size="small" type="success">
              {{ cacheStore.formatFileSize(cacheStore.totalCachedSize) }} used
            </el-tag>
            <el-tag v-if="cacheStore.maxCacheSize > 0" size="small" type="warning">
              of {{ cacheStore.formatFileSize(cacheStore.maxCacheSize) }} max
            </el-tag>
          </div>
        </div>

        <div class="cache-actions">
          <el-button
            @click="showDownloadDialog = true"
            type="primary"
            :disabled="cacheStore.isLoading"
            :icon="Download"
          >
            Download Video
          </el-button>

          <el-button
            @click="refreshCache"
            type="default"
            :disabled="cacheStore.isLoading"
            :icon="Refresh"
          >
            Refresh
          </el-button>

          <el-button
            @click="showPurgeDialog = true"
            type="warning"
            :disabled="cacheStore.isLoading || cacheStore.totalCachedCount === 0"
            :icon="Delete"
          >
            Manage Cache
          </el-button>
        </div>
      </div>
    </template>

    <!-- Active Downloads -->
    <div v-if="cacheStore.activeDownloads.length > 0" class="active-downloads">
      <h4>Active Downloads</h4>
      <div
        v-for="download in cacheStore.activeDownloads"
        :key="download.video_id"
        class="download-item"
        :class="{ 'download-error': download.status === 'error' }"
      >
        <div class="download-info">
          <div class="download-title">{{ download.url }}</div>
          <div
            class="download-status"
            :class="{
              'status-error': download.status === 'error',
              'status-completed': download.status === 'completed',
              'status-downloading': download.status === 'downloading'
            }"
          >
            {{ download.status === 'error' ? 'Failed' : download.status }}
          </div>
          <div v-if="download.message && download.status === 'error'" class="download-error-message">
            {{ download.message }}
          </div>
          <div v-else-if="download.message" class="download-message">
            {{ download.message }}
          </div>
        </div>

        <div v-if="download.status !== 'error'" class="download-progress">
          <div class="progress-bar">
            <div
              class="progress-fill"
              :style="{ width: download.progress + '%' }"
            ></div>
          </div>
          <span class="progress-text">{{ download.progress.toFixed(1) }}%</span>
        </div>

        <div class="download-actions">
          <span v-if="download.speed" class="download-speed">{{ download.speed }}</span>
          <span v-if="download.eta" class="download-eta">ETA: {{ download.eta }}</span>
          <el-button
            v-if="download.status === 'error'"
            @click="clearErrorDownload(download.video_id)"
            size="small"
            type="primary"
            :icon="Close"
          >
            Dismiss
          </el-button>
        </div>
      </div>
    </div>

    <!-- Error Display -->
    <el-alert
      v-if="cacheStore.lastError"
      :title="cacheStore.lastError"
      type="error"
      :closable="true"
      @close="cacheStore.clearError"
      show-icon
    />

    <!-- Cached Videos List -->
    <div class="cached-videos">
      <div v-if="cacheStore.isLoading" class="loading">
        Loading cache information...
      </div>

      <div v-else-if="cacheStore.cachedVideos.length === 0" class="empty-cache">
        <p>No videos in cache. Download some videos to get started.</p>
      </div>

      <div v-else class="video-list">
        <div
          v-for="video in sortedVideos"
          :key="video.id"
          class="video-item"
          :class="{ selected: selectedVideoId === video.id }"
        >
          <div class="video-thumbnail" v-if="video.thumbnail_path">
            <img :src="video.thumbnail_path" :alt="video.title" />
          </div>

          <div class="video-details">
            <h4 class="video-title">{{ video.title }}</h4>
            <div class="video-meta">
              <span class="video-platform">{{ video.platform }}</span>
              <span class="video-duration">{{ cacheStore.formatDuration(video.duration) }}</span>
              <span class="video-size">{{ cacheStore.formatFileSize(video.file_size) }}</span>
              <span class="video-format">{{ video.format }}</span>
            </div>
            <div class="video-dates">
              <span class="cached-date">Cached: {{ formatDate(video.cached_at) }}</span>
              <span class="accessed-date">Last used: {{ formatDate(video.last_accessed) }}</span>
            </div>
          </div>

          <div class="video-actions">
            <el-button
              @click="selectVideo(video)"
              type="primary"
              size="small"
            >
              Select
            </el-button>

            <el-button
              @click="deleteVideo(video.id)"
              type="danger"
              size="small"
              :loading="isDeleting.has(video.id)"
              :disabled="cacheStore.isLoading"
            >
              Delete
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- Download Dialog -->
    <VideoDownloadDialog
      v-if="showDownloadDialog"
      @close="showDownloadDialog = false"
      @download="handleDownload"
    />

    <!-- Cache Purge Dialog -->
    <CachePurgeDialog
      v-if="showPurgeDialog"
      :cache-info="cacheStore.cacheInfo"
      @close="showPurgeDialog = false"
      @purge="handlePurge"
    />
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useCacheStore } from '@/stores/cache'
import type { CachedVideo, CacheDownloadRequest, CachePurgeOptions } from '@/types/cache'
import VideoDownloadDialog from './VideoDownloadDialog.vue'
import CachePurgeDialog from './CachePurgeDialog.vue'
import { Download, Refresh, Delete, Close } from '@element-plus/icons-vue'

// Props
interface Props {
  selectedVideoId?: string
}

withDefaults(defineProps<Props>(), {
  selectedVideoId: undefined
})

// Emits
const emit = defineEmits<{
  videoSelected: [video: CachedVideo]
}>()

// Store
const cacheStore = useCacheStore()

// Local state
const showDownloadDialog = ref(false)
const showPurgeDialog = ref(false)
const isDeleting = ref<Set<string>>(new Set())

// Computed
const sortedVideos = computed(() => {
  return [...cacheStore.cachedVideos].sort((a, b) => {
    return new Date(b.last_accessed).getTime() - new Date(a.last_accessed).getTime()
  })
})

// Methods
async function refreshCache() {
  try {
    await cacheStore.loadCacheInfo()
    ElMessage.success('Cache information refreshed')
  } catch {
    ElMessage.error('Failed to refresh cache information')
  }
}

async function handleDownload(request: CacheDownloadRequest) {
  showDownloadDialog.value = false
  const result = await cacheStore.downloadVideo(request)

  if (result.status === 'success') {
    ElMessage.success('Download started successfully')
  } else {
    ElMessage.error(`Download failed: ${result.message}`)
  }
}

async function handlePurge(options: CachePurgeOptions) {
  showPurgeDialog.value = false

  try {
    const result = await cacheStore.purgeCache(options)

    if (result.status === 'success') {
      // Extract number from message like "Deleted 5 videos from cache"
      const deletedCount = result.message?.match(/Deleted (\d+) videos/)?.[1] || '0'

      if (deletedCount === '0') {
        ElMessage.info('No videos were deleted based on the selected criteria')
      } else {
        ElMessage.success({
          message: `Successfully deleted ${deletedCount} videos from cache`,
          duration: 3000
        })
      }
    } else {
      ElMessage.error(`Cache cleanup failed: ${result.message}`)
    }
  } catch {
    ElMessage.error('Failed to clean cache')
  }
}

async function selectVideo(video: CachedVideo) {
  try {
    const selectedVideo = await cacheStore.selectVideoFromCache(video.id)
    if (selectedVideo) {
      emit('videoSelected', selectedVideo)
      ElMessage.success(`Selected: ${video.title}`)
    }
  } catch {
    ElMessage.error('Failed to select video')
  }
}

async function deleteVideo(videoId: string) {
  const video = cacheStore.cachedVideos.find(v => v.id === videoId)
  const videoTitle = video?.title || 'this video'

  try {
    await ElMessageBox.confirm(
      `Are you sure you want to delete "${videoTitle}" from cache? This action cannot be undone.`,
      'Delete Video',
      {
        confirmButtonText: 'Delete',
        cancelButtonText: 'Cancel',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )

    isDeleting.value.add(videoId)

    const result = await cacheStore.deleteVideo(videoId)

    if (result.status === 'success') {
      ElMessage.success(`Successfully deleted "${videoTitle}" from cache`)
    } else {
      ElMessage.error(`Failed to delete video: ${result.message}`)
    }
  } catch (error) {
    // User cancelled - no message needed
    if (error !== 'cancel') {
      ElMessage.error('Failed to delete video')
    }
  } finally {
    isDeleting.value.delete(videoId)
  }
}

// Clear a specific error download
function clearErrorDownload(videoId: string) {
  // Remove from the download progress tracking
  cacheStore.downloadProgress.delete(videoId)
  ElMessage.info('Error dismissed')
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Lifecycle
onMounted(() => {
  cacheStore.loadCacheInfo()
})
</script>

<style scoped>
.video-cache-manager {
  margin-bottom: 1rem;
}

.cache-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.cache-info h3 {
  margin: 0 0 0.5rem 0;
  color: var(--el-text-color-primary);
}

.cache-stats {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.cache-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.active-downloads {
  margin-bottom: 1rem;
  padding: 1rem;
  background-color: var(--el-bg-color-page);
  border-radius: 6px;
  border: 1px solid var(--el-border-color);
}

.active-downloads h4 {
  margin: 0 0 1rem 0;
  color: var(--el-text-color-primary);
}

.download-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  background-color: var(--el-bg-color);
  border-radius: 4px;
  margin-bottom: 0.5rem;
  border: 1px solid var(--el-border-color-light);
}

.download-item.download-error {
  border-color: var(--el-color-danger);
  background-color: var(--el-color-danger-light-9);
}

.download-info {
  flex: 1;
  min-width: 0;
}

.download-title {
  font-weight: 500;
  color: var(--el-text-color-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.download-status {
  font-size: 0.8rem;
  color: var(--el-text-color-secondary);
  text-transform: capitalize;
}

.download-status.status-error {
  color: var(--el-color-danger);
  font-weight: 500;
}

.download-status.status-completed {
  color: var(--el-color-success);
  font-weight: 500;
}

.download-status.status-downloading {
  color: var(--el-color-primary);
  font-weight: 500;
}

.download-error-message {
  font-size: 0.75rem;
  color: var(--el-color-danger);
  margin-top: 0.25rem;
  padding: 0.25rem 0.5rem;
  background-color: var(--el-color-danger-light-8);
  border-radius: 4px;
  border-left: 3px solid var(--el-color-danger);
}

.download-message {
  font-size: 0.75rem;
  color: var(--el-text-color-regular);
  margin-top: 0.25rem;
  font-style: italic;
}

.download-progress {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 120px;
}

.progress-bar {
  width: 80px;
  height: 6px;
  background-color: var(--el-border-color-light);
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background-color: var(--el-color-primary);
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 0.8rem;
  color: var(--el-text-color-secondary);
  min-width: 35px;
}

.download-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: var(--el-text-color-secondary);
}

.loading, .empty-cache {
  text-align: center;
  padding: 2rem;
  color: var(--el-text-color-secondary);
}

.video-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.video-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background-color: var(--el-bg-color-page);
  border: 2px solid transparent;
  border-radius: 6px;
  transition: all 0.2s;
}

.video-item:hover {
  background-color: var(--el-bg-color);
  border-color: var(--el-border-color);
}

.video-item.selected {
  border-color: var(--el-color-primary);
}

.video-thumbnail {
  width: 80px;
  height: 45px;
  flex-shrink: 0;
  border-radius: 4px;
  overflow: hidden;
  background-color: var(--el-border-color-light);
}

.video-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.video-details {
  flex: 1;
  min-width: 0;
}

.video-title {
  margin: 0 0 0.5rem 0;
  color: var(--el-text-color-primary);
  font-size: 1rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.video-meta, .video-dates {
  display: flex;
  gap: 1rem;
  font-size: 0.8rem;
  color: var(--el-text-color-secondary);
}

.video-dates {
  margin-top: 0.25rem;
}

.video-actions {
  display: flex;
  gap: 0.5rem;
  flex-shrink: 0;
}

/* Animation for progress bars */
@keyframes progress-animation {
  0% { background-position: 0 0; }
  100% { background-position: 40px 0; }
}

.progress-fill {
  background-image: linear-gradient(
    45deg,
    rgba(255, 255, 255, 0.1) 25%,
    transparent 25%,
    transparent 50%,
    rgba(255, 255, 255, 0.1) 50%,
    rgba(255, 255, 255, 0.1) 75%,
    transparent 75%,
    transparent
  );
  background-size: 40px 40px;
  animation: progress-animation 1s linear infinite;
}

/* Responsive design */
@media (max-width: 768px) {
  .cache-header {
    flex-direction: column;
    gap: 1rem;
  }

  .cache-actions {
    width: 100%;
    justify-content: stretch;
  }

  .video-item {
    flex-direction: column;
    text-align: center;
  }

  .video-thumbnail {
    align-self: center;
  }
}
</style>
