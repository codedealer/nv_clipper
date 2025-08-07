<template>
  <el-dialog
    v-model="visible"
    title="Manage Video Cache"
    width="600px"
    :before-close="handleClose"
  >
    <!-- Current Cache Stats -->
    <div class="cache-summary">
      <h4>Current Cache Status</h4>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="Total Videos">
          {{ cacheInfo?.total_count ?? 0 }}
        </el-descriptions-item>
        <el-descriptions-item label="Total Size">
          {{ formatFileSize(cacheInfo?.total_size ?? 0) }}
        </el-descriptions-item>
        <el-descriptions-item label="Max Size" v-if="cacheInfo?.max_size && cacheInfo.max_size > 0">
          {{ formatFileSize(cacheInfo.max_size) }}
        </el-descriptions-item>
        <el-descriptions-item label="Cache Directory" :span="2">
          <el-text type="info" size="small">{{ cacheInfo?.cache_dir ?? 'Unknown' }}</el-text>
        </el-descriptions-item>
      </el-descriptions>
    </div>

    <!-- Purge Options -->
    <div class="purge-options">
      <h4>Cleanup Options</h4>

      <el-form label-width="auto">
        <el-form-item>
          <el-checkbox v-model="options.deleteOldVideos">
            Delete videos older than
          </el-checkbox>
          <div v-if="options.deleteOldVideos" style="margin-top: 8px; margin-left: 24px;">
            <el-input-number
              v-model="options.olderThanDays"
              :min="1"
              :max="365"
              size="small"
              style="width: 100px;"
            />
            <span style="margin-left: 8px;">days</span>
          </div>
        </el-form-item>

        <el-form-item>
          <el-checkbox v-model="options.enforceSizeLimit">
            Enforce size limit
          </el-checkbox>
          <div v-if="options.enforceSizeLimit" style="margin-top: 8px; margin-left: 24px;">
            <el-input-number
              v-model="options.sizeLimitMB"
              :min="100"
              :step="100"
              size="small"
              style="width: 120px;"
            />
            <span style="margin-left: 8px;">MB</span>
            <el-text type="info" size="small" style="margin-left: 8px;">
              (Oldest videos will be deleted first)
            </el-text>
          </div>
        </el-form-item>

        <el-form-item>
          <el-checkbox v-model="options.keepRecentOnly">
            Keep only the most recent
          </el-checkbox>
          <div v-if="options.keepRecentOnly" style="margin-top: 8px; margin-left: 24px;">
            <el-input-number
              v-model="options.keepCount"
              :min="1"
              :max="100"
              size="small"
              style="width: 100px;"
            />
            <span style="margin-left: 8px;">videos</span>
          </div>
        </el-form-item>

        <el-form-item>
          <el-button
            @click="deleteAllVideos"
            type="danger"
            plain
            :disabled="!cacheInfo?.total_count"
          >
            Delete All Videos
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- Preview of what will be deleted -->
    <div v-if="videosToDelete.length > 0" class="deletion-preview">
      <h4>
        <el-icon><WarningFilled /></el-icon>
        Videos to be deleted ({{ videosToDelete.length }})
      </h4>
      <el-card>
        <div class="preview-list">
          <div
            v-for="video in videosToDelete.slice(0, 5)"
            :key="video.id"
            class="preview-item"
          >
            <el-text truncated>{{ video.title }}</el-text>
            <el-text type="info" size="small">{{ formatFileSize(video.file_size) }}</el-text>
            <el-text type="info" size="small">{{ formatDate(video.cached_at) }}</el-text>
          </div>
          <div v-if="videosToDelete.length > 5" class="more-items">
            <el-text type="info">... and {{ videosToDelete.length - 5 }} more videos</el-text>
          </div>
        </div>
        <div class="preview-stats">
          <el-text type="warning" size="large">
            <strong>Total space to be freed: {{ formatFileSize(totalDeleteSize) }}</strong>
          </el-text>
        </div>
      </el-card>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">Cancel</el-button>
        <el-button
          type="warning"
          @click="handlePurge"
          :disabled="!hasValidOptions"
          :icon="Delete"
        >
          Clean Cache
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessageBox } from 'element-plus'
import type { CacheInfo, CachePurgeOptions, CachedVideo } from '@/types/cache'
import { WarningFilled, Delete } from '@element-plus/icons-vue'

// Props
interface Props {
  cacheInfo: CacheInfo | null
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  close: []
  purge: [options: CachePurgeOptions]
}>()

// Local state
const visible = ref(true)
const options = ref({
  deleteOldVideos: false,
  olderThanDays: 30,
  enforceSizeLimit: false,
  sizeLimitMB: 1000,
  keepRecentOnly: false,
  keepCount: 10,
  deleteAll: false
})

// Computed
const hasValidOptions = computed(() => {
  return options.value.deleteOldVideos ||
         options.value.enforceSizeLimit ||
         options.value.keepRecentOnly ||
         options.value.deleteAll
})

const videosToDelete = computed(() => {
  if (!props.cacheInfo?.videos) return []

  const videos = [...props.cacheInfo.videos]
  const toDelete: CachedVideo[] = []
  const now = new Date()

  if (options.value.deleteAll) {
    return videos
  }

  // Delete old videos
  if (options.value.deleteOldVideos) {
    const cutoffDate = new Date(now.getTime() - options.value.olderThanDays * 24 * 60 * 60 * 1000)
    const oldVideos = videos.filter(v => new Date(v.cached_at) < cutoffDate)
    toDelete.push(...oldVideos)
  }

  // Sort by last accessed (oldest first) for size limit and keep recent logic
  const sortedByAccess = videos.sort((a, b) =>
    new Date(a.last_accessed).getTime() - new Date(b.last_accessed).getTime()
  )

  // Enforce size limit
  if (options.value.enforceSizeLimit) {
    const maxSize = options.value.sizeLimitMB * 1024 * 1024
    let currentSize = props.cacheInfo.total_size

    for (const video of sortedByAccess) {
      if (currentSize <= maxSize) break
      if (!toDelete.includes(video)) {
        toDelete.push(video)
        currentSize -= video.file_size
      }
    }
  }

  // Keep only recent videos
  if (options.value.keepRecentOnly) {
    const videosToKeep = sortedByAccess.slice(-options.value.keepCount)
    const videosToRemove = videos.filter(v => !videosToKeep.includes(v))
    for (const video of videosToRemove) {
      if (!toDelete.includes(video)) {
        toDelete.push(video)
      }
    }
  }

  return toDelete
})

const totalDeleteSize = computed(() => {
  return videosToDelete.value.reduce((total, video) => total + video.file_size, 0)
})

// Methods
function handleClose() {
  visible.value = false
  emit('close')
}

async function deleteAllVideos() {
  const totalVideos = props.cacheInfo?.total_count || 0
  const totalSize = formatFileSize(props.cacheInfo?.total_size || 0)

  try {
    await ElMessageBox.confirm(
      `This will permanently delete ALL ${totalVideos} videos (${totalSize}) from the cache. This action cannot be undone.`,
      'Delete All Videos',
      {
        confirmButtonText: 'Delete All',
        cancelButtonText: 'Cancel',
        type: 'error',
        confirmButtonClass: 'el-button--danger'
      }
    )

    options.value.deleteAll = true
    handlePurge()
  } catch {
    // User cancelled - no action needed
  }
}

function handlePurge() {
  const purgeOptions: CachePurgeOptions = {}

  if (options.value.deleteAll) {
    // Delete all - no specific options needed
    emit('purge', {})
    return
  }

  if (options.value.deleteOldVideos) {
    purgeOptions.older_than_days = options.value.olderThanDays
  }

  if (options.value.enforceSizeLimit) {
    purgeOptions.size_limit_mb = options.value.sizeLimitMB
  }

  if (options.value.keepRecentOnly) {
    purgeOptions.keep_most_recent = options.value.keepCount
  }

  emit('purge', purgeOptions)
  handleClose()
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'

  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))

  return parseFloat((bytes / Math.pow(1024, i)).toFixed(2)) + ' ' + sizes[i]
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString()
}
</script><style scoped>
.cache-summary {
  margin-bottom: 2rem;
}

.purge-options {
  margin-bottom: 2rem;
}

.deletion-preview {
  margin-bottom: 1rem;
}

.preview-list {
  margin-bottom: 1rem;
}

.preview-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  gap: 1rem;
}

.preview-stats {
  text-align: center;
  padding-top: 1rem;
  border-top: 1px solid var(--el-border-color);
}

.more-items {
  text-align: center;
  margin-top: 0.5rem;
}

/* Ensure dialog inherits dark theme properly */
:deep(.el-dialog) {
  background-color: var(--el-bg-color);
}

:deep(.el-form-item__label) {
  color: var(--el-text-color-primary);
}

:deep(.el-input__wrapper) {
  background-color: var(--el-fill-color);
  border-color: var(--el-border-color);
}

:deep(.el-input__inner) {
  background-color: var(--el-fill-color);
  border-color: var(--el-border-color);
  color: var(--el-text-color-primary);
}

:deep(.el-input-number .el-input__wrapper) {
  background-color: var(--el-fill-color);
}

:deep(.el-input-number .el-input__inner) {
  background-color: var(--el-fill-color);
  color: var(--el-text-color-primary);
}

:deep(.el-checkbox__label) {
  color: var(--el-text-color-primary);
}

:deep(.el-descriptions__label) {
  color: var(--el-text-color-primary);
}

:deep(.el-descriptions__content) {
  color: var(--el-text-color-regular);
}
</style>
