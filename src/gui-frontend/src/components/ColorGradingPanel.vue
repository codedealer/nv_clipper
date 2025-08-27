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
                :min="-0.5"
                :max="0.5"
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

            <!-- Filter Output & Controls Card -->
            <div class="filter-output-card">
              <div class="filter-card-header">
                <h5>Generated Filter</h5>
                <div class="filter-header-controls">
                  <el-checkbox
                    v-model="previewEnabled"
                    @change="updatePreview"
                    size="small"
                  >
                    Preview
                  </el-checkbox>
                </div>
              </div>

              <div class="filter-display">
                <el-input
                  v-model="generatedFilter"
                  type="textarea"
                  :rows="2"
                  readonly
                  placeholder="Color grading filter will appear here"
                  class="filter-textarea"
                />
              </div>

              <div class="filter-actions">
                <div class="action-group primary-actions">
                  <el-button
                    size="small"
                    type="primary"
                    @click="copyFilter"
                    :disabled="!generatedFilter"
                    plain
                  >
                    <el-icon><DocumentCopy /></el-icon>
                    Copy Filter
                  </el-button>
                  <el-button
                    size="small"
                    @click="showPasteDialog"
                    plain
                  >
                    <el-icon><Document /></el-icon>
                    Paste Filter
                  </el-button>
                </div>

                <div class="action-group secondary-actions">
                  <el-button
                    size="small"
                    type="success"
                    @click="copyToAllClips"
                    :disabled="!generatedFilter || isMockMarkup"
                    plain
                    v-if="!isMockMarkup"
                  >
                    <el-icon><CopyDocument /></el-icon>
                    Copy to All Clips
                  </el-button>
                  <el-button
                    size="small"
                    type="warning"
                    @click="handleReset"
                    plain
                  >
                    <el-icon><RefreshLeft /></el-icon>
                    Reset
                  </el-button>
                </div>
              </div>
            </div>
              </div>
            </el-scrollbar>
          </div>
        </div>
      </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading, DocumentCopy, Document, CopyDocument, RefreshLeft } from '@element-plus/icons-vue'
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
  isMockMarkup?: boolean
  getClipColorGrading?: (clipNumber: number) => string | undefined
}

interface Emits {
  (e: 'color-grading-changed', clipNumber: number, filter: string): void
  (e: 'copy-to-all-clips', filter: string): void
}

const props = withDefaults(defineProps<Props>(), {
  selectedClip: null,
  videoPath: null,
  videoDuration: null,
  videoInfo: null,
  isProcessing: false,
  isMockMarkup: false,
  getClipColorGrading: undefined
})

const emit = defineEmits<Emits>()

// State
const previewResolution = ref(0.5)
const previewTimestamp = ref(0)
const isGeneratingPreview = ref(false)
const previewImageUrl = ref('')
const previewError = ref('')
const previewEnabled = ref(true)
// Guard to suppress preview during re-init on video change
const isInitializing = ref(false)

// Color parameters
const brightness = ref(0)
const contrast = ref(1)
const saturation = ref(1)
const hue = ref(0)
const gamma = ref(1)

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

  // Build hue filter for saturation, brightness, and hue adjustments
  // This is preferred for Topaz AI custom FFmpeg builds that don't include eq filter
  const hueParams = []

  // Convert brightness from [-1, 1] range to hue filter's [-10, 10] range
  if (brightness.value !== 0) {
    // Scale the brightness value: UI range [-1,1] maps to hue filter range [-10,10]
    const hueBrightness = brightness.value * 10
    hueParams.push(`b=${hueBrightness}`)
  }

  // Convert saturation from [0, 3] UI range to hue filter's saturation parameter
  if (saturation.value !== 1) {
    // The hue filter's 's' parameter defaults to 1 (normal saturation)
    // We map our UI range [0,3] to roughly match eq filter behavior
    // UI: 0 (no sat) -> hue: 0, UI: 1 (normal) -> hue: 1, UI: 3 (max) -> hue: 3
    const hueSaturation = saturation.value
    hueParams.push(`s=${hueSaturation.toFixed(2)}`)
  }

  // Add hue adjustment if needed
  if (hue.value !== 0) {
    hueParams.push(`h=${hue.value}`)
  }

  if (hueParams.length > 0) {
    filters.push(`hue=${hueParams.join(':')}`)
  }

  // Gamma via lutyuv
  if (gamma.value !== 1) {
    // Use inverse so UI gamma > 1 brightens, < 1 darkens
    const uiG = Math.max(0.1, Math.min(10, Number(gamma.value.toFixed(3))))
    const g = Number((1 / uiG).toFixed(6))
    filters.push(`lutyuv=y=gammaval(${g})`)
  }

  // Contrast via lutyuv on luma around mid-gray (bit-depth agnostic)
  if (contrast.value !== 1) {
    const c = Number(contrast.value.toFixed(3))
    const expr = `y='min(max((val-(maxval+minval)/2)*${c}+(maxval+minval)/2,minval),maxval)'`
    filters.push(`lutyuv=${expr}`)
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
const handleReset = () => {
  resetToDefaults()
  updateColorGrading()
  updatePreview()
}

const loadClipColorGrading = () => {
  if (!props.selectedClip) {
    resetToDefaults()
    return
  }

  // Get existing color grading filter for this clip
  let existingFilter: string | undefined

  // Use the provided method if available, otherwise fall back to clip data
  if (props.getClipColorGrading) {
    existingFilter = props.getClipColorGrading(props.selectedClip.number)
  } else {
    existingFilter = props.selectedClip.overrides?.colorGrading as string | undefined
  }

  if (existingFilter && existingFilter.trim()) {
    // Parse the existing filter to populate controls (without triggering updates)
    try {
      parseFilterToControls(existingFilter)
    } catch (error) {
      console.error('Failed to parse existing color grading filter:', error)
      resetToDefaults()
    }
  } else {
    // No existing filter - reset to defaults
    resetToDefaults()
  }
}

const resetToDefaults = () => {
  brightness.value = 0
  contrast.value = 1
  saturation.value = 1
  hue.value = 0
  gamma.value = 1
  // Don't call updateColorGrading() here to avoid unnecessary updates
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
  if (isInitializing.value) return

  isGeneratingPreview.value = true
  previewError.value = ''

  try {
    // Use filter only if preview is enabled
    const filterToApply = previewEnabled.value ? generatedFilter.value || undefined : undefined

    const result = await window.pywebview.api.generate_frame_preview(
      props.videoPath!,
      previewTimestamp.value,
      filterToApply,
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

const showPasteDialog = async () => {
  try {
    const clipboardText = await navigator.clipboard.readText()
    if (clipboardText.trim()) {
      pasteFilter(clipboardText.trim())
    } else {
      ElMessage.warning('Clipboard is empty')
    }
  } catch (error) {
    ElMessage.error('Failed to access clipboard. Please check permissions.')
    console.error('Clipboard access failed:', error)
  }
}

const copyToAllClips = () => {
  if (!generatedFilter.value || props.isMockMarkup) {
    return
  }

  emit('copy-to-all-clips', generatedFilter.value)
}

const pasteFilter = async (filterText?: string) => {
  let textToPaste = filterText

  if (!textToPaste) {
    try {
      textToPaste = await navigator.clipboard.readText()
    } catch (error) {
      ElMessage.error('Failed to access clipboard. Please check permissions.')
      return
    }
  }

  const trimmedText = textToPaste.trim()
  if (!trimmedText) {
    ElMessage.warning('No filter text to paste')
    return
  }

  // Try to parse and apply the filter to the current clip
  try {
    parseAndApplyFilter(trimmedText)
    updatePreview()
  } catch (error) {
    ElMessage.error(`Failed to apply filter: ${error}`)
  }
}

// Split a filter chain on commas only at top-level (outside quotes/parentheses)
function splitTopLevelFilters(s: string): string[] {
  const parts: string[] = []
  let buf = ''
  let inSingle = false
  let inDouble = false
  let paren = 0
  for (let i = 0; i < s.length; i++) {
    const ch = s[i]
    if (ch === "'" && !inDouble) {
      inSingle = !inSingle
      buf += ch
      continue
    }
    if (ch === '"' && !inSingle) {
      inDouble = !inDouble
      buf += ch
      continue
    }
    if (!inSingle && !inDouble) {
      if (ch === '(') paren++
      else if (ch === ')' && paren > 0) paren--
      if (ch === ',' && paren === 0) {
        const part = buf.trim()
        if (part) parts.push(part)
        buf = ''
        continue
      }
    }
    buf += ch
  }
  const tail = buf.trim()
  if (tail) parts.push(tail)
  return parts
}

const parseFilterToControls = (filterString: string) => {
  // Reset values first
  resetToDefaults()

  // Simple parser for common filter formats
  const filters = splitTopLevelFilters(filterString)

  for (const filter of filters) {
    const trimmed = filter.trim()

    if (trimmed.startsWith('hue=')) {
      const params = trimmed.substring(4).split(':')
      for (const param of params) {
        const [key, value] = param.split('=')
        const numValue = parseFloat(value)

        switch (key) {
          case 'b': // brightness in hue filter range [-10, 10]
            // Convert back to UI range [-1, 1]
            brightness.value = numValue / 10
            break
          case 's': // saturation - direct mapping from hue filter to UI
            // We use direct mapping: hue filter value = UI value
            saturation.value = numValue
            break
          case 'h': // hue angle in degrees
            hue.value = numValue
            break
        }
      }
    } else if (trimmed.startsWith('lutyuv=')) {
      // Handle gamma: lutyuv=y=gammaval(x)
      const afterEq = trimmed.substring('lutyuv='.length)
      // Normalize quotes
      const s = afterEq.replace(/^"|^'|"$|'$/g, '')
      // y=gammaval(x) form
      const gammaMatch = s.match(/y\s*=\s*gammaval\(([^)]+)\)/)
      if (gammaMatch) {
        const g = parseFloat(gammaMatch[1])
        if (!Number.isNaN(g) && g > 0) gamma.value = 1 / g
        continue
      }
      // Contrast around mid using min/max clamp
      const contrastMinMax = s.match(/y\s*=\s*'?min\(max\(\(val-\(maxval\+minval\)\/2\)\*([0-9.]+)\+\(maxval\+minval\)\/2\s*,\s*minval\)\s*,\s*maxval\)('?)/)
      if (contrastMinMax) {
        const c = parseFloat(contrastMinMax[1])
        if (!Number.isNaN(c)) contrast.value = c
        continue
      }
      // Back-compat: older clip() form
  const contrastClip = s.match(/y\s*=\s*'?clip\(\(val-\(maxval\+minval\)\/2\)\*([0-9.]+)\+\(maxval\+minval\)\/2\)'?/)
      if (contrastClip) {
        const c = parseFloat(contrastClip[1])
        if (!Number.isNaN(c)) contrast.value = c
        continue
      }
    } else if (trimmed.startsWith('eq=')) {
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
            // Use inverse to keep UI orientation consistent with lutyuv
            gamma.value = numValue > 0 ? 1 / numValue : numValue
            break
        }
      }
    }
  }
}

const parseAndApplyFilter = (filterString: string) => {
  parseFilterToControls(filterString)
  updateColorGrading()
}

const formatTime = (seconds: number): string => {
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${minutes}:${secs.toFixed(1).padStart(4, '0')}`
}

// (Removed separate watchers for selectedClip and videoPath; using consolidated watcher below)

// Watch for video info changes
watch(() => props.videoInfo, () => {
  // Video info display will automatically update via computed property
})

// Watch for preview resolution changes to update video info display
watch(() => previewResolution.value, () => {
  // Video info display will automatically update via computed property
})

// Consolidated watcher to avoid duplicate preview generation when clip/video changes
let initTimer: number | null = null
watch(
  () => ({
    clipNumber: props.selectedClip?.number ?? null,
    videoPath: props.videoPath ?? null,
    duration: props.videoDuration ?? null
  }),
  async (curr, prev) => {
    // If video path changed, reset UI state and wait for clip/duration to settle
    if (prev && curr.videoPath !== prev.videoPath) {
      isInitializing.value = true
      // Clear controls to defaults; avoid emitting changes
      resetToDefaults()
      // Cancel any pending color-grading preview debounce
      if (updateColorGrading.debounceTimer) {
        clearTimeout(updateColorGrading.debounceTimer)
        updateColorGrading.debounceTimer = null
      }
      // Cancel pending init timer
      if (initTimer) {
        clearTimeout(initTimer)
        initTimer = null
      }
      previewImageUrl.value = ''
      previewError.value = ''
      previewTimestamp.value = 0
      // Don't generate preview here; wait for next clip/duration update
      return
    }

    // Only proceed when both video and clip exist
    if (!hasVideoAndClip.value) return

    // Debounce to coalesce rapid duration/clip changes (e.g., mock markup init)
    if (initTimer) {
      clearTimeout(initTimer)
    }
    initTimer = window.setTimeout(async () => {
      await nextTick()
      loadClipColorGrading()
      initializeTimestamp()
      // End init and render once with settled state
      isInitializing.value = false
      updatePreview()
    }, 100)
  },
  { immediate: true, deep: false }
)

// Remove separate watchers and rely on the consolidated watcher above
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

.filter-output-card {
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  padding: 16px;
  background: var(--el-bg-color);
  margin-top: 16px;
}

.filter-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.filter-card-header h5 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.filter-header-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-textarea {
  margin-bottom: 16px;
}

.filter-textarea :deep(.el-textarea__inner) {
  font-family: monospace;
  font-size: 12px;
  line-height: 1.4;
  background: var(--el-fill-color-lighter);
}

.filter-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.action-group {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.primary-actions .el-button {
  flex: 1;
  min-width: 120px;
}

.secondary-actions .el-button {
  flex: 1;
  min-width: 100px;
}

.copy-paste-controls {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}
</style>
