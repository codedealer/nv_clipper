<template>
  <div class="header-content">
    <div class="header-controls">
      <el-button-group>
        <el-button @click="$emit('open-video-cache')" :icon="Coin">
          Video Cache
        </el-button>
        <el-button @click="$emit('open-settings')" :icon="Setting">
          Settings
        </el-button>
      </el-button-group>
      <div class="quick-settings">
        <el-tooltip placement="bottom" effect="dark" content="Constant Rate Factor (0-51). Lower = higher quality/larger size. Empty = auto.">
          <el-input
            v-model="crfInput"
            placeholder="CRF"
            size="small"
            style="width:70px"
            @change="onCrfChange"
            @blur="onCrfBlur"
            clearable
          />
        </el-tooltip>
        <el-tooltip placement="bottom" effect="dark" content="Target Frames Per Second (1-300). Empty = keep source.">
          <el-input
            v-model="targetFpsInput"
            placeholder="FPS"
            size="small"
            style="width:70px"
            @change="onTargetFpsChange"
            @blur="onTargetFpsBlur"
            clearable
          />
        </el-tooltip>
      </div>
    </div>

    <QuickDownload @video-selected="$emit('video-selected', $event)" />

    <div class="status-indicator">
      <el-tag
        :type="getStatusType()"
        :icon="getStatusIcon()"
        size="large"
      >
        {{ getStatusMessage() }}
      </el-tag>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElButtonGroup, ElButton, ElTag, ElInput, ElTooltip } from 'element-plus'
import { Coin, Setting } from '@element-plus/icons-vue'
import QuickDownload from './QuickDownload.vue'
import type { EngineStatus } from '@/types/api'
import type { CachedVideo } from '@/types/cache'
import { ENGINE_STATUS } from '@/constants'
import { useSettingsStore } from '@/stores/settings'
import { ref, watch } from 'vue'

interface Props {
  engineStatus: EngineStatus | null
}

interface Emits {
  (e: 'open-video-cache'): void
  (e: 'open-settings'): void
  (e: 'video-selected', video: CachedVideo): void
}

const props = defineProps<Props>()
defineEmits<Emits>()

// Settings store for quick updates
const settingsStore = useSettingsStore()
const crfInput = ref<string>('')
const targetFpsInput = ref<string>('')

function syncFromStore() {
  const gs = settingsStore.generalSettings
  crfInput.value = gs?.crf !== undefined && gs.crf !== null ? String(gs.crf) : ''
  targetFpsInput.value = gs?.target_fps !== undefined && gs.target_fps !== null ? String(gs.target_fps) : ''
}
watch(() => settingsStore.generalSettings, syncFromStore, { deep: true })
syncFromStore()

async function commitSetting(key: 'crf' | 'target_fps', raw: string) {
  if (!settingsStore.generalSettings) return
  const trimmed = raw.trim()
  if (trimmed === '') {
    await settingsStore.updateGeneralSettings({ [key]: null })
    return
  }
  const num = Number(trimmed)
  if (Number.isNaN(num)) return // ignore invalid
  if (key === 'crf') {
    if (num < 0 || num > 51) return
  } else if (key === 'target_fps') {
    if (num < 1 || num > 300) return
  }
  await settingsStore.updateGeneralSettings({ [key]: num })
}

function onCrfChange(val: string) { crfInput.value = val }
function onCrfBlur() { commitSetting('crf', crfInput.value) }
function onTargetFpsChange(val: string) { targetFpsInput.value = val }
function onTargetFpsBlur() { commitSetting('target_fps', targetFpsInput.value) }

// Status helpers
function getStatusType() {
  if (!props.engineStatus) return 'info'
  return props.engineStatus.engine_ready ? 'success' : 'warning'
}

function getStatusIcon() {
  if (!props.engineStatus) return 'Loading'
  return props.engineStatus.engine_ready ? 'CircleCheckFilled' : 'WarningFilled'
}

function getStatusMessage() {
  if (!props.engineStatus) return ENGINE_STATUS.LOADING
  return props.engineStatus.engine_ready ? ENGINE_STATUS.READY : ENGINE_STATUS.INITIALIZING
}
</script>

<style scoped>
.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.header-controls {
  display: flex;
  align-items: center;
}
.quick-settings {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: 12px;
}
</style>
