<template>
  <div class="preview-timeline-column">
    <div class="preview-section">
      <div class="preview-header">
        <h4 class="preview-title">Preview</h4>
        <div class="preview-header-right">
          <div class="preview-meta">
            <div v-if="videoInfoDisplay" class="video-info" :title="videoInfoDisplay">{{ videoInfoDisplay }}</div>
          </div>
          <div class="preview-controls">
            <el-select v-model="previewResolution" size="small" style="width: 100px" @change="refresh">
              <el-option label="10%" :value="0.1" />
              <el-option label="25%" :value="0.25" />
              <el-option label="50%" :value="0.5" />
              <el-option label="100%" :value="1.0" />
            </el-select>
            <el-button size="small" @click="() => refresh(true)" :loading="isGeneratingPreview">Refresh</el-button>
            <el-button
              v-if="!videoPath && canGenerateFromUrl && !remoteResolvedVideoUrl"
              size="small"
              type="primary"
              :loading="isResolvingRemote || isGeneratingPreview"
              @click="generatePreviewFromUrl"
            >
              {{ isResolvingRemote ? 'Resolving...' : 'Generate from VideoUrl' }}
            </el-button>
            <el-tag
              v-if="remoteResolvedVideoUrl"
              type="success"
              effect="plain"
              size="small"
              style="max-width:160px; overflow:hidden; text-overflow:ellipsis;"
              title="Resolved direct media URL"
            >Resolved URL</el-tag>
          </div>
          <div v-if="remoteResolveError" class="resolve-error"><el-alert type="error" :title="remoteResolveError" show-icon :closable="false" /></div>
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
import { computed } from 'vue'
import { ElAlert, ElButton, ElEmpty, ElIcon, ElSelect, ElOption, ElSlider } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import type { ClipInfo, VideoInfo } from '@/types/api'
import { useFramePreview } from '@/composables/useFramePreview'

interface Props {
  selectedClip?: ClipInfo | null
  videoPath?: string | null
  videoDuration?: number | null
  videoInfo?: VideoInfo | null
  markupVideoUrl?: string | null
  filter?: string | null
  previewEnabled?: boolean
  useStoreFallback?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  selectedClip: null,
  videoPath: null,
  videoDuration: null,
  videoInfo: null,
  markupVideoUrl: null,
  filter: null,
  previewEnabled: true,
  useStoreFallback: true
})

const {
  previewResolution,
  previewTimestamp,
  isGeneratingPreview,
  previewImageUrl,
  previewError,
  hasSomeTimeline,
  timestampRange: effectiveTimestampRange,
  refresh,
  handleTimelineInput,
  enableRemotePreview,
  remotePreviewEnabled,
  resolveRemoteVideoUrl,
  isResolvingRemote,
  remoteResolveError,
  remoteResolvedVideoUrl,
} = useFramePreview({
  markupVideoUrl: () => props.markupVideoUrl,
  filter: () => props.filter || null,
  previewEnabled: () => props.previewEnabled,
})

const canGenerateFromUrl = computed(() => !props.videoPath && !!props.markupVideoUrl)

const formatTime = (seconds: number): string => {
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${minutes}:${secs.toFixed(1).padStart(4, '0')}`
}

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

const getBitDepth = (info: VideoInfo): number | null => {
  const raw = info.bits_per_raw_sample
  if (typeof raw === 'number' && Number.isFinite(raw)) return raw
  if (typeof raw === 'string') {
    const n = Number.parseInt(raw, 10)
    if (Number.isFinite(n)) return n
  }

  // Fall back to parsing ffprobe pixel format strings like "yuv420p10le".
  const pixFmt = info.pix_fmt
  if (typeof pixFmt === 'string' && pixFmt.length) {
    const m = pixFmt.match(/p(\d{2})/i) || pixFmt.match(/(\d{2})(?:le|be)?$/i)
    if (m?.[1]) {
      const n = Number.parseInt(m[1], 10)
      if (Number.isFinite(n)) return n
    }
  }

  return null
}

const isLooseHdr = (info: VideoInfo): boolean => {
  const bitDepth = getBitDepth(info)
  return bitDepth !== null && bitDepth > 8
}

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
  if (isLooseHdr(info)) parts.push('HDR')
  return parts.length ? parts.join(' • ') : null
})

const handleImageError = () => { /* no-op placeholder */ }
const generatePreviewFromUrl = async () => {
  if (!remotePreviewEnabled.value) enableRemotePreview()
  const ok = await resolveRemoteVideoUrl()
  if (ok) refresh(true)
}
</script>

<style scoped>
.preview-timeline-column { display: flex; flex-direction: column; gap: 16px; height: 100%; min-height: 0; overflow: hidden; }
.preview-section { flex: 1; min-height: 0; overflow: hidden; border: 1px solid var(--el-border-color); border-radius: 4px; padding: 8px 12px 12px; }
.preview-container { display: flex; align-items: center; justify-content: center; background: var(--el-fill-color-lighter); border-radius: 4px; overflow: hidden; height: 100%; }
.preview-loading { display: flex; flex-direction: column; align-items: center; gap: 12px; }
.preview-image { display: contents; }
.preview-image img { max-width: 100%; max-height: 100%; height: auto; width: auto; object-fit: contain; border-radius: 4px; }
.timeline-section { border: 1px solid var(--el-border-color); border-radius: 4px; padding: 16px; }
.timeline-controls { display: flex; align-items: center; gap: 12px; width: 100%; }
.time-display { font-weight: 600; min-width: 60px; text-align: center; font-family: monospace; }
.timeline-slider { flex: 1; }
.time-range { color: var(--el-text-color-secondary); font-size: 12px; min-width: 120px; text-align: right; font-family: monospace; }
.preview-header { display: flex; justify-content: space-between; align-items: center; gap: 16px; margin-bottom: 6px; }
.preview-title { margin: 0; font-size: 13px; font-weight: 600; line-height: 1; }
.preview-header-right { display: flex; align-items: center; gap: 16px; flex-wrap: nowrap; min-width: 0; }
.preview-meta { display: flex; align-items: center; gap: 12px; min-width: 0; }
.video-info, .gen-key { font-size: 11px; color: var(--el-text-color-secondary); font-family: monospace; white-space: nowrap; max-width: 260px; overflow: hidden; text-overflow: ellipsis; }
.preview-controls { display: flex; align-items: center; gap: 8px; }
</style>
