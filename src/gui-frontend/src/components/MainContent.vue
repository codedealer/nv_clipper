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
      <el-container direction="horizontal" style="height: 100%;">
        <!-- Main Content Area (Video Preview & Timeline) -->
        <el-main class="central-content">
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
        </el-main>

        <!-- Right Sidebar: Color Grading Panel -->
        <el-aside width="520px" class="color-grading-sidebar" v-if="hasVideoFile && clipCount > 0">
          <div class="sidebar-content">
            <ColorGradingPanel
              :selected-clip="selectedClip"
              :video-path="videoFile"
              :is-processing="isProcessing"
              @color-grading-changed="handleColorGradingChanged"
            />
          </div>
        </el-aside>
      </el-container>
    </div>
  </el-main>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  Document,
  Monitor,
  VideoCamera,
  Timer
} from '@element-plus/icons-vue'
import ColorGradingPanel from './ColorGradingPanel.vue'
import type { ClipInfo } from '@/types/api'

interface Props {
  hasMarkupFile: boolean
  hasVideoFile: boolean
  videoFile: string | null
  clipCount: number
  selectedClips: number[]
  parsedClips: ClipInfo[]
  isProcessing?: boolean
}

interface Emits {
  (e: 'color-grading-changed', clipNumber: number, filter: string): void
}

const props = withDefaults(defineProps<Props>(), {
  isProcessing: false
})

const emit = defineEmits<Emits>()

// Computed properties
const selectedClip = computed(() => {
  if (!props.parsedClips.length || !props.selectedClips.length) return null

  // For now, use the first selected clip
  const selectedIndex = props.selectedClips[0]
  return props.parsedClips[selectedIndex] || null
})

// Methods
function getFileName(path: string): string {
  return path.split(/[\\/]/).pop() || path
}

function handleColorGradingChanged(clipNumber: number, filter: string) {
  emit('color-grading-changed', clipNumber, filter)
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
}

.central-content {
  padding-right: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.color-grading-sidebar {
  border-left: 1px solid var(--el-border-color);
  background: var(--el-bg-color);
}

.sidebar-content {
  padding: 16px;
  height: 100%;
  overflow-y: auto;
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
