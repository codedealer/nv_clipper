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
import { ElButtonGroup, ElButton, ElTag } from 'element-plus'
import { Coin, Setting } from '@element-plus/icons-vue'
import QuickDownload from './QuickDownload.vue'
import type { EngineStatus } from '@/types/api'
import type { CachedVideo } from '@/types/cache'
import { ENGINE_STATUS, ELEMENT_CONFIGS } from '@/constants'

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
</style>
