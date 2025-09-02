<template>
  <div class="preview-timeline-column">
    <div class="preview-section">
      <div class="preview-header">
        <h4>Preview</h4>
        <div class="preview-header-right">
          <div v-if="videoInfoDisplay" class="video-info">{{ videoInfoDisplay }}</div>
          <div class="preview-controls">
            <el-select v-model="previewResolution" size="small" style="width: 100px" @change="updatePreview">
              <el-option label="10%" :value="0.1" />
              <el-option label="25%" :value="0.25" />
              <el-option label="50%" :value="0.5" />
              <el-option label="100%" :value="1.0" />
            </el-select>
            <el-button size="small" @click="updatePreview" :loading="isGeneratingPreview">Refresh</el-button>
            <el-button v-if="!videoPath && canGenerateFromUrl" size="small" type="primary" :loading="isGeneratingPreview" @click="generatePreviewFromUrl">
              Generate from VideoUrl
            </el-button>
          </div>
        </div>
      </div>

      <div class="preview-container">
        <div v-if="!videoPath && canGenerateFromUrl && !previewImageUrl && !isGeneratingPreview" class="preview-hint">
          <el-alert type="info" title="No local video selected. You can generate a preview using the VideoUrl from the markup." :closable="false" show-icon />
        </div>
        <div v-else-if="isGeneratingPreview" class="preview-loading">
          <el-icon class="is-loading" :size="24"><Loading /></el-icon>
          <p>Generating preview...</p>
        </div>
        <div v-else-if="previewError" class="preview-error">
          <el-alert type="error" :title="previewError" show-icon :closable="false" />
        </div>
        <div v-else-if="previewImageUrl" class="preview-image">
          <img :src="previewImageUrl" alt="Color grading preview" @error="handleImageError" />
        </div>
        <div v-else class="no-preview">
          <el-empty description="Click refresh to generate preview" />
        </div>
      </div>
    </div>

    <div class="timeline-section" v-if="hasSomeTimeline">
      <div class="timeline-controls">
        <span class="time-display">{{ formatTime(previewTimestamp) }}</span>
        <el-slider v-model="previewTimestamp" :min="effectiveTimestampRange.min" :max="effectiveTimestampRange.max" :step="0.1" :show-tooltip="false" @input="handleTimelineInput" class="timeline-slider" />
        <span class="time-range">{{ formatTime(effectiveTimestampRange.start) }} - {{ formatTime(effectiveTimestampRange.end) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { ElAlert, ElButton, ElEmpty, ElIcon, ElSelect, ElOption, ElSlider } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import type { ClipInfo, VideoInfo } from '@/types/api'
import { debounce } from '@/utils/debounce'


interface Props {
  selectedClip?: ClipInfo | null
  videoPath?: string | null
  videoDuration?: number | null
  videoInfo?: VideoInfo | null
  markupVideoUrl?: string | null
  filter?: string | null
  previewEnabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  selectedClip: null,
  videoPath: null,
  videoDuration: null,
  videoInfo: null,
  markupVideoUrl: null,
  filter: null,
  previewEnabled: true
})

// State
const previewResolution = ref(0.5)
const previewTimestamp = ref(0)
const isGeneratingPreview = ref(false)
const previewImageUrl = ref('')
const previewError = ref('')
const previewOpId = ref(0)
const isInitializing = ref(false)
let inFlightKey: string | null = null

const hasSomeTimeline = computed(() => !!props.selectedClip)
const canGenerateFromUrl = computed(() => !!props.markupVideoUrl && !!props.selectedClip)

const effectiveTimestampRange = computed(() => {
  if (!props.selectedClip) return { min: 0, max: 60, start: 0, end: 60 }
  const clip = props.selectedClip
  const videoDuration = props.videoDuration
  if (videoDuration && videoDuration > 0) {
    const effectiveStart = Math.min(clip.start, videoDuration - 0.1)
    const effectiveEnd = Math.min(clip.end, videoDuration)
    return { min: Math.max(0, effectiveStart), max: effectiveEnd, start: effectiveStart, end: effectiveEnd }
  }
  return { min: clip.start, max: clip.end, start: clip.start, end: clip.end }
})

const videoInfoDisplay = computed(() => {
  if (!props.videoInfo) return null
  const info = props.videoInfo
  const parts: string[] = []
  if (info.width && info.height) parts.push(`${info.width}×${info.height}`)
  if (previewResolution.value !== 1.0 && info.width && info.height) {
    const pw = Math.round(info.width * previewResolution.value)
    const ph = Math.round(info.height * previewResolution.value)
    parts.push(`Preview: ${pw}×${ph}`)
  }
  if (info.frame_rate) parts.push(formatFrameRate(info.frame_rate))
  return parts.length ? parts.join(' • ') : null
})

const formatFrameRate = (frameRate: string): string => {
  try {
    if (frameRate.includes('/')) {
      const [n, d] = frameRate.split('/').map(Number)
      if (d === 1) return `${n}fps`
      const fps = n / d
      if (Math.abs(fps - 23.976) < 0.01) return '23.98fps'
      if (Math.abs(fps - 29.970) < 0.01) return '29.97fps'
      if (Math.abs(fps - 59.940) < 0.01) return '59.94fps'
      return fps % 1 === 0 ? `${fps}fps` : `${fps.toFixed(2)}fps`
    }
    const fps = parseFloat(frameRate)
    return fps % 1 === 0 ? `${fps}fps` : `${fps.toFixed(2)}fps`
  } catch { return `${frameRate}fps` }
}

const formatTime = (seconds: number): string => {
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${minutes}:${secs.toFixed(1).padStart(4, '0')}`
}

// Debounced timeline preview
const debouncedUpdatePreview = debounce(() => updatePreview(), 300)
const handleTimelineInput = (v: number | number[]) => {
  const n = Array.isArray(v) ? (v[0] ?? 0) : v
  previewTimestamp.value = n
  debouncedUpdatePreview()
}

const initializeTimestamp = () => {
  if (!props.selectedClip) return
  const clip = props.selectedClip
  const vd = props.videoDuration
  if (vd && vd > 0) {
    if (clip.start >= vd) { previewTimestamp.value = Math.max(0, vd - 1); previewError.value = `Clip start time (${Math.round(clip.start)}s) exceeds video duration (${Math.round(vd)}s). Using fallback timestamp.`; return }
    if (clip.end > vd) { previewTimestamp.value = clip.start; previewError.value = `Clip end time (${Math.round(clip.end)}s) exceeds video duration (${Math.round(vd)}s). Using clip start time.`; return }
  }
  const clipDuration = clip.end - clip.start
  previewTimestamp.value = clip.start + clipDuration / 2
  previewError.value = ''
}

const updatePreview = async () => {
  if (!hasSomeTimeline.value || !window.pywebview?.api) return
  if (isInitializing.value) return
  const opId = ++previewOpId.value
  isGeneratingPreview.value = true
  previewError.value = ''

  try {
    const filterToApply = props.previewEnabled ? (props.filter || undefined) : undefined
    const videoSource = props.videoPath || tempVideoUrlRef.value
    if (!videoSource) { isGeneratingPreview.value = false; return }

    const tsKey = Number(previewTimestamp.value.toFixed(3))
    const filterKey = props.previewEnabled ? (props.filter || '') : 'nofilter'
    const key = [videoSource, tsKey, previewResolution.value, filterKey].join('|')
    if (inFlightKey === key) { isGeneratingPreview.value = false; return }
    inFlightKey = key

    const result = await window.pywebview.api.generate_frame_preview(
      videoSource, previewTimestamp.value, filterToApply, previewResolution.value
    )

    if (opId !== previewOpId.value) return
    if (result.status === 'success') {
      if (result.base64_image && result.mime_type) previewImageUrl.value = `data:${result.mime_type};base64,${result.base64_image}`
      else previewImageUrl.value = ''
    } else {
      previewError.value = result.message || 'Failed to generate preview'
    }
  } catch (e) {
    if (opId !== previewOpId.value) return
    previewError.value = `Preview generation error: ${String(e)}`
    console.error('Preview generation failed:', e)
  } finally {
    if (opId === previewOpId.value) { inFlightKey = null; isGeneratingPreview.value = false }
  }
}

const handleImageError = () => { previewError.value = 'Failed to load preview image' }

const tempVideoUrlRef = ref<string | null>(null)
const generatePreviewFromUrl = async () => {
  if (!props.markupVideoUrl || !window.pywebview?.api) return
  try {
    const opId = ++previewOpId.value
    isGeneratingPreview.value = true
    previewError.value = ''
    const res = await window.pywebview.api.get_direct_video_url(props.markupVideoUrl)
    if (opId !== previewOpId.value) return
    if (res.status === 'success' && res.url) {
      tempVideoUrlRef.value = res.url as string
      await updatePreview()
    } else {
      previewError.value = res.message || 'Failed to resolve VideoUrl via yt-dlp'
    }
  } catch (e) {
    previewError.value = `Failed to fetch direct video URL: ${String(e)}`
  } finally {
    isGeneratingPreview.value = false
  }
}

// Consolidated watcher for clip/video/duration
let initTimer: number | null = null
watch(
  () => ({ clipNumber: props.selectedClip?.number ?? null, videoPath: props.videoPath ?? null, duration: props.videoDuration ?? null }),
  async (curr, prev) => {
    if (prev && curr.videoPath !== prev.videoPath) {
      isInitializing.value = true
      previewOpId.value++
      if (initTimer) { clearTimeout(initTimer); initTimer = null }
      previewImageUrl.value = ''
      previewError.value = ''
      previewTimestamp.value = 0
      isGeneratingPreview.value = false
      return
    }
    if (!hasSomeTimeline.value) {
      previewOpId.value++
      isGeneratingPreview.value = false
      previewImageUrl.value = ''
      previewError.value = ''
      return
    }
    if (initTimer) clearTimeout(initTimer)
    initTimer = window.setTimeout(async () => {
      await nextTick()
      initializeTimestamp()
      isInitializing.value = false
      updatePreview()
    }, 200)
  },
  { immediate: true, deep: false }
)

// React to filter changes with debounce to avoid spamming during drag
const debouncedFilterPreview = debounce(() => { if (!isInitializing.value) updatePreview() }, 150)
watch(() => [props.filter, props.previewEnabled, previewResolution.value], () => {
  debouncedFilterPreview()
})
</script>

<style scoped>
.preview-timeline-column { display: flex; flex-direction: column; gap: 16px; height: 100%; min-height: 0; overflow: hidden; }
.preview-section { flex: 1; min-height: 0; overflow: hidden; border: 1px solid var(--el-border-color); border-radius: 4px; padding: 16px; }
.preview-container { display: flex; align-items: center; justify-content: center; background: var(--el-fill-color-lighter); border-radius: 4px; overflow: hidden; height: 100%; }
.preview-loading { display: flex; flex-direction: column; align-items: center; gap: 12px; }
.preview-image { display: contents; }
.preview-image img { max-width: 100%; max-height: 100%; height: auto; width: auto; object-fit: contain; border-radius: 4px; }
.timeline-section { border: 1px solid var(--el-border-color); border-radius: 4px; padding: 16px; }
.timeline-controls { display: flex; align-items: center; gap: 12px; width: 100%; }
.time-display { font-weight: 600; min-width: 60px; text-align: center; font-family: monospace; }
.timeline-slider { flex: 1; }
.time-range { color: var(--el-text-color-secondary); font-size: 12px; min-width: 120px; text-align: right; font-family: monospace; }
.preview-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.preview-header-right { display: flex; flex-direction: row; align-items: center; gap: 8px; }
.video-info { font-size: 12px; color: var(--el-text-color-secondary); font-family: monospace; white-space: nowrap; }
</style>
