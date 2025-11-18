<template>
  <div v-if="props.selectedClip" class="clip-settings-panel">
    <div class="panel-header">
      <h4 class="panel-title">{{ clipHeading }}</h4>
      <el-tag v-if="isDirty" type="warning" size="small" effect="light">Modified</el-tag>
    </div>

    <div class="panel-scroll">
      <el-form label-position="top" size="small" class="clip-settings-form">
        <section class="form-section">
          <h5 class="section-title">Playback</h5>
          <el-row :gutter="8" class="playback-grid">
            <el-col :xs="24" :sm="12">
              <el-form-item label="Speed">
                <div class="form-item-row">
                  <el-input-number
                    v-model="form.speed"
                    :min="0.05"
                    :step="0.05"
                    :precision="3"
                    controls-position="right"
                    class="compact-number"
                    @change="handleSpeedChange"
                  />
                  <el-button text type="primary" size="small" :disabled="!canResetSpeed" @click="resetSpeed">Reset</el-button>
                </div>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12">
              <el-form-item label="Loop">
                <el-select v-model="form.loop" placeholder="Inherit" clearable @change="handleLoopChange">
                  <el-option label="Forward Only" value="none" />
                  <el-option label="Forward + Reverse" value="fwrev" />
                  <el-option label="Fade Loop" value="fade" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12">
              <el-form-item label="Interpolation Mode">
                <el-select
                  v-model="form.minterpMode"
                  @change="handleMinterpModeChange"
                >
                  <el-option v-for="mode in minterpModes" :key="mode" :label="mode" :value="mode" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12">
              <el-form-item label="Interpolation Provider">
                <el-select
                  v-model="form.minterpProvider"
                  placeholder="Inherit"
                  clearable
                  filterable
                  allow-create
                  @change="handleMinterpProviderChange"
                >
                  <el-option v-for="provider in minterpProviders" :key="provider" :label="provider" :value="provider" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12">
              <el-form-item label="Mirror Video">
                <el-switch
                  v-model="form.mirror"
                  inline-prompt
                  :active-text="'On'"
                  :inactive-text="'Off'"
                  @change="handleMirrorChange"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </section>

        <section class="form-section">
          <div class="section-header">
            <h5 class="section-title">Video Stabilization</h5>
            <el-tag v-if="stabilizationPresetLabel" size="small" effect="plain">{{ stabilizationPresetLabel }}</el-tag>
          </div>
          <el-row :gutter="8" class="stabilization-grid">
            <el-col :xs="24" :sm="12">
              <el-form-item label="Preset">
                <el-select
                  v-model="form.videoStabilizationPreset"
                  @change="handleVideoStabilizationPresetChange"
                >
                  <el-option
                    v-for="preset in videoStabilizationPresets"
                    :key="preset.value"
                    :label="preset.label"
                    :value="preset.value"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="6">
              <el-form-item label="Rolling Shutter">
                <el-switch
                  v-model="form.videoStabilizationRollingShutter"
                  inline-prompt
                  :active-text="'On'"
                  :inactive-text="'Off'"
                  :disabled="!hasActiveStabilizationPreset"
                  @change="handleVideoStabilizationFlagChange('videoStabilizationRollingShutter', $event)"
                />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="6">
              <el-form-item label="Jittery Motion">
                <el-switch
                  v-model="form.videoStabilizationJitteryMotion"
                  inline-prompt
                  :active-text="'On'"
                  :inactive-text="'Off'"
                  :disabled="!hasActiveStabilizationPreset"
                  @change="handleVideoStabilizationFlagChange('videoStabilizationJitteryMotion', $event)"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </section>

        <section class="form-section">
          <h5 class="section-title">Video Enhancement</h5>
          <el-row :gutter="8">
            <el-col :xs="24" :sm="12">
              <el-form-item label="Enhancement Enabled">
                <el-switch
                  v-model="form.videoEnhancementEnabled"
                  inline-prompt
                  :active-text="'On'"
                  :inactive-text="'Off'"
                  @change="commitVideoEnhancement"
                />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12">
              <el-form-item label="Model">
                <el-select
                  v-model="form.videoEnhancementModel"
                  placeholder="Inherit"
                  clearable
                  :disabled="!form.videoEnhancementEnabled"
                  @change="commitVideoEnhancement"
                >
                  <el-option v-for="model in videoEnhancementModels" :key="model" :label="model" :value="model" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="8" class="enhancement-grid">
            <el-col v-for="field in videoEnhancementNumericFields" :key="field.key" :xs="24" :sm="12" :lg="12">
              <el-form-item :label="field.label">
                <el-input-number
                  v-model="form[field.key]"
                  :min="field.min"
                  :max="field.max"
                  :step="field.step"
                  controls-position="right"
                  class="compact-number"
                  :disabled="!form.videoEnhancementEnabled"
                  @change="handleVideoEnhancementNumberChange(field.key, $event)"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </section>
      </el-form>
    </div>

    <div class="panel-footer">
      <el-button size="small" :disabled="!isDirty" @click="handleReset">Reset to markup</el-button>
    </div>
  </div>
  <div v-else class="no-selection">
    <el-empty description="Select a clip to edit settings" />
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import type { ClipInfo } from '@/types/api'
import { useMarkupOperations } from '@/composables/useMarkupOperations'
import type {
  ClipSettingsOverrides,
  ClipSettingsState,
  LoopOption,
  VideoEnhancementModel,
  VideoStabilizationOverride
} from '@/types/clipSettings'

interface Props {
  selectedClip?: ClipInfo | null
  isDirty?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  selectedClip: null,
  isDirty: false
})

const minterpProviders = ['RIFE', 'TopazCHF', 'TopazApollo', 'TopazAion']
const minterpModes = ['None', 'VideoFPS', 'x2slow', 'x4slow', 'x6slow', 'x8slow'] as const
type MinterpModeOption = typeof minterpModes[number]

interface FormState {
  speed: number | null
  loop: LoopOption | null
  minterpMode: MinterpModeOption
  minterpProvider: string | null
  mirror: boolean
  videoStabilizationPreset: number
  videoStabilizationRollingShutter: boolean
  videoStabilizationJitteryMotion: boolean
  videoEnhancementEnabled: boolean
  videoEnhancementModel: VideoEnhancementModel | null
  videoEnhancementCompression: number | null
  videoEnhancementDetails: number | null
  videoEnhancementBlur: number | null
  videoEnhancementNoise: number | null
  videoEnhancementHalo: number | null
  videoEnhancementPreblur: number | null
  videoEnhancementBlend: number | null
  videoEnhancementPrenoise: number | null
}

interface VideoStabilizationPreset {
  value: number
  label: string
  config?: VideoStabilizationOverride & { zoomspeed?: number }
}

const markupOps = useMarkupOperations()

const videoStabilizationPresets: VideoStabilizationPreset[] = [
  { value: 0, label: 'Disabled' },
  { value: 1, label: 'Very Weak', config: { enabled: true, shakiness: 2, smoothing: 1, desc: 'Very Weak', zoomspeed: 0.05 } },
  { value: 2, label: 'Weak', config: { enabled: true, shakiness: 4, smoothing: 3, desc: 'Weak', zoomspeed: 0.1 } },
  { value: 3, label: 'Medium', config: { enabled: true, shakiness: 6, smoothing: 6, desc: 'Medium', zoomspeed: 0.2 } },
  { value: 4, label: 'Strong', config: { enabled: true, shakiness: 8, smoothing: 9, desc: 'Strong', zoomspeed: 0.3 } },
  { value: 5, label: 'Very Strong', config: { enabled: true, shakiness: 10, smoothing: 12, desc: 'Very Strong', zoomspeed: 0.4 } }
]

const videoEnhancementModels: VideoEnhancementModel[] = ['Proteus', 'Iris']

const videoEnhancementNumericFields = [
  { key: 'videoEnhancementCompression', label: 'Fix Compression', min: 0, max: 1, step: 0.05 },
  { key: 'videoEnhancementDetails', label: 'Improve Detail', min: 0, max: 1, step: 0.05 },
  { key: 'videoEnhancementBlur', label: 'Sharpen', min: 0, max: 1, step: 0.05 },
  { key: 'videoEnhancementNoise', label: 'Reduce Noise', min: 0, max: 1, step: 0.05 },
  { key: 'videoEnhancementHalo', label: 'Dehalo', min: 0, max: 1, step: 0.05 },
  { key: 'videoEnhancementPreblur', label: 'Anti-alias/Deblur', min: -1, max: 1, step: 0.1 },
  { key: 'videoEnhancementBlend', label: 'Recover detail', min: 0, max: 1, step: 0.05 },
  { key: 'videoEnhancementPrenoise', label: 'Add Noise', min: 0, max: 1, step: 0.05 }
] as const

type VideoEnhancementFieldKey = typeof videoEnhancementNumericFields[number]['key']
type VideoStabilizationFlagField = 'videoStabilizationRollingShutter' | 'videoStabilizationJitteryMotion'

const form = reactive<FormState>({
  speed: null,
  loop: null,
  minterpMode: 'None',
  minterpProvider: null,
  mirror: false,
  videoStabilizationPreset: 0,
  videoStabilizationRollingShutter: false,
  videoStabilizationJitteryMotion: false,
  videoEnhancementEnabled: false,
  videoEnhancementModel: null,
  videoEnhancementCompression: null,
  videoEnhancementDetails: null,
  videoEnhancementBlur: null,
  videoEnhancementNoise: null,
  videoEnhancementHalo: null,
  videoEnhancementPreblur: null,
  videoEnhancementBlend: null,
  videoEnhancementPrenoise: null
})

const clipNumber = computed(() => props.selectedClip?.number ?? null)

const currentSettings = computed(() => {
  if (clipNumber.value === null) return null
  return markupOps.getClipSettingsState(clipNumber.value)
})

const originalSettings = computed(() => {
  if (clipNumber.value === null) return null
  return markupOps.getOriginalClipSettingsState(clipNumber.value)
})

const isDirty = computed(() => Boolean(props.isDirty))

const clipHeading = computed(() => {
  if (!props.selectedClip) return 'No clip selected'
  const number = props.selectedClip.number ? `Clip ${props.selectedClip.number}` : 'Clip'
  return props.selectedClip.title ? `${number}: ${props.selectedClip.title}` : number
})

const stabilizationPresetLabel = computed(() => {
  const preset = videoStabilizationPresets.find(p => p.value === form.videoStabilizationPreset)
  return preset && preset.value !== 0 ? preset.label : null
})

const hasActiveStabilizationPreset = computed(() => form.videoStabilizationPreset !== 0)

function resetForm() {
  form.speed = props.selectedClip?.speed ?? null
  form.loop = null
  form.minterpMode = 'None'
  form.minterpProvider = null
  form.mirror = false
  form.videoStabilizationPreset = 0
  form.videoStabilizationRollingShutter = false
  form.videoStabilizationJitteryMotion = false
  form.videoEnhancementEnabled = false
  form.videoEnhancementModel = null
  form.videoEnhancementCompression = null
  form.videoEnhancementDetails = null
  form.videoEnhancementBlur = null
  form.videoEnhancementNoise = null
  form.videoEnhancementHalo = null
  form.videoEnhancementPreblur = null
  form.videoEnhancementBlend = null
  form.videoEnhancementPrenoise = null
}

function findPresetValueFromConfig(config?: VideoStabilizationOverride | null): number {
  if (!config || !config.enabled) return 0
  const match = videoStabilizationPresets.find(p => {
    if (!p.config) return false
    return p.config.shakiness === config.shakiness && p.config.smoothing === config.smoothing
  })
  return match ? match.value : 1
}

function normalizeMinterpMode(raw: unknown): MinterpModeOption {
  if (raw === false || raw === undefined || raw === null) return 'None'
  if (typeof raw === 'string' && (minterpModes as readonly string[]).includes(raw)) {
    return raw as MinterpModeOption
  }
  return 'None'
}

function applySettings(settings: ClipSettingsState | null) {
  resetForm()
  if (!settings) return
  form.speed = settings.speed ?? form.speed
  const effective = settings.effectiveOverrides || {}
  form.loop = (effective.loop as LoopOption | undefined) ?? null
  form.minterpMode = normalizeMinterpMode(effective.minterpMode)
  form.minterpProvider = (effective.minterpProvider as string | undefined) ?? null
  form.mirror = effective.mirror ?? false

  const presetValue = findPresetValueFromConfig(effective.videoStabilization as VideoStabilizationOverride | undefined)
  form.videoStabilizationPreset = presetValue
  form.videoStabilizationRollingShutter = effective.videoStabilizationRollingShutter ?? false
  form.videoStabilizationJitteryMotion = effective.videoStabilizationJitteryMotion ?? false

  form.videoEnhancementEnabled = effective.videoEnhancementEnabled ?? false
  form.videoEnhancementModel = (effective.videoEnhancementModel as VideoEnhancementModel | undefined) ?? null
  form.videoEnhancementCompression = typeof effective.videoEnhancementCompression === 'number' ? effective.videoEnhancementCompression : 0
  form.videoEnhancementDetails = typeof effective.videoEnhancementDetails === 'number' ? effective.videoEnhancementDetails : 0
  form.videoEnhancementBlur = typeof effective.videoEnhancementBlur === 'number' ? effective.videoEnhancementBlur : 0
  form.videoEnhancementNoise = typeof effective.videoEnhancementNoise === 'number' ? effective.videoEnhancementNoise : 0
  form.videoEnhancementHalo = typeof effective.videoEnhancementHalo === 'number' ? effective.videoEnhancementHalo : 0
  form.videoEnhancementPreblur = typeof effective.videoEnhancementPreblur === 'number' ? effective.videoEnhancementPreblur : 0
  form.videoEnhancementBlend = typeof effective.videoEnhancementBlend === 'number' ? effective.videoEnhancementBlend : 0
  form.videoEnhancementPrenoise = typeof effective.videoEnhancementPrenoise === 'number' ? effective.videoEnhancementPrenoise : 0
}

watch(currentSettings, (settings) => {
  applySettings(settings)
}, { immediate: true })

watch(() => props.selectedClip?.number, (newNumber) => {
  if (newNumber === null || newNumber === undefined) {
    resetForm()
    return
  }
  const nextSettings = markupOps.getClipSettingsState(newNumber)
  applySettings(nextSettings)
})

const canResetSpeed = computed(() => {
  if (!props.selectedClip || !originalSettings.value) return false
  return Math.abs((originalSettings.value.speed ?? 0) - (form.speed ?? originalSettings.value.speed ?? 0)) > 1e-6
})

function ensureClip(): number | null {
  const number = clipNumber.value
  if (number === null) return null
  return number
}

function handleSpeedChange(value: number | null) {
  const number = ensureClip()
  if (number === null) return
  markupOps.updateClipSettings(number, { speed: value ?? null })
}

function resetSpeed() {
  const number = ensureClip()
  if (number === null) return
  markupOps.updateClipSettings(number, { speed: null })
}

function handleLoopChange(value: LoopOption | undefined) {
  const number = ensureClip()
  if (number === null) return
  markupOps.updateClipSettings(number, { overrides: { loop: value } })
}

function handleMinterpModeChange(value: MinterpModeOption) {
  const number = ensureClip()
  if (number === null) return
  const resolved = value === 'None' ? false : value
  markupOps.updateClipSettings(number, { overrides: { minterpMode: resolved } })
}

function handleMinterpProviderChange(value: string | undefined) {
  const number = ensureClip()
  if (number === null) return
  const resolved = value && value.trim().length ? value.trim() : undefined
  markupOps.updateClipSettings(number, { overrides: { minterpProvider: resolved } })
}

function handleMirrorChange(value: boolean) {
  const number = ensureClip()
  if (number === null) return
  markupOps.updateClipSettings(number, { overrides: { mirror: value } })
}

function commitVideoStabilization(applyFlags = true) {
  const number = ensureClip()
  if (number === null) return
  const preset = videoStabilizationPresets.find(p => p.value === form.videoStabilizationPreset)
  const overrides: Partial<ClipSettingsOverrides> = {}

  if (!preset || preset.value === 0) {
    overrides.videoStabilization = undefined
    overrides.videoStabilizationRollingShutter = undefined
    overrides.videoStabilizationJitteryMotion = undefined
    overrides.videoStabilizationDynamicZoom = undefined
    if (applyFlags) {
      form.videoStabilizationRollingShutter = false
      form.videoStabilizationJitteryMotion = false
    }
  } else if (preset.config) {
    overrides.videoStabilization = { ...preset.config }
    overrides.videoStabilizationRollingShutter = form.videoStabilizationRollingShutter
    overrides.videoStabilizationJitteryMotion = form.videoStabilizationJitteryMotion
    overrides.videoStabilizationDynamicZoom = undefined
  }

  markupOps.updateClipSettings(number, { overrides })
}

function handleVideoStabilizationPresetChange() {
  if (!hasActiveStabilizationPreset.value) {
    commitVideoStabilization()
    return
  }
  commitVideoStabilization(false)
}

function handleVideoStabilizationFlagChange(field: VideoStabilizationFlagField, value: boolean) {
  if (!hasActiveStabilizationPreset.value) {
    form[field] = false
    return
  }
  form[field] = value
  commitVideoStabilization(false)
}

function handleVideoEnhancementNumberChange(field: VideoEnhancementFieldKey, value: number | null | undefined) {
  form[field] = typeof value === 'number' ? value : null
  commitVideoEnhancement()
}

function buildVideoEnhancementOverrides(): Partial<ClipSettingsOverrides> {
  const overrides: Partial<ClipSettingsOverrides> = {
    videoEnhancementEnabled: form.videoEnhancementEnabled
  }
  overrides.videoEnhancementModel = form.videoEnhancementModel ?? undefined
  overrides.videoEnhancementCompression = form.videoEnhancementCompression ?? undefined
  overrides.videoEnhancementDetails = form.videoEnhancementDetails ?? undefined
  overrides.videoEnhancementBlur = form.videoEnhancementBlur ?? undefined
  overrides.videoEnhancementNoise = form.videoEnhancementNoise ?? undefined
  overrides.videoEnhancementHalo = form.videoEnhancementHalo ?? undefined
  overrides.videoEnhancementPreblur = form.videoEnhancementPreblur ?? undefined
  overrides.videoEnhancementBlend = form.videoEnhancementBlend ?? undefined
  overrides.videoEnhancementPrenoise = form.videoEnhancementPrenoise ?? undefined
  return overrides
}

function commitVideoEnhancement() {
  const number = ensureClip()
  if (number === null) return
  const overrides = buildVideoEnhancementOverrides()
  markupOps.updateClipSettings(number, { overrides })
}

function handleReset() {
  const number = ensureClip()
  if (number === null) return
  markupOps.resetClipSettings(number)
  applySettings(originalSettings.value)
}
</script>

<style scoped>
.clip-settings-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  gap: 8px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.panel-title {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
}

.panel-scroll {
  flex: 1;
  min-height: 0;
  padding-right: 6px;
  overflow-y: auto;
}

.clip-settings-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 10px;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  background: var(--el-bg-color-overlay);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.section-title {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
}

.form-item-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.compact-number {
  width: 120px;
}

.panel-footer {
  display: flex;
  justify-content: flex-end;
  flex-shrink: 0;
}

.no-selection {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 16px;
}

.playback-grid :deep(.el-form-item) {
  margin-bottom: 0;
}

.enhancement-grid :deep(.el-form-item) {
  margin-bottom: 0;
}

.stabilization-grid :deep(.el-form-item) {
  margin-bottom: 0;
}

:deep(.el-form-item) {
  margin-bottom: 0;
}

:deep(.el-form-item__label) {
  padding-bottom: 2px;
}
</style>
