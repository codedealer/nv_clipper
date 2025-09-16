import { computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useVideoOperations } from './useVideoOperations'
import { useMarkupOperations } from './useMarkupOperations'
import type { ColorGradingState } from '@/types/colorGrading'
import type { ClipInfo } from '@/types/api'
import { buildFilterFromState } from '@/utils/colorFilterBuild'
import { UI_MESSAGES } from '@/constants'
import { useClipperStore } from '@/stores/counter'

/**
 * Composable for color grading functionality including active clip management
 * and color grading modifications
 */
export function useColorGrading(
  videoOps?: ReturnType<typeof useVideoOperations>,
  markupOps?: ReturnType<typeof useMarkupOperations>
) {
  const clipperStore = useClipperStore()
  // Must expose the numeric index, not the ref object itself, or downstream typeof checks fail
  const activeColorGradingClip = computed({
    get: () => clipperStore.activeColorGradingClip,
    set: (v: number | null) => clipperStore.setActiveColorGradingClip(v)
  })

  // Use passed composables or create new instances (for backward compatibility)
  const { videoDuration, findFirstValidClip } = videoOps || useVideoOperations()
  const { parsedClips, updateClipColorGrading, applyColorGradingToAllClips, getActiveClip, isMockMarkup } = markupOps || useMarkupOperations()

  // Computed properties
  const selectedClip = computed(() => getActiveClip(activeColorGradingClip.value))

  const hasActiveClip = computed(() =>
    activeColorGradingClip.value !== null && selectedClip.value !== null
  )

  /**
   * Set the active clip for color grading
   */
  function setActiveClip(clipIndex: number | null) {
    if (clipIndex !== null && (clipIndex < 0 || clipIndex >= parsedClips.value.length)) {
      console.warn('Invalid clip index for color grading:', clipIndex)
      return
    }

    if (clipIndex === activeColorGradingClip.value) {
      return
    }

  activeColorGradingClip.value = clipIndex

    if (clipIndex !== null) {
      ElMessage.info(UI_MESSAGES.CLIP_SWITCHED(clipIndex))
    }
  }

  /**
   * Handle clip selection for color grading (separate from processing selection)
   */
  function handleClipSelectedForColorGrading(clipIndex: number) {
    if (clipIndex >= 0 && clipIndex < parsedClips.value.length) {
      setActiveClip(clipIndex)
    } else {
      ElMessage.error('Invalid clip selection for color grading')
    }
  }

  /**
   * Handle color grading changes for the active clip
   */
  function handleColorGradingChanged(clipNumber: number, filter: string, state?: ColorGradingState) {
    const effectiveFilter = (!filter || !filter.length) && state ? buildFilterFromState(state) : filter
    const success = updateClipColorGrading(clipNumber, effectiveFilter, state)
    if (!success) {
      ElMessage.error('Failed to apply color grading changes')
    }
  }

  /**
   * Initialize active clip when clips are loaded
   */
  function initializeActiveClip(clips: ClipInfo[]) {
    if (clips.length === 0) {
  activeColorGradingClip.value = null
      return
    }

    // Set the first valid clip as active for color grading
    const firstValidIndex = findFirstValidClip(clips, videoDuration.value)
  activeColorGradingClip.value = firstValidIndex
  }

  /**
   * Reset color grading state
   */
  function resetColorGradingState() {
  activeColorGradingClip.value = null
  }

  /**
   * Get color grading filter for a specific clip by clip number (1-based)
   */
  function getClipColorGrading(clipNumber: number): string | undefined {
    const clip = parsedClips.value.find(c => c.number === clipNumber)
    return clip?.overrides?.colorGrading as string | undefined
  }

  /**
   * Check if a clip has color grading applied by clip number (1-based)
   */
  function clipHasColorGrading(clipNumber: number): boolean {
    const filter = getClipColorGrading(clipNumber)
    return !!filter && filter.trim().length > 0
  }

  /**
   * Clear color grading from the active clip
   */
  function clearActiveClipColorGrading() {
    if (selectedClip.value) {
      handleColorGradingChanged(selectedClip.value.number, '')
    }
  }

  /**
   * Move to next clip for color grading
   */
  function nextClip() {
    if (!parsedClips.value.length) return

    const currentIndex = activeColorGradingClip.value ?? -1
    const nextIndex = (currentIndex + 1) % parsedClips.value.length
    setActiveClip(nextIndex)
  }

  /**
   * Apply color grading filter to all clips
   */
  function handleCopyToAllClips(state: ColorGradingState): boolean {
    if (isMockMarkup.value) {
      ElMessage.warning('Mock markup only has one clip')
      return false
    }
    const filter = buildFilterFromState(state)
    return applyColorGradingToAllClips(filter, state)
  }
  /**
   * Move to previous clip for color grading
   */
  function previousClip() {
    if (!parsedClips.value.length) return

    const currentIndex = activeColorGradingClip.value ?? 0
    const prevIndex = currentIndex === 0 ? parsedClips.value.length - 1 : currentIndex - 1
    setActiveClip(prevIndex)
  }

  return {
    // State
    activeColorGradingClip,

    // Computed
    selectedClip,
    hasActiveClip,
    isMockMarkup,

    // Methods
    setActiveClip,
    handleClipSelectedForColorGrading,
    handleColorGradingChanged,
    handleCopyToAllClips,
    initializeActiveClip,
    resetColorGradingState,
    getClipColorGrading,
    clipHasColorGrading,
    clearActiveClipColorGrading,
    nextClip,
    previousClip
  }
}
