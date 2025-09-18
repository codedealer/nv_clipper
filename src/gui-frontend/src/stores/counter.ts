import { ref, computed, watch } from 'vue'
import { defineStore } from 'pinia'
import type { SelectedFiles, ProcessingResult, EngineStatus, ParseMarkupResult, JobStatus, ClipInfo } from '@/types/api'
import type { ColorGradingState } from '@/types/colorGrading'
import { waitForPywebview } from '@/utils/api'
import { useSettingsStore } from './settings'
import { ElMessage } from 'element-plus'
import type { MarkupData } from '@/utils/markup'

export const useClipperStore = defineStore('clipper', () => {
  // State
  const selectedFiles = ref<SelectedFiles>({
    markup: null,
    video: null
  })

  const isProcessing = ref(false)
  const isCanceling = ref(false)
  const currentJobId = ref<string | null>(null)
  const processingStatus = ref<string>('')
  const processingResult = ref<ProcessingResult | null>(null)
  const engineStatus = ref<EngineStatus | null>(null)

  // New: video info (single source of truth for loaded video metadata)
  const videoInfo = ref<null | {
    duration: number | null
    width: number | null
    height: number | null
    frame_rate?: string | null
    codec_name?: string | null
    bit_rate?: string | null
    path: string | null
  }>(null)

  // Markup / clips state (single source of truth for UI)
  const parsedClips = ref<ClipInfo[]>([])
  const selectedClips = ref<number[]>([])
  const parsedMarkupData = ref<MarkupData | null>(null)
  const activeColorGradingClip = ref<number | null>(null)
  // Key to force remount of preview / grading panel when selected files change in any way
  const previewMountKey = ref(0)

  // Derived clip state
  const hasClips = computed(() => parsedClips.value.length > 0)
  const activeSelectedClip = computed(() => {
    if (!parsedClips.value.length) return null
    if (activeColorGradingClip.value !== null && activeColorGradingClip.value >= 0 && activeColorGradingClip.value < parsedClips.value.length) {
      return parsedClips.value[activeColorGradingClip.value]
    }
    if (selectedClips.value.length) {
      const idx = selectedClips.value[0]
      return parsedClips.value[idx] || null
    }
    return parsedClips.value[0]
  })
  // Alias for preview usage (semantic clarity)
  const currentPreviewClip = activeSelectedClip

  // Getters
  const hasMarkupFile = computed(() => !!selectedFiles.value.markup)
  const hasVideoFile = computed(() => !!selectedFiles.value.video)
  const canProcess = computed(() => hasMarkupFile.value && !isProcessing.value && !isCanceling.value)
  const videoDuration = computed(() => videoInfo.value?.duration ?? null)

  // Actions
  function setSelectedFiles(files: SelectedFiles) {
    selectedFiles.value = files
  }

  function setMarkupFile(path: string | null) {
    selectedFiles.value.markup = path
  }

  function setVideoFile(path: string | null) {
    selectedFiles.value.video = path
  }

  function setVideoInfo(info: typeof videoInfo.value) {
    videoInfo.value = info
  }

  function clearVideoInfo() {
    videoInfo.value = null
  }

  function clearSelectedFiles() {
    selectedFiles.value = { markup: null, video: null }
  }

  async function startProcessing(selectedClips?: number[], markupData?: Record<string, unknown>): Promise<ProcessingResult> {
    if (!canProcess.value && !markupData) {
      throw new Error('Cannot start processing: no markup file selected or already processing')
    }

    isProcessing.value = true
    isCanceling.value = false
    processingStatus.value = 'Starting processing...'
    currentJobId.value = null
    processingResult.value = null

    try {
      const api = await waitForPywebview()

      // Use settings store to get current settings
      const settingsStore = useSettingsStore()

      // Ensure settings are loaded
      if (!settingsStore.hasSettings) {
        await settingsStore.loadAllSettings()
      }

      const result = await api.process_files(
        selectedFiles.value.markup || undefined,
        selectedFiles.value.video || undefined,
        selectedClips || undefined,
        markupData || undefined
      )

      if (result.status === 'accepted' && result.job_id) {
        currentJobId.value = result.job_id
        processingStatus.value = 'Processing files...'
        // From here we rely entirely on push events
        return result
      }

      // Immediate completion (success/error)
      processingResult.value = result
      processingStatus.value = result.message
      isProcessing.value = false
      currentJobId.value = null
      // If processing succeeded and markup was moved, update path now
      if (result.status === 'success' && result.markup_moved && result.moved_markup_path) {
        // Only update if the currently stored markup matches the original path or is non-existent
        if (!selectedFiles.value.markup ||
            (result.original_markup_path && selectedFiles.value.markup === result.original_markup_path)) {
          selectedFiles.value.markup = result.moved_markup_path
          // Optionally re-parse to refresh UI if needed
          try {
            const api = await waitForPywebview()
            const parseRes = await api.parse_markup_file(result.moved_markup_path)
            if (parseRes.status === 'success' && parseRes.clips) {
              setParsedClips(parseRes.clips)
            }
          } catch { /* best-effort refresh */ }
        }
      }
      return result
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      processingResult.value = {
        status: 'error',
        message: errorMessage
      }
      processingStatus.value = `Processing failed: ${errorMessage}`
      isProcessing.value = false
      currentJobId.value = null
      throw error
    }
  }

  // Handle backend push events
  function onProcessingEvent(payload: JobStatus & { job_id: string }): void {
    if (!payload || !payload.job_id) return
    if (payload.job_id !== currentJobId.value) return

    if (payload.status === 'starting' || payload.status === 'processing') {
      processingStatus.value = payload.message || 'Processing...'
      isProcessing.value = true
      return
    }

    if (payload.status === 'success') {
      processingResult.value = {
        status: 'success',
        message: payload.message || 'Processing completed',
        report: payload.report,
        output_path: payload.output_path
      }
      processingStatus.value = payload.message || 'Processing completed successfully'
      isProcessing.value = false
      isCanceling.value = false
      currentJobId.value = null
      // Update markup path if it was moved by backend
      if (payload.markup_moved && payload.moved_markup_path) {
        if (!selectedFiles.value.markup ||
            (payload.original_markup_path && selectedFiles.value.markup === payload.original_markup_path)) {
          selectedFiles.value.markup = payload.moved_markup_path
        }
      }
      // Show completion toast
      ElMessage.success(processingStatus.value)
      return
    }

    if (payload.status === 'error') {
      processingResult.value = {
        status: 'error',
        message: payload.message || 'Processing failed'
      }
      processingStatus.value = payload.message || 'Processing failed'
      isProcessing.value = false
      isCanceling.value = false
      currentJobId.value = null
      // Show error toast
      ElMessage.error(processingStatus.value)
      return
    }

    if (payload.status === 'canceled') {
      processingResult.value = {
        status: 'canceled',
        message: payload.message || 'Processing canceled'
      }
      processingStatus.value = payload.message || 'Processing canceled'
      isProcessing.value = false
      isCanceling.value = false
      currentJobId.value = null
      // Show cancel info toast
      ElMessage.info(processingStatus.value)
      return
    }
  }

  async function cancelCurrentJob(): Promise<void> {
    if (!currentJobId.value) return
    try {
      const api = await waitForPywebview()
      isCanceling.value = true
      processingStatus.value = 'Canceling...'
      await api.cancel_processing(currentJobId.value)
      // We expect a push event to arrive
    } catch (e) {
      console.error('Cancel failed', e)
      isCanceling.value = false
    }
  }

  async function getEngineStatus(): Promise<EngineStatus> {
    try {
      const api = await waitForPywebview()
      const status = await api.get_status()
      engineStatus.value = status
      return status
    } catch (error) {
      throw new Error(`Failed to get engine status: ${error}`)
    }
  }

  async function selectFiles(): Promise<string[]> {
    try {
      const api = await waitForPywebview()
      return await api.select_files()
    } catch (error) {
      throw new Error(`File selection failed: ${error}`)
    }
  }

  async function parseMarkupFile(filePath: string): Promise<ParseMarkupResult> {
    try {
      const api = await waitForPywebview()
      return await api.parse_markup_file(filePath)
    } catch (error) {
      throw new Error(`Failed to parse markup file: ${error}`)
    }
  }

  // ----- Clip / Markup Actions -----
  function setParsedClips(clips: ClipInfo[]) {
    parsedClips.value = [...clips]
    selectedClips.value = clips.map((_, i) => i)
    activeColorGradingClip.value = clips.length ? 0 : null
  }

  function setSelectedClips(indices: number[]) {
    selectedClips.value = [...indices]
  }

  function toggleClipSelection(index: number) {
    const pos = selectedClips.value.indexOf(index)
    if (pos > -1) selectedClips.value.splice(pos, 1)
    else selectedClips.value.push(index)
  }

  function selectAllClips() {
    selectedClips.value = Array.from({ length: parsedClips.value.length }, (_, i) => i)
  }

  function deselectAllClips() {
    selectedClips.value = []
  }

  function setParsedMarkupData(data: MarkupData | null) {
    parsedMarkupData.value = data
  }

  function resetMarkupState() {
    parsedClips.value = []
    selectedClips.value = []
    parsedMarkupData.value = null
    activeColorGradingClip.value = null
  }

  // ---------- Color Grading Override Utilities ----------
  interface GradingOverrides { colorGrading?: string; colorGradingState?: ColorGradingState }
  function cloneColorGradingState(state: ColorGradingState): ColorGradingState {
    try {
      if (typeof structuredClone === 'function') return structuredClone(state)
    } catch { /* ignore */ }
    // Fallback
    return JSON.parse(JSON.stringify(state)) as ColorGradingState
  }
  function stripGrading(o: Record<string, unknown> | undefined): void {
    if (!o) return
    delete (o as GradingOverrides).colorGrading
    delete (o as GradingOverrides).colorGradingState
  }
  function clearAllGrading(): void {
    for (const clip of parsedClips.value) stripGrading(clip.overrides as Record<string, unknown>)
    const pm = parsedMarkupData.value as { markerPairs?: Array<{ overrides?: Record<string, unknown> }> } | null
    if (pm?.markerPairs && Array.isArray(pm.markerPairs)) {
      for (const mp of pm.markerPairs) stripGrading(mp.overrides as Record<string, unknown> | undefined)
    }
  }

  watch(selectedFiles, (newVal) => {
    if (!newVal.markup && !newVal.video) {
      clearVideoInfo()
      resetMarkupState()
      previewMountKey.value++
      return
    }
    if (!newVal.video) clearVideoInfo()
    clearAllGrading()
    activeColorGradingClip.value = parsedClips.value.length ? 0 : null
    previewMountKey.value++
  }, { deep: true })

  function setActiveColorGradingClip(index: number | null) {
    if (index === null) { activeColorGradingClip.value = null; return }
    if (index < 0 || index >= parsedClips.value.length) return
    activeColorGradingClip.value = index
  }

  function updateClipColorGrading(clipNumber: number, filterString: string, newState?: ColorGradingState): boolean {
    const targetClip = parsedClips.value.find(c => c.number === clipNumber)
    if (!targetClip) return false
    const resolvedState: ColorGradingState | undefined = newState ? cloneColorGradingState(newState) : (targetClip.overrides as GradingOverrides)?.colorGradingState
    targetClip.overrides = { ...targetClip.overrides, colorGrading: filterString || undefined, colorGradingState: resolvedState }

    const markup = parsedMarkupData.value as { markerPairs?: Array<{ number: number; overrides?: GradingOverrides }> } | null
    if (markup?.markerPairs) {
      const markerPair = markup.markerPairs.find(m => m.number === clipNumber)
      if (markerPair) {
        const mirroredState: ColorGradingState | undefined = newState ? cloneColorGradingState(newState) : markerPair.overrides?.colorGradingState
        markerPair.overrides = { ...markerPair.overrides, colorGrading: filterString || undefined, colorGradingState: mirroredState }
      }
    }
    return true
  }

  function applyColorGradingToAllClips(filter: string, state?: ColorGradingState): number {
    let count = 0
    parsedClips.value.forEach(c => {
      const changed = updateClipColorGrading(c.number, filter, state)
      if (changed) count++
    })
    return count
  }

  function hasValidMarkup(): boolean {
    return parsedClips.value.length > 0 || parsedMarkupData.value !== null
  }

  return {
    // State
    selectedFiles,
    isProcessing,
    isCanceling,
    currentJobId,
    processingStatus,
    processingResult,
    engineStatus,
    parsedClips,
    selectedClips,
    parsedMarkupData,
    activeColorGradingClip,
    videoInfo,
    previewMountKey,

    // Getters
    hasMarkupFile,
    hasVideoFile,
    canProcess,
    hasClips,
    activeSelectedClip,
    currentPreviewClip,
    videoDuration,

    // Actions
    setSelectedFiles,
    setMarkupFile,
    setVideoFile,
    clearSelectedFiles,
    setVideoInfo,
    clearVideoInfo,
    startProcessing,
    getEngineStatus,
    selectFiles,
    parseMarkupFile,
    onProcessingEvent,
    cancelCurrentJob,
    // Clip / markup actions
    setParsedClips,
    setSelectedClips,
    toggleClipSelection,
    selectAllClips,
    deselectAllClips,
    setParsedMarkupData,
    resetMarkupState,
    setActiveColorGradingClip,
    updateClipColorGrading,
    applyColorGradingToAllClips,
    hasValidMarkup
  }
})
