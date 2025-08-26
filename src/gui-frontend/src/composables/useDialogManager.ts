import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useSettingsStore } from '@/stores/settings'
import type { CachedVideo } from '@/types/cache'
import { UI_MESSAGES } from '@/constants'

/**
 * Composable for managing dialog states and their related operations
 */
export function useDialogManager() {
  // State
  const showVideoCache = ref(false)
  const showSettings = ref(false)
  const selectedCacheVideoId = ref<string | undefined>(undefined)

  // Store
  const settingsStore = useSettingsStore()

  /**
   * Open video cache dialog
   */
  function openVideoCache() {
    showVideoCache.value = true
  }

  /**
   * Close video cache dialog
   */
  function closeVideoCache() {
    showVideoCache.value = false
    selectedCacheVideoId.value = undefined
  }

  /**
   * Handle video selection from cache
   */
  function handleVideoSelected(video: CachedVideo, onVideoSelect?: (video: CachedVideo) => void) {
    if (onVideoSelect) {
      onVideoSelect(video)
    }
    closeVideoCache()
  }

  /**
   * Open settings dialog
   */
  function openSettings() {
    showSettings.value = true
  }

  /**
   * Close settings dialog
   */
  function closeSettings() {
    showSettings.value = false
  }

  /**
   * Update a general setting
   */
  async function updateGeneralSetting(key: string, value: unknown): Promise<boolean> {
    try {
      await settingsStore.updateGeneralSettings({ [key]: value })
      ElMessage.success(UI_MESSAGES.SETTINGS_UPDATED(key))
      return true
    } catch (error) {
      ElMessage.error(UI_MESSAGES.SETTINGS_UPDATE_FAILED(key))
      console.error(`Failed to update ${key}:`, error)
      return false
    }
  }

  /**
   * Reset settings to defaults
   */
  async function handleResetSettings(): Promise<boolean> {
    try {
      await settingsStore.resetToDefaults()
      ElMessage.success(UI_MESSAGES.SETTINGS_RESET)
      return true
    } catch (error) {
      ElMessage.error(UI_MESSAGES.SETTINGS_RESET_FAILED)
      console.error('Failed to reset settings:', error)
      return false
    }
  }

  /**
   * Export settings to args file
   */
  async function handleExportSettings(): Promise<boolean> {
    try {
      const filePath = await settingsStore.exportToArgsFile()
      ElMessage.success(UI_MESSAGES.SETTINGS_EXPORTED(filePath))
      return true
    } catch (error) {
      ElMessage.error(UI_MESSAGES.SETTINGS_EXPORT_FAILED)
      console.error('Failed to export settings:', error)
      return false
    }
  }

  /**
   * Import settings from args file (placeholder)
   */
  function handleImportSettings() {
    ElMessage.info(UI_MESSAGES.IMPORT_COMING_SOON)
  }

  /**
   * Update overwrite setting specifically
   */
  async function updateOverwriteSetting(value: boolean): Promise<boolean> {
    return await updateGeneralSetting('overwrite', value)
  }

  /**
   * Set the selected cache video ID for dialog initialization
   */
  function setSelectedCacheVideoId(id: string | undefined) {
    selectedCacheVideoId.value = id
  }

  return {
    // State
    showVideoCache,
    showSettings,
    selectedCacheVideoId,

    // Video Cache Dialog Methods
    openVideoCache,
    closeVideoCache,
    handleVideoSelected,
    setSelectedCacheVideoId,

    // Settings Dialog Methods
    openSettings,
    closeSettings,
    updateGeneralSetting,
    handleResetSettings,
    handleExportSettings,
    handleImportSettings,
    updateOverwriteSetting
  }
}
