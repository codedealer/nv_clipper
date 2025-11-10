import { ref, computed, watch } from 'vue'
import { defineStore } from 'pinia'
import type { SelectedFiles, ProcessingResult, EngineStatus, ParseMarkupResult, JobStatus, ClipInfo } from '@/types/api'
import type { ColorGradingState } from '@/types/colorGrading'
import type { ClipSettingsState, ClipSettingsOverrides, ClipSettingsUpdatePayload } from '@/types/clipSettings'
import { waitForPywebview } from '@/utils/api'
import { useSettingsStore } from './settings'
import { ElMessage } from 'element-plus'
import type { MarkupData } from '@/utils/markup'

const CLIP_SETTINGS_KEYS: (keyof ClipSettingsOverrides)[] = [
  'loop',
  'minterpMode',
  'minterpProvider',
  'mirror',
  'videoStabilization',
  'videoStabilizationDynamicZoom',
  'videoStabilizationRollingShutter',
  'videoStabilizationJitteryMotion',
  'videoEnhancementEnabled',
  'videoEnhancementModel',
  'videoEnhancementCompression',
  'videoEnhancementDetails',
  'videoEnhancementBlur',
  'videoEnhancementNoise',
  'videoEnhancementHalo',
  'videoEnhancementPreblur',
  'videoEnhancementBlend',
  'videoEnhancementPrenoise'
]

function cloneSimple<T>(value: T): T {
  if (value === undefined || value === null) return value
  if (typeof structuredClone === 'function') {
    try {
      return structuredClone(value)
    } catch { /* fallback to JSON */ }
  }
  try {
    return JSON.parse(JSON.stringify(value)) as T
  } catch {
    return value
  }
}

function cloneClipSettingsOverrides(overrides: ClipSettingsOverrides): ClipSettingsOverrides {
  const result: ClipSettingsOverrides = {}
  for (const key of CLIP_SETTINGS_KEYS) {
    const rawValue = (overrides as Record<string, unknown>)[key as string]
    if (rawValue !== undefined) {
      ;(result as Record<string, unknown>)[key as string] = typeof rawValue === 'object' && rawValue !== null ? cloneSimple(rawValue) : rawValue
    }
  }
  return result
}

function cloneClipSettingsState(state: ClipSettingsState): ClipSettingsState {
  return {
    speed: state.speed,
    overrides: cloneClipSettingsOverrides(state.overrides),
    effectiveOverrides: cloneClipSettingsOverrides(state.effectiveOverrides)
  }
}

function deepEqual(a: unknown, b: unknown): boolean {
  if (a === b) return true
  if (typeof a !== typeof b) return false
  if (a === null || b === null) return false
  if (Array.isArray(a) && Array.isArray(b)) {
    if (a.length !== b.length) return false
    for (let i = 0; i < a.length; i++) {
      if (!deepEqual(a[i], b[i])) return false
    }
    return true
  }
  if (typeof a === 'object' && typeof b === 'object') {
    const aObj = a as Record<string, unknown>
    const bObj = b as Record<string, unknown>
    const aKeys = Object.keys(aObj)
    const bKeys = Object.keys(bObj)
    if (aKeys.length !== bKeys.length) return false
    for (const key of aKeys) {
      if (!deepEqual(aObj[key], bObj[key])) return false
    }
    return true
  }
  return false
}

function normalizeOverrides(overrides: ClipSettingsOverrides): Record<string, unknown> {
  const normalized: Record<string, unknown> = {}
  for (const key of CLIP_SETTINGS_KEYS) {
    const value = (overrides as Record<string, unknown>)[key as string]
    if (value !== undefined) {
      normalized[key as string] = typeof value === 'object' && value !== null ? cloneSimple(value) : value
    }
  }
  return normalized
}

function areClipSettingsEqual(a: ClipSettingsState, b: ClipSettingsState): boolean {
  if (Math.abs((a.speed ?? 0) - (b.speed ?? 0)) > 1e-6) return false
  return deepEqual(normalizeOverrides(a.overrides), normalizeOverrides(b.overrides))
}

function extractClipSettingsStateFromClip(clip: ClipInfo, defaults: ClipSettingsOverrides): ClipSettingsState {
  const baseOverrides = (clip.overrides || {}) as Record<string, unknown>
  const overrides: ClipSettingsOverrides = {}
  const effective: ClipSettingsOverrides = {}
  const defaultsRecord = defaults as Record<string, unknown>
  for (const key of CLIP_SETTINGS_KEYS) {
    const value = baseOverrides[key as string]
    if (value !== undefined) {
      const cloned = typeof value === 'object' && value !== null ? cloneSimple(value) : value
      ;(overrides as Record<string, unknown>)[key as string] = cloned
      ;(effective as Record<string, unknown>)[key as string] = cloned
      continue
    }
    const inherited = defaultsRecord[key as string]
    if (inherited !== undefined) {
      ;(effective as Record<string, unknown>)[key as string] = typeof inherited === 'object' && inherited !== null ? cloneSimple(inherited) : inherited
    }
  }
  return {
    speed: typeof clip.speed === 'number' ? clip.speed : 1,
    overrides,
    effectiveOverrides: effective
  }
}

function buildClipSettingsSnapshot(clips: ClipInfo[], defaults: ClipSettingsOverrides): Record<number, ClipSettingsState> {
  const snapshot: Record<number, ClipSettingsState> = {}
  for (const clip of clips) {
    if (typeof clip.number === 'number') {
      snapshot[clip.number] = cloneClipSettingsState(extractClipSettingsStateFromClip(clip, defaults))
    }
  }
  return snapshot
}

function extractGlobalClipDefaults(markup: MarkupData | null): ClipSettingsOverrides {
  const defaults: ClipSettingsOverrides = {}
  if (!markup) return defaults
  const record = markup as unknown as Record<string, unknown>
  for (const key of CLIP_SETTINGS_KEYS) {
    const rawValue = record[key as string]
    if (rawValue !== undefined) {
      ;(defaults as Record<string, unknown>)[key as string] = typeof rawValue === 'object' && rawValue !== null ? cloneSimple(rawValue) : rawValue
    }
  }
  return defaults
}

function applyOverrideChanges(target: Record<string, unknown>, changes: Partial<ClipSettingsOverrides>): Record<string, unknown> {
  const updated = { ...target }
  for (const [rawKey, rawValue] of Object.entries(changes) as [keyof ClipSettingsOverrides, unknown][]) {
    const key = rawKey as string
    const value = rawValue as unknown
    if (value === null || value === undefined || (typeof value === 'string' && value === '')) {
      delete updated[key]
      continue
    }
    if (typeof value === 'object' && value !== null) {
      updated[key] = cloneSimple(value)
    } else {
      updated[key] = value
    }
  }
  return updated
}

function pruneBooleanOverrides(
  overrides: Record<string, unknown>,
  baseline: ClipSettingsOverrides | undefined,
  defaults: ClipSettingsOverrides
): Record<string, unknown> {
  const baselineRecord = baseline ? { ...(baseline as Record<string, unknown>) } : {}
  const defaultsRecord = defaults ? { ...(defaults as Record<string, unknown>) } : {}
  const pruned: Record<string, unknown> = {}
  for (const [key, value] of Object.entries(overrides)) {
    if (
      typeof value === 'boolean' &&
      value === false &&
      !(key in baselineRecord) &&
      (!defaultsRecord[key] || defaultsRecord[key] === false)
    ) {
      continue
    }
    pruned[key] = value
  }
  return pruned
}

function pruneOverridesMatchingDefaults(
  overrides: Record<string, unknown>,
  defaults: ClipSettingsOverrides
): Record<string, unknown> {
  if (!defaults || Object.keys(defaults).length === 0) return overrides
  const defaultsRecord = defaults as Record<string, unknown>
  const result: Record<string, unknown> = {}
  for (const [key, value] of Object.entries(overrides)) {
    const defaultValue = defaultsRecord[key]
    if (defaultValue !== undefined && deepEqual(value, defaultValue)) {
      continue
    }
    result[key] = value
  }
  return result
}

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
  const originalClipSettings = ref<Record<number, ClipSettingsState>>({})
  const clipSettingsDirty = ref<Record<number, boolean>>({})

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
    parsedClips.value = clips.map(clip => ({
      ...clip,
      overrides: { ...(clip.overrides || {}) }
    }))
    selectedClips.value = clips.map((_, i) => i)
    activeColorGradingClip.value = clips.length ? 0 : null
    const defaults = extractGlobalClipDefaults(parsedMarkupData.value)
    originalClipSettings.value = buildClipSettingsSnapshot(parsedClips.value, defaults)
    clipSettingsDirty.value = {}
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
    if (!parsedClips.value.length) return
    const defaults = extractGlobalClipDefaults(parsedMarkupData.value)
    originalClipSettings.value = buildClipSettingsSnapshot(parsedClips.value, defaults)
    const dirtyMap: Record<number, boolean> = {}
    for (const clip of parsedClips.value) {
      if (typeof clip.number !== 'number') continue
      const current = cloneClipSettingsState(extractClipSettingsStateFromClip(clip, defaults))
      const baseline = originalClipSettings.value[clip.number]
      if (current && baseline && !areClipSettingsEqual(current, baseline)) {
        dirtyMap[clip.number] = true
      }
    }
    clipSettingsDirty.value = dirtyMap
  }

  function resetMarkupState() {
    parsedClips.value = []
    selectedClips.value = []
    parsedMarkupData.value = null
    activeColorGradingClip.value = null
    originalClipSettings.value = {}
    clipSettingsDirty.value = {}
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

  function findMarkerPair(clipNumber: number) {
    const markup = parsedMarkupData.value as { markerPairs?: Array<{ number: number; speed?: number; overrides?: Record<string, unknown> }> } | null
    if (!markup?.markerPairs) return null
    return markup.markerPairs.find(mp => mp.number === clipNumber) || null
  }

  function getClipSettingsState(clipNumber: number): ClipSettingsState | null {
    const clip = parsedClips.value.find(c => c.number === clipNumber)
    if (!clip) return null
    const defaults = extractGlobalClipDefaults(parsedMarkupData.value)
    return cloneClipSettingsState(extractClipSettingsStateFromClip(clip, defaults))
  }

  function getOriginalClipSettingsState(clipNumber: number): ClipSettingsState | null {
    const original = originalClipSettings.value[clipNumber]
    if (!original) return null
    return cloneClipSettingsState(original)
  }

  function syncClipSettingsDirtyFlag(clipNumber: number) {
    const current = getClipSettingsState(clipNumber)
    const baseline = originalClipSettings.value[clipNumber]
    if (!current || !baseline) {
      const rest = { ...clipSettingsDirty.value }
      delete rest[clipNumber]
      clipSettingsDirty.value = rest
      return
    }
    const dirty = !areClipSettingsEqual(current, baseline)
    clipSettingsDirty.value = { ...clipSettingsDirty.value, [clipNumber]: dirty }
  }

  function updateClipSettings(clipNumber: number, payload: ClipSettingsUpdatePayload): boolean {
    const clipIndex = parsedClips.value.findIndex(c => c.number === clipNumber)
    if (clipIndex === -1) return false

    const existingClip = parsedClips.value[clipIndex]
    const baseline = originalClipSettings.value[clipNumber]
    const globalDefaults = extractGlobalClipDefaults(parsedMarkupData.value)

    let nextSpeed = existingClip.speed
    if (payload.speed !== undefined) {
      if (payload.speed === null && baseline) {
        nextSpeed = baseline.speed
      } else if (payload.speed !== null) {
        nextSpeed = payload.speed
      }
    }

    const currentOverrides = { ...(existingClip.overrides || {}) }
    const overridesChanges = payload.overrides as Partial<ClipSettingsOverrides> | undefined
    const nextOverrides = overridesChanges ? applyOverrideChanges(currentOverrides, overridesChanges) : currentOverrides
  const booleanPruned = pruneBooleanOverrides(nextOverrides, baseline?.overrides, globalDefaults)
    const prunedOverrides = pruneOverridesMatchingDefaults(booleanPruned, globalDefaults)

    const updatedClip: ClipInfo = {
      ...existingClip,
      speed: nextSpeed,
      overrides: prunedOverrides
    }
    parsedClips.value.splice(clipIndex, 1, updatedClip)

    const markerPair = findMarkerPair(clipNumber)
    if (markerPair) {
      if (payload.speed !== undefined) {
        markerPair.speed = nextSpeed
      }
      if (overridesChanges) {
        const existingOverrides = markerPair.overrides || {}
        const mergedOverrides = applyOverrideChanges(existingOverrides, overridesChanges)
  const mergedBooleanPruned = pruneBooleanOverrides(mergedOverrides, baseline?.overrides, globalDefaults)
        markerPair.overrides = pruneOverridesMatchingDefaults(mergedBooleanPruned, globalDefaults) as Record<string, unknown>
      }
    }

    syncClipSettingsDirtyFlag(clipNumber)
    return true
  }

  function resetClipSettings(clipNumber: number): boolean {
    const baseline = originalClipSettings.value[clipNumber]
    if (!baseline) return false

    const clipIndex = parsedClips.value.findIndex(c => c.number === clipNumber)
    if (clipIndex === -1) return false

    const existingClip = parsedClips.value[clipIndex]
    const currentOverrides = { ...(existingClip.overrides || {}) }
    const baselineOverrides = baseline.overrides

    for (const key of CLIP_SETTINGS_KEYS) {
      const raw = (baselineOverrides as Record<string, unknown>)[key as string]
      if (raw === undefined) {
        delete currentOverrides[key as string]
      } else {
        currentOverrides[key as string] = typeof raw === 'object' && raw !== null ? cloneSimple(raw) : raw
      }
    }

    const updatedClip: ClipInfo = {
      ...existingClip,
      speed: baseline.speed,
      overrides: currentOverrides
    }
    parsedClips.value.splice(clipIndex, 1, updatedClip)

    const markerPair = findMarkerPair(clipNumber)
    if (markerPair) {
      markerPair.speed = baseline.speed
      const existingOverrides = markerPair.overrides || {}
      const nextOverrides: Record<string, unknown> = { ...existingOverrides }
      for (const key of CLIP_SETTINGS_KEYS) {
        const raw = (baselineOverrides as Record<string, unknown>)[key as string]
        if (raw === undefined) {
          delete nextOverrides[key as string]
        } else {
          nextOverrides[key as string] = typeof raw === 'object' && raw !== null ? cloneSimple(raw) : raw
        }
      }
      markerPair.overrides = nextOverrides
    }

    syncClipSettingsDirtyFlag(clipNumber)
    return true
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
  clipSettingsDirty,

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
    updateClipSettings,
    resetClipSettings,
    getClipSettingsState,
    getOriginalClipSettingsState,
    hasValidMarkup
  }
})
