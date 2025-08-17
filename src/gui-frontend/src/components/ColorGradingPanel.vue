<template>
  <div class="color-grading-panel">
    <div class="panel-content">
      <div v-if="!hasVideoAndClip" class="no-content">
        <el-empty description="Select a video file and clip to enable color grading" />
      </div>

      <div v-else class="color-grading-content">
          <!-- Left Column: Preview + Timeline -->
          <div class="preview-timeline-column">
            <!-- Preview Controls -->
            <div class="preview-section">
            <div class="preview-header">
              <h4>Preview</h4>
              <div class="preview-header-right">
                <div v-if="videoInfoDisplay" class="video-info">
                  {{ videoInfoDisplay }}
                </div>
                <div class="preview-controls">
                  <el-select
                    v-model="previewResolution"
                    size="small"
                    style="width: 100px"
                    @change="updatePreview"
                  >
                    <el-option label="10%" :value="0.1" />
                    <el-option label="25%" :value="0.25" />
                    <el-option label="50%" :value="0.5" />
                    <el-option label="100%" :value="1.0" />
                  </el-select>
                  <el-button
                    size="small"
                    @click="updatePreview"
                    :loading="isGeneratingPreview"
                  >
                    Refresh
                  </el-button>
                </div>
              </div>
            </div>

            <div class="preview-container">
              <div v-if="isGeneratingPreview" class="preview-loading">
                <el-icon class="is-loading" :size="24">
                  <Loading />
                </el-icon>
                <p>Generating preview...</p>
              </div>
              <div v-else-if="previewError" class="preview-error">
                <el-alert
                  type="error"
                  :title="previewError"
                  show-icon
                  :closable="false"
                />
              </div>
              <div v-else-if="previewImageUrl" class="preview-image">
                <img
                  :src="previewImageUrl"
                  alt="Color grading preview"
                  @error="handleImageError"
                />
              </div>
              <div v-else class="no-preview">
                <el-empty description="Click refresh to generate preview" />
              </div>
            </div>
          </div>

          <!-- Timeline Scrubber -->
          <div class="timeline-section">
            <div class="timeline-controls">
              <span class="time-display">{{ formatTime(previewTimestamp) }}</span>
              <el-slider
                v-model="previewTimestamp"
                :min="effectiveTimestampRange.min"
                :max="effectiveTimestampRange.max"
                :step="0.1"
                :show-tooltip="false"
                @input="handleTimelineInput"
                class="timeline-slider"
              />
              <span class="time-range">
                  {{ formatTime(effectiveTimestampRange.start) }} - {{ formatTime(effectiveTimestampRange.end) }}
                </span>
              </div>
          </div>
          </div>

          <!-- Color Controls -->
          <div class="color-controls">
            <el-scrollbar height="100%">
              <div class="color-controls-content">
                <h4>Color Adjustments</h4>

            <!-- Brightness -->
            <div class="control-group">
              <div class="control-label">Brightness</div>
              <el-slider
                v-model="brightness"
                :min="-1"
                :max="1"
                :step="0.01"
                @change="updateColorGrading"
                show-input
                input-size="small"
              />
            </div>

            <!-- Contrast -->
            <div class="control-group">
              <div class="control-label">Contrast</div>
              <el-slider
                v-model="contrast"
                :min="0"
                :max="3"
                :step="0.01"
                @change="updateColorGrading"
                show-input
                input-size="small"
              />
            </div>

            <!-- Saturation -->
            <div class="control-group">
              <div class="control-label">Saturation</div>
              <el-slider
                v-model="saturation"
                :min="0"
                :max="3"
                :step="0.01"
                @change="updateColorGrading"
                show-input
                input-size="small"
              />
            </div>

            <!-- Hue -->
            <div class="control-group">
              <div class="control-label">Hue</div>
              <el-slider
                v-model="hue"
                :min="-180"
                :max="180"
                :step="1"
                @change="updateColorGrading"
                show-input
                input-size="small"
              />
            </div>

            <!-- Gamma -->
            <div class="control-group">
              <div class="control-label">Gamma</div>
              <el-slider
                v-model="gamma"
                :min="0.1"
                :max="3"
                :step="0.01"
                @change="updateColorGrading"
                show-input
                input-size="small"
              />
            </div>

            <!-- Filter String Display -->
            <div class="filter-display">
              <el-form-item label="Generated Filter">
                <el-input
                  v-model="generatedFilter"
                  type="textarea"
                  :rows="2"
                  readonly
                  placeholder="Color grading filter will appear here"
                />
              </el-form-item>
            </div>

            <!-- Copy/Paste Controls -->
            <div class="copy-paste-controls">
              <el-button
                size="small"
                @click="copyFilter"
                :disabled="!generatedFilter"
              >
                Copy Filter
              </el-button>
              <el-button
                size="small"
                @click="showPasteDialog"
              >
                Paste Filter
              </el-button>
              <el-button
                size="small"
                @click="resetToDefaults"
              >
                Reset
              </el-button>
            </div>
              </div>
            </el-scrollbar>
          </div>
        </div>
      </div>

    <!-- Paste Filter Dialog -->
    <el-dialog
      v-model="pasteDialogVisible"
      title="Paste Color Grading Filter"
      width="500px"
    >
      <el-input
        v-model="pasteFilterText"
        type="textarea"
        :rows="3"
        placeholder="Paste FFmpeg color grading filter string here"
      />
      <template #footer>
        <el-button @click="pasteDialogVisible = false">Cancel</el-button>
        <el-button type="primary" @click="pasteFilter">Apply</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import type { ClipInfo, VideoInfo } from '@/types/api'

// Simple debounce function
function debounce<T extends (...args: any[]) => any>(func: T, wait: number): T {
  let timeout: ReturnType<typeof setTimeout>
  return ((...args: any[]) => {
    clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }) as T
}

interface Props {
  selectedClip?: ClipInfo | null
  videoPath?: string | null
  videoDuration?: number | null
  videoInfo?: VideoInfo | null
  isProcessing?: boolean
}

interface Emits {
  (e: 'color-grading-changed', clipNumber: number, filter: string): void
}

const props = withDefaults(defineProps<Props>(), {
  selectedClip: null,
  videoPath: null,
  videoDuration: null,
  videoInfo: null,
  isProcessing: false
})

const emit = defineEmits<Emits>()

// State
const previewResolution = ref(0.5)
const previewTimestamp = ref(0)
const isGeneratingPreview = ref(false)
const previewImageUrl = ref('')
const previewError = ref('')

// Color parameters
const brightness = ref(0)
const contrast = ref(1)
const saturation = ref(1)
const hue = ref(0)
const gamma = ref(1)

// Dialog state
const pasteDialogVisible = ref(false)
const pasteFilterText = ref('')

// Computed properties
const hasVideoAndClip = computed(() =>
  !!(props.videoPath && props.selectedClip)
)

// Get the effective timestamp range considering video duration limits
const effectiveTimestampRange = computed(() => {
  if (!props.selectedClip) return { min: 0, max: 60, start: 0, end: 60 }

  const clip = props.selectedClip
  const videoDuration = props.videoDuration

  if (videoDuration && videoDuration > 0) {
    // Constrain clip times to video duration
    const effectiveStart = Math.min(clip.start, videoDuration - 0.1)
    const effectiveEnd = Math.min(clip.end, videoDuration)

    return {
      min: Math.max(0, effectiveStart),
      max: effectiveEnd,
      start: effectiveStart,
      end: effectiveEnd
    }
  }

  // No video duration info - use clip times as-is
  return {
    min: clip.start,
    max: clip.end,
    start: clip.start,
    end: clip.end
  }
})

const generatedFilter = computed(() => {
  const filters = []

  // Build eq filter for brightness, contrast, saturation, gamma
  const eqParams = []
  if (brightness.value !== 0) eqParams.push(`brightness=${brightness.value}`)
  if (contrast.value !== 1) eqParams.push(`contrast=${contrast.value}`)
  if (saturation.value !== 1) eqParams.push(`saturation=${saturation.value}`)
  if (gamma.value !== 1) eqParams.push(`gamma=${gamma.value}`)

  if (eqParams.length > 0) {
    filters.push(`eq=${eqParams.join(':')}`)
  }

  // Add hue filter if needed
  if (hue.value !== 0) {
    filters.push(`hue=h=${hue.value}`)
  }

  return filters.join(',')
})

// Video information display
const videoInfoDisplay = computed(() => {
  if (!props.videoInfo) return null

  const info = props.videoInfo
  const parts = []

  // Original resolution
  if (info.width && info.height) {
    parts.push(`${info.width}×${info.height}`)
  }

  // Preview resolution (if not 100%)
  if (previewResolution.value !== 1.0 && info.width && info.height) {
    const previewWidth = Math.round(info.width * previewResolution.value)
    const previewHeight = Math.round(info.height * previewResolution.value)
    parts.push(`Preview: ${previewWidth}×${previewHeight}`)
  }

  // Frame rate
  if (info.frame_rate) {
    const frameRateStr = formatFrameRate(info.frame_rate)
    parts.push(frameRateStr)
  }

  return parts.length > 0 ? parts.join(' • ') : null
})

const formatFrameRate = (frameRate: string): string => {
  try {
    // Handle common frame rate formats
    if (frameRate.includes('/')) {
      // Fractional format like "30000/1001" or "24/1"
      const [num, den] = frameRate.split('/').map(Number)
      if (den === 1) {
        return `${num}fps`
      } else {
        const fps = num / den
        // Check for common NTSC rates
        if (Math.abs(fps - 23.976) < 0.01) return '23.98fps'
        if (Math.abs(fps - 29.970) < 0.01) return '29.97fps'
        if (Math.abs(fps - 59.940) < 0.01) return '59.94fps'

        // For other fractional rates, show with decimal
        return fps % 1 === 0 ? `${fps}fps` : `${fps.toFixed(2)}fps`
      }
    } else {
      // Simple decimal format
      const fps = parseFloat(frameRate)
      return fps % 1 === 0 ? `${fps}fps` : `${fps.toFixed(2)}fps`
    }
  } catch {
    // If parsing fails, return as-is with fps suffix
    return `${frameRate}fps`
  }
}

// Methods
const resetToDefaults = () => {
  brightness.value = 0
  contrast.value = 1
  saturation.value = 1
  hue.value = 0
  gamma.value = 1
  updateColorGrading()
  updatePreview()
}

// Debounced function for timeline scrubbing
const debouncedUpdatePreview = debounce(() => {
  updatePreview()
}, 300) // 300ms delay

const handleTimelineInput = (value: number) => {
  previewTimestamp.value = value
  debouncedUpdatePreview()
}

const initializeTimestamp = () => {
  if (props.selectedClip) {
    const clip = props.selectedClip
    const videoDuration = props.videoDuration

    // Check if timestamps are valid for the video duration
    if (videoDuration && videoDuration > 0) {
      if (clip.start >= videoDuration) {
        previewTimestamp.value = Math.max(0, videoDuration - 1) // Go to near the end
        previewError.value = `Clip start time (${Math.round(clip.start)}s) exceeds video duration (${Math.round(videoDuration)}s). Using fallback timestamp.`
        return
      }

      if (clip.end > videoDuration) {
        // Start is valid but end exceeds duration - use start time
        previewTimestamp.value = clip.start
        previewError.value = `Clip end time (${Math.round(clip.end)}s) exceeds video duration (${Math.round(videoDuration)}s). Using clip start time.`
        return
      }
    }

    // Normal case - timestamps are within bounds or no duration info
    const clipDuration = clip.end - clip.start
    previewTimestamp.value = clip.start + clipDuration / 2
    previewError.value = '' // Clear any previous errors
  }
}

const updateColorGrading = () => {
  if (!props.selectedClip) return

  const filter = generatedFilter.value
  emit('color-grading-changed', props.selectedClip.number, filter)

  // Auto-update preview with a small delay to debounce rapid changes
  if (updateColorGrading.debounceTimer) {
    clearTimeout(updateColorGrading.debounceTimer)
  }
  updateColorGrading.debounceTimer = setTimeout(() => {
    updatePreview()
  }, 500)
}

// Add debounce timer property to the function
updateColorGrading.debounceTimer = null as number | null

const updatePreview = async () => {
  if (!hasVideoAndClip.value || !window.pywebview?.api) return

  isGeneratingPreview.value = true
  previewError.value = ''

  try {
    const result = await window.pywebview.api.generate_frame_preview(
      props.videoPath!,
      previewTimestamp.value,
      generatedFilter.value || undefined,
      previewResolution.value
    )

    if (result.status === 'success') {
      // Create data URL from base64 image
      if (result.base64_image && result.mime_type) {
        previewImageUrl.value = `data:${result.mime_type};base64,${result.base64_image}`
      } else {
        previewImageUrl.value = ''
      }
    } else {
      previewError.value = result.message || 'Failed to generate preview'
    }
  } catch (error) {
    previewError.value = `Preview generation error: ${error}`
    console.error('Preview generation failed:', error)
  } finally {
    isGeneratingPreview.value = false
  }
}

const handleImageError = () => {
  previewError.value = 'Failed to load preview image'
}

const copyFilter = async () => {
  try {
    await navigator.clipboard.writeText(generatedFilter.value)
    ElMessage.success('Filter copied to clipboard')
  } catch (error) {
    console.error('Failed to copy filter:', error)
    ElMessage.error('Failed to copy filter to clipboard')
  }
}

const showPasteDialog = () => {
  pasteFilterText.value = ''
  pasteDialogVisible.value = true
}

const pasteFilter = () => {
  const filterText = pasteFilterText.value.trim()
  if (!filterText) {
    ElMessage.warning('Please enter a filter string')
    return
  }

  // Try to parse and apply the filter
  try {
    parseAndApplyFilter(filterText)
    pasteDialogVisible.value = false
    ElMessage.success('Filter applied successfully')
    updatePreview()
  } catch (error) {
    ElMessage.error(`Failed to apply filter: ${error}`)
  }
}

const parseAndApplyFilter = (filterString: string) => {
  // Reset values first
  resetToDefaults()

  // Simple parser for common filter formats
  const filters = filterString.split(',')

  for (const filter of filters) {
    const trimmed = filter.trim()

    if (trimmed.startsWith('eq=')) {
      const params = trimmed.substring(3).split(':')
      for (const param of params) {
        const [key, value] = param.split('=')
        const numValue = parseFloat(value)

        switch (key) {
          case 'brightness':
            brightness.value = numValue
            break
          case 'contrast':
            contrast.value = numValue
            break
          case 'saturation':
            saturation.value = numValue
            break
          case 'gamma':
            gamma.value = numValue
            break
        }
      }
    } else if (trimmed.startsWith('hue=h=')) {
      hue.value = parseInt(trimmed.substring(6))
    }
  }

  updateColorGrading()
}

const formatTime = (seconds: number): string => {
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${minutes}:${secs.toFixed(1).padStart(4, '0')}`
}

// Watch for clip changes
watch(() => props.selectedClip, (newClip, oldClip) => {
  if (newClip && newClip !== oldClip) {
    initializeTimestamp()
    updatePreview()
  }
})

// Watch for video path changes
watch(() => props.videoPath, () => {
  if (hasVideoAndClip.value) {
    updatePreview()
  }
})

// Watch for video info changes
watch(() => props.videoInfo, () => {
  // Video info display will automatically update via computed property
})

// Watch for preview resolution changes to update video info display
watch(() => previewResolution.value, () => {
  // Video info display will automatically update via computed property
})

onMounted(() => {
  if (hasVideoAndClip.value) {
    initializeTimestamp()
    updatePreview()
  }
})
</script>

<style scoped>
.color-grading-panel {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  margin: 0 auto;
}

.panel-content {
  padding: 16px;
  height: 100%;
  min-height: 0;
}

/* Responsive layout for larger screens */
@media (min-width: 1024px) {
  .color-grading-content {
    display: grid;
    grid-template-columns: 1fr 300px;
    gap: 20px;
    height: 100%;
  }

  .preview-timeline-column {
    display: flex;
    flex-direction: column;
    gap: 16px;
    height: 100%;
    min-height: 0;
    overflow: hidden;
  }

  .preview-section {
    flex: 1;
    min-height: 0;
    overflow: hidden;
  }

  .preview-container {
    height: 100%;
  }

  .timeline-section {
    flex-shrink: 0;
    max-height: 120px;
  }

  .color-controls {
    height: 100%;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
}

.no-content {
  text-align: center;
  padding: 40px 20px;
  color: var(--el-text-color-secondary);
}

.controls-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.preview-section {
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  padding: 16px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.preview-header h4 {
  margin: 0;
}

.preview-header-right {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8px;
}

.video-info {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  font-family: monospace;
  white-space: nowrap;
}

.preview-controls {
  display: flex;
  gap: 8px;
  align-items: center;
}

.preview-container {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--el-fill-color-lighter);
  border-radius: 4px;
  overflow: hidden;
  height: 100%;
}

.preview-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.preview-image {
  display: contents;
}

.preview-image img {
  max-width: 100%;
  max-height: 100%;
  height: auto;
  width: auto;
  object-fit: contain;
  border-radius: 4px;
}

.timeline-section {
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  padding: 16px;
}

.timeline-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.time-display {
  font-weight: 600;
  min-width: 60px;
  text-align: center;
  font-family: monospace;
}

.timeline-slider {
  flex: 1;
}

.time-range {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  min-width: 120px;
  text-align: right;
  font-family: monospace;
}

.color-controls h4 {
  margin: 0 0 16px 0;
  border-bottom: 1px solid var(--el-border-color);
  padding-bottom: 8px;
}

.control-group {
  margin-bottom: 16px;
}

.control-label {
  font-size: 13px;
  color: var(--el-text-color-regular);
  margin-bottom: 8px;
  font-weight: 500;
}

.filter-display {
  border-top: 1px solid var(--el-border-color);
  padding-top: 16px;
}

.copy-paste-controls {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}
</style>
