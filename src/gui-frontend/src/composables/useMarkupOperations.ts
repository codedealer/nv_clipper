import { computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useClipperStore } from '@/stores/counter'
import type { ClipInfo } from '@/types/api'
import type { ClipSettingsState, ClipSettingsUpdatePayload } from '@/types/clipSettings'
import type { MarkupData } from '@/utils/markup'
import { SUPPORTED_MARKUP_EXTENSIONS, MOCK_MARKUP_DEFAULTS } from '@/constants'
import type { ColorGradingState } from '@/types/colorGrading'
import { storeToRefs } from 'pinia'

function cloneState<T>(obj: T): T {
  if (obj == null) return obj
  try {
    if (typeof structuredClone === 'function') {
      return structuredClone(obj as unknown as T)
    }
  } catch { /* ignore */ }
  return JSON.parse(JSON.stringify(obj)) as T
}

/**
 * Composable for markup-related operations including parsing, clip management,
 * and markup data manipulation
 */
export function useMarkupOperations() {
  // Central store (single source of truth)
  const clipperStore = useClipperStore()
  const { parsedClips, selectedClips, parsedMarkupData, clipSettingsDirty } = storeToRefs(clipperStore)

  // Computed properties
  const isMockMarkup = computed(() => {
    // Mock markup is identified by having exactly one clip that starts at 0
    // and the markup data having the generic platform structure
  if (parsedClips.value.length !== 1) return false
  const clip = parsedClips.value[0]
  const markupData = parsedMarkupData.value as MarkupData | null

    return (
      clip.start === 0 &&
      clip.number === 1 &&
      markupData?.platform === MOCK_MARKUP_DEFAULTS.PLATFORM &&
      markupData?.videoID === MOCK_MARKUP_DEFAULTS.VIDEO_ID
    )
  })

  /**
   * Parse a JSON markup file and extract clips
   */
  async function parseMarkupFile(filePath: string): Promise<boolean> {
    try {
  const result = await clipperStore.parseMarkupFile(filePath)

      if (result.status === 'success' && result.clips) {
  clipperStore.setParsedClips(result.clips)
  await loadFullMarkupData(filePath) // loads markup data

        ElMessage.success(`Loaded ${result.clips.length} clips from markup`)
        return true
      } else {
        throw new Error(result.message || 'Failed to parse markup file')
      }
  } catch (error) {
      console.error('Failed to parse markup file:', error)
      ElMessage.error(`Failed to parse markup file: ${error}`)

      // Reset state on failure
  resetMarkupState()
      return false
    }
  }

  /**
   * Load the complete markup file data for modifications
   */
  async function loadFullMarkupData(filePath: string): Promise<void> {
    try {
  const fullMarkupData = await window.pywebview.api.load_markup_file_data(filePath)

      if (fullMarkupData.status === 'success' && fullMarkupData.data) {
        clipperStore.setParsedMarkupData(fullMarkupData.data as MarkupData)
      } else {
        clipperStore.setParsedMarkupData(null)
        if (fullMarkupData.message) {
          ElMessage.warning(`Color grading may not work: ${fullMarkupData.message}`)
        }
      }
    } catch {
      clipperStore.setParsedMarkupData(null)
      ElMessage.warning('Color grading changes may not persist due to file loading error')
    }
  }

  /**
   * Set parsed markup data and clips from external source (e.g., mock markup)
   */
  function setMarkupData(markupData: MarkupData, clips: ClipInfo[]) {
    clipperStore.setParsedMarkupData(markupData)
    clipperStore.setParsedClips(clips)
  }

  /**
   * Apply color grading filter to all clips
   */
  function applyColorGradingToAllClips(filter: string, state?: ColorGradingState): boolean {
    if (isMockMarkup.value) {
      ElMessage.warning('Cannot apply to all clips in mock markup')
      return false
    }

    let appliedCount = 0

  parsedClips.value.forEach(clip => {
      clip.overrides = {
        ...clip.overrides,
        colorGrading: filter || undefined,
        colorGradingState: state ? cloneState(state) : (clip.overrides as { colorGradingState?: ColorGradingState } | undefined)?.colorGradingState
      }

      // Also update the markup data structure
  const pm = parsedMarkupData.value as unknown as { markerPairs?: Array<{ number: number; overrides?: { colorGrading?: string; colorGradingState?: ColorGradingState } }> } | null
      if (pm?.markerPairs && Array.isArray(pm.markerPairs)) {
        const markerPair = pm.markerPairs.find((mp: { number?: unknown }) => mp.number === clip.number)
        if (markerPair) {
          markerPair.overrides = {
            ...markerPair.overrides,
            colorGrading: filter || undefined,
            colorGradingState: state ? cloneState(state) : markerPair.overrides?.colorGradingState
          }
          appliedCount++
        }
      }
    })

    if (appliedCount > 0) {
      ElMessage.success(`Color grading applied to ${appliedCount} clips`)
      return true
    } else {
      ElMessage.error('Failed to apply color grading to all clips')
      return false
    }
  }
  function updateClipColorGrading(clipNumber: number, filter: string, state?: ColorGradingState): boolean {
    // Find the clip and update its color grading
  const clip = parsedClips.value.find(c => c.number === clipNumber)
    if (clip) {
      // Update the clip's color grading in the overrides
      clip.overrides = {
        ...clip.overrides,
        colorGrading: filter || undefined,
        colorGradingState: state ? cloneState(state) : (clip.overrides as { colorGradingState?: ColorGradingState } | undefined)?.colorGradingState
      }

      // Also update the markup data structure to ensure backend receives changes
  const pm = parsedMarkupData.value as unknown as { markerPairs?: Array<{ number: number; overrides?: { colorGrading?: string; colorGradingState?: ColorGradingState } }> } | null
      if (pm?.markerPairs && Array.isArray(pm.markerPairs)) {
        const markerPair = pm.markerPairs.find((mp: { number?: unknown }) => mp.number === clipNumber)
        if (markerPair) {
          markerPair.overrides = {
            ...markerPair.overrides,
            colorGrading: filter || undefined,
            colorGradingState: state ? cloneState(state) : markerPair.overrides?.colorGradingState
          }
        }
      }

      // Don't show success messages for individual clip updates to avoid spam
      return true
    } else {
      console.error('Clip not found for color grading update:', clipNumber)
      return false
    }
  }

  function updateClipSettings(clipNumber: number, payload: ClipSettingsUpdatePayload): boolean {
    return clipperStore.updateClipSettings(clipNumber, payload)
  }

  function resetClipSettings(clipNumber: number): boolean {
    return clipperStore.resetClipSettings(clipNumber)
  }

  function getClipSettingsState(clipNumber: number): ClipSettingsState | null {
    return clipperStore.getClipSettingsState(clipNumber)
  }

  function getOriginalClipSettingsState(clipNumber: number): ClipSettingsState | null {
    return clipperStore.getOriginalClipSettingsState(clipNumber)
  }

  /**
   * Get the currently active clip for color grading
   */
  function getActiveClip(activeIndex: number | null): ClipInfo | null {
    if (!parsedClips.value.length) return null
    let targetIndex = activeIndex
    if (targetIndex === null || targetIndex === undefined) {
      if (!selectedClips.value.length) return null
      targetIndex = selectedClips.value[0]
    }
    return parsedClips.value[targetIndex] || null
  }

  /**
   * Check if markup file extension is supported
   */
  function isMarkupFile(filename: string): boolean {
    const extension = filename.split('.').pop()?.toLowerCase()
    if (!extension) return false
    return (SUPPORTED_MARKUP_EXTENSIONS as readonly string[]).includes(extension)
  }

  /**
   * Reset all markup-related state
   */
  function resetMarkupState() {
  clipperStore.resetMarkupState()
  }

  /**
   * Toggle clip selection for processing
   */
  function toggleClipSelection(clipIndex: number) {
  clipperStore.toggleClipSelection(clipIndex)
  }

  /**
   * Select all clips for processing
   */
  function selectAllClips() {
  clipperStore.selectAllClips()
  }

  /**
   * Deselect all clips
   */
  function deselectAllClips() {
  clipperStore.deselectAllClips()
  }

  /**
   * Check if we have valid markup data for processing
   */
  function hasValidMarkup(): boolean {
  return clipperStore.hasValidMarkup()
  }

  return {
    // State
  parsedClips,
  selectedClips,
  parsedMarkupData,
  clipSettingsDirty,

    // Computed
    isMockMarkup,

    // Methods
    parseMarkupFile,
    loadFullMarkupData,
    setMarkupData,
    updateClipColorGrading,
    applyColorGradingToAllClips,
    getActiveClip,
    isMarkupFile,
    resetMarkupState,
    toggleClipSelection,
    selectAllClips,
    deselectAllClips,
    hasValidMarkup,
    updateClipSettings,
    resetClipSettings,
    getClipSettingsState,
    getOriginalClipSettingsState
  }
}
