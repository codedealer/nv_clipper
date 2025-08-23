import { ref, readonly } from 'vue'
import { ElMessage } from 'element-plus'
import { useClipperStore } from '@/stores/counter'
import type { ClipInfo } from '@/types/api'
import type { MarkupData } from '@/utils/markup'
import {
  SUPPORTED_MARKUP_EXTENSIONS,
  UI_MESSAGES
} from '@/constants'

/**
 * Composable for markup-related operations including parsing, clip management,
 * and markup data manipulation
 */
export function useMarkupOperations() {
  // State
  const parsedClips = ref<ClipInfo[]>([])
  const selectedClips = ref<number[]>([])
  const parsedMarkupData = ref<MarkupData | null>(null)

  // Store
  const clipperStore = useClipperStore()

  /**
   * Parse a JSON markup file and extract clips
   */
  async function parseMarkupFile(filePath: string): Promise<boolean> {
    try {
      const result = await clipperStore.parseMarkupFile(filePath)

      if (result.status === 'success' && result.clips) {
        parsedClips.value = result.clips
        selectedClips.value = Array.from({ length: result.clips.length }, (_, i) => i)

        // Load the complete markup structure to enable color grading modifications
        await loadFullMarkupData(filePath)

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
        parsedMarkupData.value = fullMarkupData.data
      } else {
        parsedMarkupData.value = null
        if (fullMarkupData.message) {
          ElMessage.warning(`Color grading may not work: ${fullMarkupData.message}`)
        }
      }
    } catch (error) {
      parsedMarkupData.value = null
      ElMessage.warning('Color grading changes may not persist due to file loading error')
    }
  }

  /**
   * Set parsed markup data and clips from external source (e.g., mock markup)
   */
  function setMarkupData(markupData: MarkupData, clips: ClipInfo[]) {
    parsedMarkupData.value = markupData
    parsedClips.value = clips
    selectedClips.value = Array.from({ length: clips.length }, (_, i) => i)
  }

  /**
   * Update color grading for a specific clip
   */
  function updateClipColorGrading(clipNumber: number, filter: string): boolean {
    // Find the clip and update its color grading
    const clip = parsedClips.value.find(c => c.number === clipNumber)
    if (clip) {
      // Update the clip's color grading in the overrides
      clip.overrides = {
        ...clip.overrides,
        colorGrading: filter || undefined
      }

      // Also update the markup data structure to ensure backend receives changes
      if (parsedMarkupData.value?.markerPairs && Array.isArray(parsedMarkupData.value.markerPairs)) {
        const markerPair = parsedMarkupData.value.markerPairs.find((mp: Record<string, unknown>) => mp.number === clipNumber)
        if (markerPair) {
          markerPair.overrides = {
            ...markerPair.overrides,
            colorGrading: filter || undefined
          }
        }
      }

      ElMessage.success(filter ? UI_MESSAGES.COLOR_GRADING_APPLIED : UI_MESSAGES.COLOR_GRADING_REMOVED)
      return true
    } else {
      ElMessage.error(UI_MESSAGES.CLIP_NOT_FOUND)
      return false
    }
  }

  /**
   * Get the currently active clip for color grading
   */
  function getActiveClip(activeIndex: number | null): ClipInfo | null {
    if (!parsedClips.value.length) return null

    // Use the active color grading clip if set, otherwise use the first selected clip
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
    return SUPPORTED_MARKUP_EXTENSIONS.includes(extension as any)
  }

  /**
   * Reset all markup-related state
   */
  function resetMarkupState() {
    parsedClips.value = []
    selectedClips.value = []
    parsedMarkupData.value = null
  }

  /**
   * Toggle clip selection for processing
   */
  function toggleClipSelection(clipIndex: number) {
    const currentIndex = selectedClips.value.indexOf(clipIndex)
    if (currentIndex > -1) {
      selectedClips.value.splice(currentIndex, 1)
    } else {
      selectedClips.value.push(clipIndex)
    }
  }

  /**
   * Select all clips for processing
   */
  function selectAllClips() {
    selectedClips.value = Array.from({ length: parsedClips.value.length }, (_, i) => i)
  }

  /**
   * Deselect all clips
   */
  function deselectAllClips() {
    selectedClips.value = []
  }

  /**
   * Check if we have valid markup data for processing
   */
  function hasValidMarkup(): boolean {
    return parsedClips.value.length > 0 || parsedMarkupData.value !== null
  }

  return {
    // State
    parsedClips,
    selectedClips,
    parsedMarkupData: readonly(parsedMarkupData),

    // Methods
    parseMarkupFile,
    loadFullMarkupData,
    setMarkupData,
    updateClipColorGrading,
    getActiveClip,
    isMarkupFile,
    resetMarkupState,
    toggleClipSelection,
    selectAllClips,
    deselectAllClips,
    hasValidMarkup
  }
}
