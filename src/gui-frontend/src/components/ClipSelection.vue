<template>
  <el-card v-if="clips.length > 0" class="section-card" shadow="hover">
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
        style="margin-bottom: 12px;"
      >
        Select All
      </el-checkbox>

      <el-scrollbar max-height="300px">
        <el-checkbox-group v-model="selectedClips" size="small">
          <div
            v-for="(clip, index) in clips"
            :key="index"
            class="clip-item"
          >
            <el-checkbox :value="index">
              <div class="clip-info">
                <div class="clip-title">{{ clip.title || `Clip ${clip.number || index + 1}` }}</div>
                <div class="clip-duration">{{ formatDuration(clip) }}</div>
              </div>
            </el-checkbox>
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
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: number[]]
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
</script>

<style scoped>
.section-card {
  margin-bottom: 16px;
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
  padding: 8px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.clip-item:last-child {
  border-bottom: none;
}

.clip-info {
  flex: 1;
  margin-left: 8px;
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
