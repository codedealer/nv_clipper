import { ref, computed, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useClipperStore } from '@/stores/counter'
import { debounce } from '@/utils/debounce'

export interface UseFramePreviewOptions {
  filter?: string | (() => string | null | undefined) | null
  previewEnabled?: boolean | (() => boolean | undefined)
  markupVideoUrl?: string | (() => string | null | undefined) | null
  resolution?: number
}

function resolveMaybeFn<T>(v: T | (() => T)): T {
  return typeof v === 'function' ? (v as () => T)() : v
}

export function useFramePreview(opts: UseFramePreviewOptions = {}) {
  const store = useClipperStore()
  const { activeSelectedClip, selectedFiles, videoDuration: storeVideoDuration } = storeToRefs(store)

  // Base reactive state
  const previewResolution = ref(opts.resolution ?? 0.5)
  const previewTimestamp = ref(0)
  const effectiveTimestamp = ref(0)
  const isGeneratingPreview = ref(false)
  const previewImageUrl = ref('')
  const previewError = ref('')
  const remoteResolveError = ref('')
  const refreshNonce = ref(0)

  // Authoritative clip + video path + duration
  const clip = computed(() => activeSelectedClip.value)
  const localVideoPath = computed(() => selectedFiles.value.video || null)
  const duration = computed(() => storeVideoDuration.value || null)

  // Remote URL handling (explicit enable + resolution)
  const remotePreviewEnabled = ref(false)
  const remoteResolvedVideoUrl = ref<string | null>(null)
  const isResolvingRemote = ref(false)
  const markupUrl = computed(() => {
    const raw = opts.markupVideoUrl
    if (!raw) return null
    return resolveMaybeFn(raw) || null
  })
  function enableRemotePreview() { if (markupUrl.value) remotePreviewEnabled.value = true }
  async function resolveRemoteVideoUrl(): Promise<boolean> {
    remoteResolveError.value = ''
    if (!markupUrl.value) { remoteResolveError.value = 'No markup URL available'; return false }
    if (!remotePreviewEnabled.value) enableRemotePreview()
    if (remoteResolvedVideoUrl.value) return true
    try {
      isResolvingRemote.value = true
      const res = await window.pywebview?.api?.get_direct_video_url?.(markupUrl.value)
      if (!res || res.status !== 'success' || !res.url) { remoteResolveError.value = res?.message || 'Failed to resolve direct URL'; return false }
      if (!/^https?:\/\//i.test(res.url)) { remoteResolveError.value = 'Resolved URL not http(s)'; return false }
      remoteResolvedVideoUrl.value = res.url
      refreshNonce.value++
      return true
    } catch (e) {
      remoteResolveError.value = `Resolve error: ${String(e)}`
      return false
    } finally {
      isResolvingRemote.value = false
    }
  }

  const effectiveVideoPath = computed(() => {
    if (localVideoPath.value) return localVideoPath.value
    if (remotePreviewEnabled.value && remoteResolvedVideoUrl.value) return remoteResolvedVideoUrl.value
    return null
  })

  // Preview enabled indicates whether to apply filter; when disabled we still generate base frame (original video)
  const enabled = computed(() => {
    if (opts.previewEnabled == null) return true
    return !!resolveMaybeFn(opts.previewEnabled as boolean | (() => boolean | undefined))
  })
  const filter = computed(() => {
    if (!opts.filter) return null
    const raw = resolveMaybeFn(opts.filter as string | (() => string | null | undefined) | null)
    return enabled.value ? raw : null
  })

  const hasTimeline = computed(() => !!clip.value || (duration.value != null && duration.value > 0))
  const timestampRange = computed(() => {
    if (clip.value) {
      const c = clip.value
      const vd = duration.value
      if (vd && vd > 0) {
        const start = Math.min(c.start, Math.max(0, vd - 0.1))
        const end = Math.min(c.end, vd)
        return { min: Math.max(0, start), max: end, start, end }
      }
      return { min: c.start, max: c.end, start: c.start, end: c.end }
    }
    const vd = duration.value
    if (vd && vd > 0) return { min: 0, max: vd, start: 0, end: vd }
    return { min: 0, max: 0, start: 0, end: 0 }
  })

  // Clamp timestamp when clip or duration changes
  watch([clip, duration], () => {
    const r = timestampRange.value
    if (r.max <= r.min) { previewTimestamp.value = 0; return }
    if (previewTimestamp.value < r.min || previewTimestamp.value > r.max) {
      previewTimestamp.value = r.start + (r.end - r.start) / 2
    }
  }, { immediate: true })

  // Debounce slider changes
  const commitEffectiveTs = debounce(() => { effectiveTimestamp.value = Number(previewTimestamp.value.toFixed(3)) }, 200)
  watch(() => previewTimestamp.value, () => { if (hasTimeline.value) commitEffectiveTs() })

  // Reset both timestamps to clip midpoint on clip or duration change
  watch([clip, duration], () => {
    const r = timestampRange.value
    if (r.max <= r.min) { previewTimestamp.value = 0; effectiveTimestamp.value = 0; previewImageUrl.value=''; return }
    const mid = r.start + (r.end - r.start) / 2
    previewTimestamp.value = mid
    effectiveTimestamp.value = mid
    refreshNonce.value++
  }, { immediate: true })

  // Parameter change retrigger
  watch([effectiveVideoPath, filter, previewResolution], () => {
    effectiveTimestamp.value = Number(previewTimestamp.value.toFixed(3))
    refreshNonce.value++
  })

  // Generation key (debug / dedupe marker)
  const generationKey = computed(() => {
    const vs = effectiveVideoPath.value || ''
    const c = clip.value
    const clipPart = c ? `${c.number}:${c.start}:${c.end}` : 'global'
    const ts = (effectiveTimestamp.value || previewTimestamp.value || 0).toFixed(3)
    const filt = filter.value || ''
    const res = previewResolution.value
    const en = enabled.value ? '1' : '0'
    return `${en}|${vs}|${clipPart}|${ts}|${filt}|${res}|n${refreshNonce.value}`
  })

  // Preview generation
  watch(generationKey, async (k) => {
  const vs = effectiveVideoPath.value
  if (!vs) { previewImageUrl.value=''; previewError.value=''; return }
    const rawTs = effectiveTimestamp.value || previewTimestamp.value || 0
    const ts = Number(rawTs.toFixed(3))
    isGeneratingPreview.value = true
    previewError.value = ''
    try {
      const res = await window.pywebview?.api?.generate_frame_preview?.(vs, ts, filter.value || undefined, previewResolution.value, undefined)
      if (generationKey.value !== k) return // stale
      if (!res || res.status !== 'success' || !res.base64_image) {
        previewError.value = res?.message || 'Failed to generate preview'
        previewImageUrl.value = ''
        return
      }
      previewImageUrl.value = `data:${res.mime_type || 'image/jpeg'};base64,${res.base64_image}`
    } catch (e) {
      previewError.value = `Preview error: ${String(e)}`
      previewImageUrl.value = ''
    } finally {
      if (generationKey.value === k) isGeneratingPreview.value = false
    }
  }, { immediate: true })

  function handleTimelineInput(v: number | number[]) {
    const n = Array.isArray(v) ? (v[0] ?? 0) : v
    previewTimestamp.value = n
  }
  function refresh(forceMidpoint = false) {
    if (forceMidpoint) {
      const r = timestampRange.value
      if (r.max > r.min) {
        const mid = r.start + (r.end - r.start) / 2
        previewTimestamp.value = mid
        effectiveTimestamp.value = mid
        refreshNonce.value++
        return
      }
    }
    effectiveTimestamp.value = Number(previewTimestamp.value.toFixed(3))
    refreshNonce.value++
  }

  return {
    // State
    previewResolution,
    previewTimestamp,
    isGeneratingPreview,
    previewImageUrl,
    previewError,
    hasSomeTimeline: hasTimeline,
    timestampRange,
    // Controls
    handleTimelineInput,
    refresh,
    enableRemotePreview,
    resolveRemoteVideoUrl,
    remotePreviewEnabled,
    isResolvingRemote,
    remoteResolveError,
    remoteResolvedVideoUrl,
    generationKey, // optional debug
  }
}

