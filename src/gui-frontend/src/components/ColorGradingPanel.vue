<template>
  <div class="color-grading-panel">
    <div class="panel-content">
      <div class="color-grading-content">
          <!-- Left Column: Preview + Timeline -->
          <ColorPreview
            :video-path="props.videoPath"
            :video-duration="props.videoDuration"
            :video-info="props.videoInfo"
            :markup-video-url="props.markupVideoUrl"
            :filter="generatedFilter"
            :preview-enabled="previewEnabled"
            :selected-clip="props.selectedClip"
          />

          <!-- Color Controls -->
          <ColorControls
            :is-mock-markup="props.isMockMarkup"
            :preview-enabled="previewEnabled"
            @filter-changed="onFilterChanged"
            @toggle-preview="onTogglePreview"
            @copy-to-all-clips="(s:ColorGradingState)=>emit('copy-to-all-clips', s)"
          />
        </div>
      </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { buildFilterFromState } from '@/utils/colorFilterBuild'
import type { ColorGradingState } from '@/types/colorGrading'
import type { ClipInfo, VideoInfo } from '@/types/api'
import ColorPreview from './ColorPreview.vue'
import ColorControls from './ColorControls.vue'

interface Props {
  selectedClip?: ClipInfo | null
  videoPath?: string | null
  videoDuration?: number | null
  videoInfo?: VideoInfo | null
  isProcessing?: boolean
  isMockMarkup?: boolean
  markupVideoUrl?: string | null
  getClipColorGrading?: (clipNumber: number) => string | undefined
}

interface Emits {
  (e: 'color-grading-changed', clipNumber: number, filter: string, state: ColorGradingState): void
  (e: 'copy-to-all-clips', state: ColorGradingState): void
}

const props = withDefaults(defineProps<Props>(), {
  selectedClip: null,
  videoPath: null,
  videoDuration: null,
  videoInfo: null,
  isProcessing: false,
  isMockMarkup: false,
  markupVideoUrl: null,
  getClipColorGrading: undefined
})

const emit = defineEmits<Emits>()

// State
const previewEnabled = ref(true)

// Sync initial preview enabled from child prop if provided (optional future extensibility)

// Computed properties
// const hasVideo = computed(() => !!props.videoPath)
// Keep a generated filter for passing to preview, but filter is owned by ColorControls
const generatedFilter = ref('')
const onFilterChanged = (clipNumber: number, state: ColorGradingState) => {
  const filter = buildFilterFromState(state)
  generatedFilter.value = filter
  emit('color-grading-changed', clipNumber, filter, state)
}

const onTogglePreview = (enabled: boolean) => {
  previewEnabled.value = enabled
}

// filterForClip no longer needed: ColorControls reads directly from store
</script>

<style scoped>
.color-grading-panel {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  margin: 0 auto;
}

.panel-content {
  padding: 16px;
  height: 100%;
  min-height: 0;
}

/* Responsive layout for larger screens */
@media (min-width: 1024px) {
  .color-grading-content {
    display: grid;
    grid-template-columns: 1fr 300px;
    gap: 20px;
    height: 100%;
  }

  .preview-timeline-column {
    display: flex;
    flex-direction: column;
    gap: 16px;
    height: 100%;
    min-height: 0;
    overflow: hidden;
  }

  .preview-section {
    flex: 1;
    min-height: 0;
    overflow: hidden;
  }

  .preview-container {
    height: 100%;
  }

  .timeline-section {
    flex-shrink: 0;
    max-height: 120px;
  }

  .color-controls {
    height: 100%;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
}

.no-content {
  text-align: center;
  padding: 40px 20px;
  color: var(--el-text-color-secondary);
}

.controls-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.copy-paste-controls {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}
</style>
