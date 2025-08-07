<template>
  <el-dialog
    v-model="visible"
    title="Download Video to Cache"
    width="600px"
    :before-close="handleClose"
  >
    <el-form :model="form" label-width="120px" label-position="left">
      <el-form-item label="Video URL" required>
        <el-input
          v-model="form.url"
          type="url"
          placeholder="https://www.youtube.com/watch?v=..."
          clearable
        />
        <div class="form-help">
          Supported platforms: YouTube, Weverse, Naver TV, AfreecaTV, and others supported by yt-dlp
        </div>
      </el-form-item>

      <el-form-item label="Custom Title">
        <el-input
          v-model="form.title"
          placeholder="Leave empty to use original title"
          clearable
        />
      </el-form-item>

      <el-form-item label="Download Format">
        <el-radio-group v-model="form.formatPreset">
          <el-radio value="default">Use default yt-dlp settings</el-radio>
          <el-radio value="settings">Use format settings from Settings</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-collapse>
        <el-collapse-item title="Advanced Options" name="advanced">
          <el-form-item label="Auto-update yt-dlp">
            <el-radio-group v-model="form.autoUpdatePreset">
              <el-radio value="settings">Use settings value ({{ settingsAutoUpdate ? 'Enabled' : 'Disabled' }})</el-radio>
              <el-radio value="override">Override for this download</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item v-if="form.autoUpdatePreset === 'override'" label="">
            <el-checkbox v-model="form.auto_update_override">
              Enable auto-update for this download
            </el-checkbox>
          </el-form-item>
        </el-collapse-item>
      </el-collapse>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">Cancel</el-button>
      <el-button
        type="primary"
        @click="handleSubmit"
        :disabled="!form.url.trim()"
        :icon="Download"
      >
        Start Download
      </el-button>
    </template>
  </el-dialog>
</template><script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { CacheDownloadRequest } from '@/types/cache'
import { Download } from '@element-plus/icons-vue'
import { useSettingsStore } from '@/stores/settings'

// Emits
const emit = defineEmits<{
  close: []
  download: [request: CacheDownloadRequest]
}>()

// Stores
const settingsStore = useSettingsStore()

// Local state
const visible = ref(true)

const form = ref({
  url: '',
  title: '',
  formatPreset: 'default',
  autoUpdatePreset: 'settings',
  auto_update_override: false
})

// Computed
const settingsAutoUpdate = computed(() =>
  settingsStore.generalSettings?.ytdl_auto_update ?? true
)

// Load settings on mount
onMounted(async () => {
  if (!settingsStore.hasSettings) {
    try {
      await settingsStore.loadAllSettings()
    } catch (error) {
      console.error('Failed to load settings:', error)
    }
  }
})

// Methods
function handleClose() {
  visible.value = false
  emit('close')
}

function handleSubmit() {
  const request: CacheDownloadRequest = {
    url: form.value.url.trim(),
    use_settings_format: form.value.formatPreset === 'settings'
  }

  if (form.value.title.trim()) {
    request.title = form.value.title.trim()
  }

  // Handle auto-update setting
  if (form.value.autoUpdatePreset === 'override') {
    request.auto_update = form.value.auto_update_override
  } else {
    request.auto_update = settingsAutoUpdate.value
  }

  emit('download', request)
  handleClose()
}
</script>

<style scoped>
/* Ensure dialog inherits dark theme properly */
:deep(.el-dialog) {
  background-color: var(--el-bg-color);
}

:deep(.el-form-item__label) {
  color: var(--el-text-color-primary);
}

:deep(.el-input__wrapper) {
  background-color: var(--el-fill-color);
  border-color: var(--el-border-color);
}

:deep(.el-input__inner) {
  background-color: var(--el-fill-color);
  border-color: var(--el-border-color);
  color: var(--el-text-color-primary);
}

:deep(.el-input__inner:focus) {
  border-color: var(--el-color-primary);
}

:deep(.el-select .el-input__wrapper) {
  background-color: var(--el-fill-color);
}

:deep(.el-select .el-input__inner) {
  background-color: var(--el-fill-color);
  color: var(--el-text-color-primary);
}

:deep(.el-checkbox__label) {
  color: var(--el-text-color-primary);
}

:deep(.el-collapse-item__header) {
  background-color: var(--el-fill-color-light);
  color: var(--el-text-color-primary);
}

:deep(.el-collapse-item__content) {
  background-color: var(--el-bg-color);
}

:deep(.el-input-number .el-input__wrapper) {
  background-color: var(--el-fill-color);
}
</style>

