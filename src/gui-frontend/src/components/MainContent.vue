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
  <div v-else-if="canShowPanel" class="color-grading-area">
      <ColorGradingPanel
        :key="previewMountKey"
        :selected-clip="selectedClip"
        :video-path="videoFile"
        :video-duration="videoDuration"
        :video-info="videoInfo"
        :is-processing="isProcessing"
        :is-mock-markup="props.isMockMarkup"
        :markup-video-url="markupVideoUrl"
        :get-clip-color-grading="getClipColorGrading"
        :clip-settings-dirty="props.clipSettingsDirty"
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
import { useClipperStore } from '@/stores/counter'
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
  videoDuration?: number | null
  videoInfo?: VideoInfo | null
  isProcessing?: boolean
  isMockMarkup?: boolean
  markupVideoUrl?: string | null
  getClipColorGrading?: (clipNumber: number) => string | undefined
  clipSettingsDirty?: Record<number, boolean>
}

import type { ColorGradingState } from '@/types/colorGrading'
interface Emits {
  (e: 'color-grading-changed', clipNumber: number, filter: string, state: ColorGradingState): void
  (e: 'copy-to-all-clips', state: ColorGradingState): void
}

const props = withDefaults(defineProps<Props>(), {
  videoDuration: null,
  videoInfo: null,
  isProcessing: false,
  isMockMarkup: false,
  markupVideoUrl: null,
  getClipColorGrading: undefined
})

const emit = defineEmits<Emits>()

// Computed properties
const canShowPanel = computed(() => props.clipCount > 0 && (props.hasVideoFile || !!props.markupVideoUrl))

// Remount key from store ensures full reset on any selectedFiles change
const clipperStore = useClipperStore()
const previewMountKey = computed(() => clipperStore.previewMountKey)

const activeColorGradingClip = computed(() => clipperStore.activeColorGradingClip)

const selectedClip = computed(() => {
  const clips = props.parsedClips
  if (!clips.length) return null

  const activeIdx = activeColorGradingClip.value
  if (typeof activeIdx === 'number' && activeIdx >= 0 && activeIdx < clips.length) {
    return clips[activeIdx]
  }

  if (props.selectedClips.length > 0) {
    const idx = props.selectedClips[0]
    if (idx >= 0 && idx < clips.length) return clips[idx]
  }

  return clips[0]
})


function handleColorGradingChanged(clipNumber: number, filter: string, state: ColorGradingState) {
  emit('color-grading-changed', clipNumber, filter, state)
}

function handleCopyToAllClips(state: ColorGradingState) {
  emit('copy-to-all-clips', state)
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
