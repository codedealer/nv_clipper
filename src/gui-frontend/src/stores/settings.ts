import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type {
  GeneralSettings,
  VideoSpecificSettings,
  SettingsSchema
} from '@/types/settings'
import { waitForPywebview } from '@/utils/api'

export const useSettingsStore = defineStore('settings', () => {
  // State
  const generalSettings = ref<GeneralSettings | null>(null)
  const videoSettings = ref<VideoSpecificSettings | null>(null)
  const settingsSchema = ref<SettingsSchema | null>(null)
  const isLoading = ref(false)
  const lastError = ref<string | null>(null)

  // Getters
  const hasSettings = computed(() => generalSettings.value !== null)
  const isOverwriteEnabled = computed(() => generalSettings.value?.overwrite ?? false)

  // Actions
  async function loadAllSettings(): Promise<void> {
    isLoading.value = true
    lastError.value = null

    try {
      const api = await waitForPywebview()

      // Load settings and schema in parallel
      const [settingsResult, schemaResult] = await Promise.all([
        api.get_all_settings(),
        api.get_settings_schema()
      ])

      if (settingsResult.status === 'success') {
        generalSettings.value = settingsResult.general as unknown as GeneralSettings
        videoSettings.value = settingsResult.video as unknown as VideoSpecificSettings
      } else {
        throw new Error(settingsResult.message || 'Failed to load settings')
      }

      if (schemaResult.status === 'success') {
        settingsSchema.value = schemaResult.schema as unknown as SettingsSchema
      } else {
        console.warn('Failed to load settings schema:', schemaResult.message)
      }

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      lastError.value = errorMessage
      console.error('Settings store: Failed to load settings:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function loadGeneralSettings(): Promise<void> {
    isLoading.value = true
    lastError.value = null

    try {
      const api = await waitForPywebview()
      const result = await api.get_general_settings()

      if (result.status === 'success') {
        generalSettings.value = result.settings as unknown as GeneralSettings
      } else {
        throw new Error(result.message || 'Failed to load general settings')
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      lastError.value = errorMessage
      console.error('Failed to load general settings:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function loadVideoSettings(): Promise<void> {
    isLoading.value = true
    lastError.value = null

    try {
      const api = await waitForPywebview()
      const result = await api.get_video_settings()

      if (result.status === 'success') {
        videoSettings.value = result.settings as unknown as VideoSpecificSettings
      } else {
        throw new Error(result.message || 'Failed to load video settings')
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      lastError.value = errorMessage
      console.error('Failed to load video settings:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function updateGeneralSettings(updates: Partial<GeneralSettings>): Promise<void> {
    if (!generalSettings.value) {
      throw new Error('General settings not loaded')
    }

    isLoading.value = true
    lastError.value = null

    try {
      const api = await waitForPywebview()
      const result = await api.update_general_settings(updates)

      if (result.status === 'success') {
        generalSettings.value = result.settings as unknown as GeneralSettings
      } else {
        throw new Error(result.message || 'Failed to update general settings')
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      lastError.value = errorMessage
      console.error('Failed to update general settings:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function updateVideoSettings(updates: Partial<VideoSpecificSettings>): Promise<void> {
    if (!videoSettings.value) {
      throw new Error('Video settings not loaded')
    }

    isLoading.value = true
    lastError.value = null

    try {
      const api = await waitForPywebview()
      const result = await api.update_video_settings(updates)

      if (result.status === 'success') {
        videoSettings.value = result.settings as unknown as VideoSpecificSettings
      } else {
        throw new Error(result.message || 'Failed to update video settings')
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      lastError.value = errorMessage
      console.error('Failed to update video settings:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function resetToDefaults(): Promise<void> {
    isLoading.value = true
    lastError.value = null

    try {
      const api = await waitForPywebview()
      const result = await api.reset_settings_to_defaults()

      if (result.status === 'success') {
        generalSettings.value = result.general as unknown as GeneralSettings
        videoSettings.value = result.video as unknown as VideoSpecificSettings
      } else {
        throw new Error(result.message || 'Failed to reset settings')
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      lastError.value = errorMessage
      console.error('Failed to reset settings:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function exportToArgsFile(filePath?: string): Promise<string> {
    isLoading.value = true
    lastError.value = null

    try {
      const api = await waitForPywebview()
      const result = await api.export_settings_to_args_file(filePath)

      if (result.status === 'success') {
        return result.file_path || ''
      } else {
        throw new Error(result.message || 'Failed to export settings')
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      lastError.value = errorMessage
      console.error('Failed to export settings:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function importFromArgsFile(filePath: string): Promise<void> {
    isLoading.value = true
    lastError.value = null

    try {
      const api = await waitForPywebview()
      const result = await api.import_settings_from_args_file(filePath)

      if (result.status === 'success') {
        generalSettings.value = result.general as unknown as GeneralSettings
        videoSettings.value = result.video as unknown as VideoSpecificSettings
      } else {
        throw new Error(result.message || 'Failed to import settings')
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      lastError.value = errorMessage
      console.error('Failed to import settings:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  function clearError(): void {
    lastError.value = null
  }

  // Convenience method to toggle overwrite setting
  async function toggleOverwrite(): Promise<void> {
    if (!generalSettings.value) {
      throw new Error('General settings not loaded')
    }

    await updateGeneralSettings({
      overwrite: !generalSettings.value.overwrite
    })
  }

  return {
    // State
    generalSettings,
    videoSettings,
    settingsSchema,
    isLoading,
    lastError,

    // Getters
    hasSettings,
    isOverwriteEnabled,

    // Actions
    loadAllSettings,
    loadGeneralSettings,
    loadVideoSettings,
    updateGeneralSettings,
    updateVideoSettings,
    resetToDefaults,
    exportToArgsFile,
    importFromArgsFile,
    clearError,
    toggleOverwrite
  }
})
