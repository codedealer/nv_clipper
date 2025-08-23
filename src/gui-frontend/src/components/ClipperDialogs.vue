<template>
  <!-- Video Cache Dialog -->
  <el-dialog
    :model-value="showVideoCache"
    title="Video Cache Management"
    :width="DIALOG_WIDTHS.VIDEO_CACHE"
    @close="$emit('close-video-cache')"
    :close-on-click-modal="false"
  >
    <VideoCacheManager
      :selected-video-id="selectedCacheVideoId"
      @video-selected="$emit('video-selected', $event)"
    />
  </el-dialog>

  <!-- Settings Dialog -->
  <el-dialog
    :model-value="showSettings"
    title="Settings"
    :width="DIALOG_WIDTHS.SETTINGS"
    @close="$emit('close-settings')"
  >
    <SettingsPanel
      v-if="settings"
      :settings="settings"
      :is-loading="settingsLoading"
      @update-setting="handleUpdateSetting"
      @reset-settings="$emit('reset-settings')"
      @export-settings="$emit('export-settings')"
      @import-settings="$emit('import-settings')"
    />

    <div v-if="settingsError" class="error-message">
      <el-alert
        :title="settingsError"
        type="error"
        :closable="true"
        @close="$emit('clear-settings-error')"
      />
    </div>

    <template #footer>
      <el-button @click="$emit('close-settings')">Close</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ElDialog, ElButton, ElAlert } from 'element-plus'
import VideoCacheManager from './VideoCacheManager.vue'
import SettingsPanel from './SettingsPanel.vue'
import type { CachedVideo } from '@/types/cache'
import type { GeneralSettings } from '@/types/settings'
import { DIALOG_WIDTHS } from '@/constants'

interface Props {
  showVideoCache: boolean
  showSettings: boolean
  selectedCacheVideoId?: string
  settings: GeneralSettings | null
  settingsLoading: boolean
  settingsError: string | null
}

interface Emits {
  (e: 'close-video-cache'): void
  (e: 'close-settings'): void
  (e: 'video-selected', video: CachedVideo): void
  (e: 'update-setting', key: string, value: unknown): void
  (e: 'reset-settings'): void
  (e: 'export-settings'): void
  (e: 'import-settings'): void
  (e: 'clear-settings-error'): void
}

defineProps<Props>()
const emit = defineEmits<Emits>()

function handleUpdateSetting(key: string, value: unknown) {
  emit('update-setting', key, value)
}
</script>

<style scoped>
.error-message {
  margin-top: 16px;
}
</style>
