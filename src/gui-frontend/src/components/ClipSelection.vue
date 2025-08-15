<template>
  <el-card v-if="clips.length > 0" class="section-card">
    <template #header>
      <div class="card-header">
        <el-icon><VideoPlay /></el-icon>
        <span>Clips ({{ selectedClips.length }}/{{ clips.length }})</span>
      </div>
    </template>

    <div class="clip-selection">
      <el-checkbox
        v-model="selectAllClips"
        @change="handleSelectAllClips"
        :indeterminate="isIndeterminate"
        style="margin-bottom: 8px;"
      >
        Select All
      </el-checkbox>

      <el-scrollbar max-height="300px">
        <el-checkbox-group v-model="selectedClips" size="small">
          <div
            v-for="(clip, index) in clips"
            :key="index"
            class="clip-item"
            :class="{ 'active-color-grading': activeColorGradingClip === index }"
          >
            <el-checkbox
              :value="index"
              @click.stop
              @change="(checked: boolean) => handleCheckboxChange(index, checked)"
            />
            <div class="clip-info" @click="handleClipClick(index)">
              <div class="clip-title">
                {{ clip.title || `Clip ${clip.number || index + 1}` }}
              </div>
              <div class="clip-duration">{{ formatDuration(clip) }}</div>
            </div>
          </div>
        </el-checkbox-group>
      </el-scrollbar>
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

// Methods
function handleSelectAllClips(value: boolean) {
  if (value) {
    selectedClips.value = Array.from({ length: props.clips.length }, (_, i) => i)
  } else {
    selectedClips.value = []
  }
}

function handleCheckboxChange(index: number, checked: boolean) {
  // Handle individual checkbox selection for processing
  const currentSelection = [...selectedClips.value]
  if (checked) {
    if (!currentSelection.includes(index)) {
      currentSelection.push(index)
    }
  } else {
    const indexPos = currentSelection.indexOf(index)
    if (indexPos !== -1) {
      currentSelection.splice(indexPos, 1)
    }
  }
  selectedClips.value = currentSelection
}

function formatDuration(clip: Clip): string {
  if (typeof clip.start === 'number' && typeof clip.end === 'number') {
    const duration = clip.end - clip.start
    return `${formatTime(clip.start)} - ${formatTime(clip.end)} (${formatTime(duration)})`
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
</script>

<style scoped>
.section-card {
  margin-bottom: 0;
  border-radius: 0;
  border: none;
  box-shadow: none;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.clip-selection {
  max-height: 250px;
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

.clip-title {
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.clip-duration {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
</style>
