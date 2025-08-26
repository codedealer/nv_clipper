<template>
  <el-main class="main-content">
    <div v-if="!hasMarkupFile && props.parsedClips.length === 0" class="welcome-area">
      <el-empty
        :image-size="120"
        description="Drop a JSON markup file or video file to get started"
      >
        <template #image>
          <el-icon size="120"><Document /></el-icon>
        </template>
      </el-empty>
    </div>

    <!-- Color Grading Panel (Full Area) -->
    <div v-else-if="hasVideoFile && clipCount > 0" class="color-grading-area">
      <ColorGradingPanel
        :selected-clip="selectedClip"
        :video-path="videoFile"
        :video-duration="videoDuration"
        :video-info="videoInfo"
        :is-processing="isProcessing"
        :is-mock-markup="props.isMockMarkup"
        :get-clip-color-grading="getClipColorGrading"
        @color-grading-changed="handleColorGradingChanged"
        @copy-to-all-clips="handleCopyToAllClips"
      />
    </div>

    <!-- Fallback state -->
    <div v-else class="empty-state">
      <el-empty description="Load a video file and markup to start color grading" />
    </div>
  </el-main>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Document } from '@element-plus/icons-vue'
import ColorGradingPanel from './ColorGradingPanel.vue'
import type { ClipInfo, VideoInfo } from '@/types/api'

interface Props {
  hasMarkupFile: boolean
  hasVideoFile: boolean
  videoFile: string | null
  clipCount: number
  selectedClips: number[]
  parsedClips: ClipInfo[]
  activeColorGradingClip?: number | null
  videoDuration?: number | null
  videoInfo?: VideoInfo | null
  isProcessing?: boolean
  isMockMarkup?: boolean
  getClipColorGrading?: (clipNumber: number) => string | undefined
}

interface Emits {
  (e: 'color-grading-changed', clipNumber: number, filter: string): void
  (e: 'copy-to-all-clips', filter: string): void
}

const props = withDefaults(defineProps<Props>(), {
  videoDuration: null,
  videoInfo: null,
  isProcessing: false,
  isMockMarkup: false,
  getClipColorGrading: undefined
})

const emit = defineEmits<Emits>()

// Computed properties
const selectedClip = computed(() => {
  const clips = props.parsedClips
  if (!clips.length) return null

  // Prefer active color grading clip if valid
  const active = props.activeColorGradingClip
  if (typeof active === 'number' && active >= 0 && active < clips.length) {
    return clips[active]
  }

  // Fallback to first selected clip if available
  if (props.selectedClips.length > 0) {
    const idx = props.selectedClips[0]
    if (idx >= 0 && idx < clips.length) return clips[idx]
  }

  // Final fallback to first clip
  return clips[0]
})

// Methods
function getFileName(path: string): string {
  return path.split(/[\\/]/).pop() || path
}

function handleColorGradingChanged(clipNumber: number, filter: string) {
  emit('color-grading-changed', clipNumber, filter)
}

function handleCopyToAllClips(filter: string) {
  emit('copy-to-all-clips', filter)
}
</script>

<style scoped>
.main-content {
  background: var(--el-bg-color-page);
  padding: 0;
  height: calc(100vh - 60px); /* Full height minus header */
  overflow: hidden;
}

.welcome-area,
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.color-grading-area {
  height: calc(100vh - 60px); /* Full height minus header */
  max-width: 100%;
  overflow: hidden;
}

/* Responsive adjustments */
@media (max-width: 1023px) {
  .color-grading-area {
    max-width: 100%;
  }
}

@media (min-width: 1024px) {
  .color-grading-area {
    max-width: 2000px;
    margin: 0 auto;
  }
}
</style>
