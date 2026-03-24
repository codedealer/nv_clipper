<template>
  <div class="color-controls">
    <el-scrollbar height="100%">
      <div class="color-controls-content">
        <el-tabs v-model="activeTab" type="border-card">
          <el-tab-pane label="Filters" name="basic">
            <div class="control-group">
              <div class="control-label">Brightness</div>
              <el-slider v-model="brightness" :min="-0.5" :max="0.5" :step="0.01" @change="emitFilter" show-input input-size="small" />
            </div>
            <div class="control-group">
              <div class="control-label">Contrast</div>
              <el-slider v-model="contrast" :min="0" :max="3" :step="0.01" @change="emitFilter" show-input input-size="small" />
            </div>
            <div class="control-group">
              <div class="control-label">Saturation</div>
              <el-slider v-model="saturation" :min="0" :max="3" :step="0.01" @change="emitFilter" show-input input-size="small" />
            </div>
            <div class="control-group">
              <div class="control-label">Hue</div>
              <el-slider v-model="hue" :min="-180" :max="180" :step="1" @change="emitFilter" show-input input-size="small" />
            </div>
            <div class="control-group">
              <div class="control-label">Gamma</div>
              <el-slider v-model="gamma" :min="0.1" :max="3" :step="0.01" @change="emitFilter" show-input input-size="small" />
            </div>
          </el-tab-pane>
          <el-tab-pane label="Colors (Lift/Gamma/Gain)" name="advanced">
            <LiftGammaGainWheels
              :wheel-state="advancedWheelState"
              @wheel-state-changed="handleWheelStateChanged"
            />
          </el-tab-pane>
        </el-tabs>

        <div class="filter-output-card">
          <div class="filter-card-header">
            <h6>Generated Filter</h6>
            <div class="filter-header-controls">
              <el-checkbox v-model="previewEnabledLocal" @change="$emit('toggle-preview', previewEnabledLocal)" size="small">Preview</el-checkbox>
            </div>
          </div>
          <div class="filter-display">
            <el-input v-model="generatedFilter" type="textarea" :rows="2" readonly placeholder="Color grading filter will appear here" class="filter-textarea" />
          </div>
          <div class="filter-actions">
            <div class="action-group primary-actions">
              <el-button size="small" type="primary" @click="copyState" plain :disabled="isNeutral">
                <el-icon><DocumentCopy /></el-icon>
                Copy Filter
              </el-button>
              <el-button size="small" @click="pasteFromBuffer" :disabled="!canPaste" plain>
                <el-icon><Document /></el-icon>
                Paste Filter
              </el-button>
            </div>
            <div class="action-group secondary-actions">
              <el-button size="small" type="success" @click="$emit('copy-to-all-clips', gradingState)" :disabled="isNeutral || isMockMarkup" plain v-if="!isMockMarkup">
                <el-icon><CopyDocument /></el-icon>
                Copy to All Clips
              </el-button>
              <el-button size="small" type="warning" @click="reset" plain>
                <el-icon><RefreshLeft /></el-icon>
                Reset
              </el-button>
              <el-button size="small" @click="copyFilterString" :disabled="!generatedFilter || isNeutral" plain>
                <el-icon><DocumentCopy /></el-icon>
                Copy String
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </el-scrollbar>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useClipperStore } from '@/stores/counter'
import { ElMessage } from 'element-plus'
import { DocumentCopy, Document, CopyDocument, RefreshLeft } from '@element-plus/icons-vue'
import LiftGammaGainWheels from './LiftGammaGainWheels.vue'
import { buildFilterFromState } from '@/utils/colorFilterBuild'
import type { ColorGradingState, LggWheelState } from '@/types/colorGrading'
import { createDefaultColorGradingState, cloneColorGradingState } from '@/types/colorGrading'
import { setColorGradingBuffer, getColorGradingBuffer, useColorGradingBufferReactive } from '@/utils/colorGradingBuffer'


interface Props {
  isMockMarkup?: boolean
  previewEnabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isMockMarkup: false,
  previewEnabled: true,
})

// Events now carry structured state; filter string is derived presentation only
const emit = defineEmits<{
  (e: 'filter-changed', clipNumber: number, state: ColorGradingState): void
  (e: 'toggle-preview', enabled: boolean): void
  (e: 'copy-to-all-clips', state: ColorGradingState): void
}>()

const activeTab = ref<'basic' | 'advanced'>('basic')
const gradingState = ref<ColorGradingState>(createDefaultColorGradingState())
const brightness = ref(gradingState.value.basic.brightness)
const contrast = ref(gradingState.value.basic.contrast)
const saturation = ref(gradingState.value.basic.saturation)
const hue = ref(gradingState.value.basic.hue)
const gamma = ref(gradingState.value.basic.gamma)
const advancedWheelState = ref<LggWheelState>(cloneColorGradingState(gradingState.value).lgg)
const previewEnabledLocal = ref<boolean>(props.previewEnabled)

// Build filter only when displaying (commit based). Wheels update internal state continuously, but emission occurs on commit.
const generatedFilter = computed(() => buildFilterFromState(gradingState.value))

// Store reference for clip identity
const clipperStore = useClipperStore()
const { activeSelectedClip } = storeToRefs(clipperStore)

// Commit-based emission: continuous wheel movement updates local state only; emission happens on pointerup/change events from wheel component.
function syncBasicToState() {
  const b = gradingState.value.basic
  b.brightness = brightness.value
  b.contrast = contrast.value
  b.saturation = saturation.value
  b.hue = hue.value
  b.gamma = gamma.value
}
function emitFilter(force = false) {
  const clipNumber = activeSelectedClip.value?.number
  if (clipNumber == null) return
  syncBasicToState()
  if (import.meta.env.DEV) console.log('[ColorControls] emitFilter commit', { clipNumber, state: gradingState.value, force })
  emit('filter-changed', clipNumber, cloneColorGradingState(gradingState.value))
}
const handleWheelStateChanged = (state: LggWheelState) => {
  // Commit from wheel: update state then emit upward once
  advancedWheelState.value = state
  gradingState.value.lgg = cloneColorGradingState({ basic: gradingState.value.basic, lgg: state }).lgg
  emitFilter()
}

const internalResetState = () => {
  gradingState.value = createDefaultColorGradingState()
  const b = gradingState.value.basic
  brightness.value = b.brightness
  contrast.value = b.contrast
  saturation.value = b.saturation
  hue.value = b.hue
  gamma.value = b.gamma
  advancedWheelState.value = cloneColorGradingState(gradingState.value).lgg
}

const reset = () => {
  console.log('[ColorControls] reset() invoked')
  internalResetState()
  emitFilter(true)
}

const copyState = () => {
  setColorGradingBuffer(cloneColorGradingState(gradingState.value))
  ElMessage.success('Filter state copied')
}
const pasteFromBuffer = () => {
  const buf = getColorGradingBuffer()
  if (!buf) return
  gradingState.value = cloneColorGradingState(buf)
  const b = gradingState.value.basic
  brightness.value = b.brightness
  contrast.value = b.contrast
  saturation.value = b.saturation
  hue.value = b.hue
  gamma.value = b.gamma
  advancedWheelState.value = cloneColorGradingState(gradingState.value).lgg
  emitFilter(true)
  ElMessage.success('Filter state pasted')
}
const copyFilterString = async () => {
  try {
    await navigator.clipboard.writeText(generatedFilter.value)
    ElMessage.success('Filter string copied')
  } catch {
    ElMessage.error('Copy failed')
  }
}
const bufferRef = useColorGradingBufferReactive()
const canPaste = computed(() => !!bufferRef.value)

defineExpose({ generatedFilter })

const isMockMarkup = computed(() => props.isMockMarkup)
const isNeutral = computed(() => {
  const b = gradingState.value.basic
  const w = gradingState.value.lgg
  const neutralBasic = b.brightness === 0 && b.contrast === 1 && b.saturation === 1 && b.hue === 0 && b.gamma === 1
  const neutralW = w.lift.hex.toLowerCase() === '#ffffff' && w.lift.sat === 0 && w.lift.amount === 0.5 &&
    w.mid.hex.toLowerCase() === '#ffffff' && w.mid.sat === 0 && w.mid.amount === 0.5 &&
    w.gain.hex.toLowerCase() === '#ffffff' && w.gain.sat === 0 && w.gain.amount === 0.5 &&
    w.globalGamma === 1
  return neutralBasic && neutralW
})

// --- Store-only clip identity watcher to ensure reset on clip switch ---
watch(
  () => activeSelectedClip.value?.number,
  () => {
    const storeState = (activeSelectedClip.value?.overrides as { colorGradingState?: ColorGradingState } | undefined)?.colorGradingState
    if (storeState) {
      gradingState.value = cloneColorGradingState(storeState)
    } else {
      internalResetState()
    }
    const b = gradingState.value.basic
    brightness.value = b.brightness; contrast.value = b.contrast; saturation.value = b.saturation; hue.value = b.hue; gamma.value = b.gamma
    advancedWheelState.value = cloneColorGradingState(gradingState.value).lgg
    // Force sync exactly once on clip switch
    emitFilter(true)
  },
  { immediate: true }
)
</script>

<style scoped>
.color-controls { height: 100%; overflow-y: auto; display: flex; flex-direction: column; gap: 16px; }
.control-group { margin-bottom: 16px; }
.control-label { font-size: 13px; color: var(--el-text-color-regular); margin-bottom: 8px; font-weight: 500; }
.filter-display { border-top: 1px solid var(--el-border-color); padding-top: 16px; }
.filter-output-card { border: 1px solid var(--el-border-color); border-radius: 8px; padding: 16px; background: var(--el-bg-color); margin-top: 16px; }
.filter-card-header { display: flex; justify-content: space-between; align-items: center; }
.filter-card-header h6 { margin: 0; font-size: 11px; font-weight: 400; color: var(--el-text-color-primary); }
.filter-header-controls { display: flex; align-items: center; gap: 8px; }
.filter-textarea { margin-bottom: 16px; }
.filter-textarea :deep(.el-textarea__inner) { font-family: monospace; font-size: 12px; line-height: 1.4; background: var(--el-fill-color-lighter); }
.filter-actions { display: flex; flex-direction: column; gap: 12px; }
.action-group { display: flex; gap: 8px; flex-wrap: wrap; }
.primary-actions .el-button { flex: 1; min-width: 120px; }
.secondary-actions .el-button { flex: 1; min-width: 100px; }
</style>
