<template>
  <el-card v-if="clips.length > 0" class="section-card">
    <div class="clips-toolbar">
      <div class="clips-title">
        <el-icon class="clips-icon"><VideoPlay /></el-icon>
        <span>Clips ({{ selectedClips.length }}/{{ clips.length }})</span>
      </div>
      <el-checkbox
        v-model="selectAllClips"
        @change="handleSelectAllClips"
        :indeterminate="isIndeterminate"
        class="select-all"
      >
        Select All
      </el-checkbox>
    </div>

    <div class="clip-selection">
      <el-checkbox-group v-model="selectedClips" size="small">
        <div
          v-for="(clip, index) in clips"
          :key="index"
          class="clip-item"
          :class="{ 'active-color-grading': activeColorGradingClip === index, modified: isClipModified(clip, index) }"
        >
          <el-checkbox :value="index" />
          <div class="clip-info" @click="handleClipClick(index)">
            <div class="clip-info-row">
              <div class="clip-duration">{{ `${clip.number || index + 1} - ${formatDuration(clip)}` }}</div>
              <el-tag v-if="isClipModified(clip, index)" type="warning" size="small" effect="plain" class="clip-modified-tag">Modified</el-tag>
            </div>
          </div>
        </div>
      </el-checkbox-group>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { VideoPlay } from '@element-plus/icons-vue'

interface Clip {
  title?: string
  number?: number
  start: number
  end: number
  duration?: number
  speed?: number
  crop?: string
  enableZoomPan?: boolean
  overrides?: Record<string, unknown>
}

interface Props {
  clips: Clip[]
  modelValue: number[]
  activeColorGradingClip?: number | null
  clipSettingsDirty?: Record<number, boolean>
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: number[]]
  'clip-selected-for-color-grading': [clipIndex: number]
}>()

// Local state
const selectAllClips = ref(true)

// Computed
const selectedClips = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const isIndeterminate = computed(() =>
  selectedClips.value.length > 0 && selectedClips.value.length < props.clips.length
)

// Watch for changes in clips to update selection
watch(() => props.clips, (newClips) => {
  if (newClips.length > 0 && selectedClips.value.length === 0) {
    // Auto-select all clips when clips are loaded
    selectedClips.value = Array.from({ length: newClips.length }, (_, i) => i)
    selectAllClips.value = true
  }
}, { immediate: true })

// Watch for changes in selected clips to update select all state
watch(selectedClips, (newSelection) => {
  if (newSelection.length === props.clips.length) {
    selectAllClips.value = true
  } else if (newSelection.length === 0) {
    selectAllClips.value = false
  }
}, { deep: true })

const INTERPOLATION_DURATION_FACTORS: Record<string, number> = {
  None: 1,
  VideoFPS: 1,
  x2slow: 2,
  x4slow: 4,
  x6slow: 6,
  x8slow: 8
}

function getInterpolationFactor(clip: Clip): number {
  const raw = clip.overrides?.minterpMode as string | boolean | undefined
  if (raw === false || raw === undefined || raw === null) {
    return 1
  }
  if (typeof raw === 'string') {
    return INTERPOLATION_DURATION_FACTORS[raw] ?? 1
  }
  return 1
}

function getProjectedDuration(clip: Clip, baseDuration: number): number {
  const speedMultiplier = clip.speed && clip.speed > 0 ? clip.speed : 1
  const interpolationFactor = getInterpolationFactor(clip)
  const rawProjected = baseDuration * interpolationFactor
  return rawProjected / (speedMultiplier || 1)
}

function getEffectiveSpeed(clip: Clip): number {
  const speedMultiplier = clip.speed && clip.speed > 0 ? clip.speed : 1
  const interpolationFactor = getInterpolationFactor(clip)
  const effective = speedMultiplier / (interpolationFactor || 1)
  return effective > 0 ? effective : 1
}

// Methods
function handleSelectAllClips(value: boolean) {
  if (value) {
    selectedClips.value = Array.from({ length: props.clips.length }, (_, i) => i)
  } else {
    selectedClips.value = []
  }
}

function formatDuration(clip: Clip): string {
  if (typeof clip.start === 'number' && typeof clip.end === 'number') {
    const baseDuration = typeof clip.duration === 'number'
      ? clip.duration
      : Math.max(clip.end - clip.start, 0)
    const projectedDuration = getProjectedDuration(clip, baseDuration)
    const durationChanged = Math.abs(projectedDuration - baseDuration) > 1e-2
    const effectiveSpeed = getEffectiveSpeed(clip)
    const speedChanged = Math.abs(effectiveSpeed - 1) > 1e-3
    const range = `${formatTime(clip.start)} - ${formatTime(clip.end)}`
    const baseText = formatTime(baseDuration)
    const speedText = speedChanged ? ` @ ${effectiveSpeed.toFixed(2)}x` : ''
    if (!durationChanged) {
      return `${range} (${baseText})${speedText}`
    }
    const projectedText = formatTime(projectedDuration)
    return `${range} (${projectedText})${speedText}`
  }
  if (clip.start && clip.end) {
    return `${clip.start} - ${clip.end}`
  }
  return 'Duration unknown'
}

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = (seconds % 60).toFixed(2)
  return `${mins}:${secs.padStart(5, '0')}`
}

function handleClipClick(index: number) {
  // Emit event to notify parent that this clip was selected for color grading
  emit('clip-selected-for-color-grading', index)
}

function isClipModified(clip: Clip, index: number): boolean {
  const clipNumber = clip.number ?? index + 1
  return Boolean(props.clipSettingsDirty?.[clipNumber])
}
</script>

<style scoped>
.section-card {
  margin-bottom: 0;
  border-radius: 0;
  border: none;
  box-shadow: none;
}

.clips-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.clips-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.clips-icon {
  display: inline-flex;
}

.select-all :deep(.el-checkbox__label) {
  font-weight: 500;
}

.clip-item {
  display: flex;
  align-items: center;
  padding: 6px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  border-radius: 4px;
  margin-bottom: 2px;
  transition: background-color 0.2s;
}

.clip-item:hover {
  background-color: var(--el-fill-color-light);
}

.clip-item.active-color-grading {
  background-color: var(--el-color-primary-light-9);
  border: 1px solid var(--el-color-primary-light-7);
}

.clip-item.modified:not(.active-color-grading) {
  border: 1px solid var(--el-color-warning-light-7);
  background-color: var(--el-color-warning-light-9);
}

.clip-item:last-child {
  border-bottom: none;
}

.clip-info {
  flex: 1;
  margin-left: 6px;
  cursor: pointer;
  padding: 2px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.clip-info:hover {
  background-color: var(--el-fill-color-lighter);
}

.clip-info-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.clip-duration {
  font-size: 12px;
  line-height: normal;
  color: var(--el-text-color-secondary);
}

.clip-modified-tag {
  flex-shrink: 0;
}
</style>
