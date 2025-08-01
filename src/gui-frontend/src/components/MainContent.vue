<template>
  <el-main class="main-content">
    <div v-if="!hasMarkupFile" class="welcome-area">
      <el-empty
        :image-size="120"
        description="Drop a JSON markup file to get started"
      >
        <template #image>
          <el-icon size="120"><Document /></el-icon>
        </template>
      </el-empty>
    </div>

    <div v-else class="content-area">
      <!-- Video Preview Area -->
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
          <p class="preview-filename">{{ getFileName(videoFile || '') }}</p>
        </div>
      </el-card>

      <!-- Timeline Area -->
      <el-card v-if="clipCount > 0" class="timeline-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <el-icon><Timer /></el-icon>
            <span>Timeline</span>
          </div>
        </template>

        <div class="timeline-placeholder">
          <el-icon size="60"><Timer /></el-icon>
          <p>Timeline view coming soon...</p>
          <p>{{ clipCount }} clips loaded</p>
        </div>
      </el-card>
    </div>
  </el-main>
</template>

<script setup lang="ts">
import {
  Document,
  Monitor,
  VideoCamera,
  Timer
} from '@element-plus/icons-vue'

interface Props {
  hasMarkupFile: boolean
  hasVideoFile: boolean
  videoFile: string | null
  clipCount: number
}

defineProps<Props>()

// Methods
function getFileName(path: string): string {
  return path.split(/[\\/]/).pop() || path
}
</script>

<style scoped>
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

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
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
</style>
