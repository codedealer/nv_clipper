<template>
  <div class="color-grading-panel">
    <el-card>
      <template #header>
        <div class="panel-header">
          <h3>Color Grading</h3>
          <div class="header-controls">
            <el-button
              v-if="!isEnabled"
              type="primary"
              size="small"
              @click="enableColorGrading"
              :disabled="!hasVideoAndClip"
            >
              Enable
            </el-button>
            <el-button
              v-else
              type="info"
              size="small"
              @click="disableColorGrading"
            >
              Disable
            </el-button>
            <el-button
              v-if="isEnabled"
              size="small"
              @click="resetToDefaults"
            >
              Reset
            </el-button>
          </div>
        </div>
      </template>

      <div v-if="!hasVideoAndClip" class="no-content">
        <el-empty description="Select a video file and clip to enable color grading" />
      </div>

      <div v-else-if="!isEnabled" class="disabled-state">
        <p>Enable color grading to adjust video appearance</p>
      </div>

      <div v-else class="controls-container">
        <!-- Preview Controls -->
        <div class="preview-section">
          <div class="preview-header">
            <h4>Preview</h4>
            <div class="preview-controls">
              <el-select
                v-model="previewResolution"
                size="small"
                style="width: 100px"
                @change="updatePreview"
              >
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

          <div class="preview-container">
            <div v-if="isGeneratingPreview" class="preview-loading">
              <el-spinner />
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

        <!-- Timestamp Control -->
        <div class="timestamp-section">
          <el-form-item label="Preview Time">
            <el-input-number
              v-model="previewTimestamp"
              :min="selectedClip?.start || 0"
              :max="selectedClip?.end || 60"
              :step="0.1"
              :precision="1"
              size="small"
              @change="updatePreview"
            />
            <span class="timestamp-info">
              ({{ formatTime(selectedClip?.start || 0) }} - {{ formatTime(selectedClip?.end || 60) }})
            </span>
          </el-form-item>
        </div>

        <!-- Color Controls -->
        <div class="color-controls">
          <h4>Color Adjustments</h4>

          <!-- Brightness -->
          <div class="control-group">
            <el-form-item label="Brightness">
              <el-slider
                v-model="brightness"
                :min="-1"
                :max="1"
                :step="0.01"
                @change="updateColorGrading"
                show-input
                input-size="small"
              />
            </el-form-item>
          </div>

          <!-- Contrast -->
          <div class="control-group">
            <el-form-item label="Contrast">
              <el-slider
                v-model="contrast"
                :min="0"
                :max="3"
                :step="0.01"
                @change="updateColorGrading"
                show-input
                input-size="small"
              />
            </el-form-item>
          </div>

          <!-- Saturation -->
          <div class="control-group">
            <el-form-item label="Saturation">
              <el-slider
                v-model="saturation"
                :min="0"
                :max="3"
                :step="0.01"
                @change="updateColorGrading"
                show-input
                input-size="small"
              />
            </el-form-item>
          </div>

          <!-- Hue -->
          <div class="control-group">
            <el-form-item label="Hue">
              <el-slider
                v-model="hue"
                :min="-180"
                :max="180"
                :step="1"
                @change="updateColorGrading"
                show-input
                input-size="small"
              />
            </el-form-item>
          </div>

          <!-- Gamma -->
          <div class="control-group">
            <el-form-item label="Gamma">
              <el-slider
                v-model="gamma"
                :min="0.1"
                :max="3"
                :step="0.01"
                @change="updateColorGrading"
                show-input
                input-size="small"
              />
            </el-form-item>
          </div>
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
        </div>
      </div>
    </el-card>

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
import type { ClipInfo } from '@/types/api'

interface Props {
  selectedClip?: ClipInfo | null
  videoPath?: string | null
  isProcessing?: boolean
}

interface Emits {
  (e: 'color-grading-changed', clipNumber: number, filter: string): void
}

const props = withDefaults(defineProps<Props>(), {
  selectedClip: null,
  videoPath: null,
  isProcessing: false
})

const emit = defineEmits<Emits>()

// State
const isEnabled = ref(false)
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

const generatedFilter = computed(() => {
  if (!isEnabled.value) return ''

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

// Methods
const enableColorGrading = () => {
  isEnabled.value = true
  initializeTimestamp()
  updatePreview()
}

const disableColorGrading = () => {
  isEnabled.value = false
  previewImageUrl.value = ''
  if (props.selectedClip) {
    emit('color-grading-changed', props.selectedClip.number, '')
  }
}

const resetToDefaults = () => {
  brightness.value = 0
  contrast.value = 1
  saturation.value = 1
  hue.value = 0
  gamma.value = 1
  updateColorGrading()
  updatePreview()
}

const initializeTimestamp = () => {
  if (props.selectedClip) {
    // Set timestamp to middle of clip
    const clipDuration = props.selectedClip.end - props.selectedClip.start
    previewTimestamp.value = props.selectedClip.start + clipDuration / 2
  }
}

const updateColorGrading = () => {
  if (!isEnabled.value || !props.selectedClip) return

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
  if (!hasVideoAndClip.value || !isEnabled.value || !window.pywebview?.api) return

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
    if (isEnabled.value) {
      updatePreview()
    }
  }
})

// Watch for video path changes
watch(() => props.videoPath, () => {
  if (isEnabled.value && hasVideoAndClip.value) {
    updatePreview()
  }
})

onMounted(() => {
  if (hasVideoAndClip.value) {
    initializeTimestamp()
  }
})
</script>

<style scoped>
.color-grading-panel {
  width: 100%;
  max-width: 500px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-header h3 {
  margin: 0;
}

.header-controls {
  display: flex;
  gap: 8px;
}

.no-content,
.disabled-state {
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

.preview-controls {
  display: flex;
  gap: 8px;
  align-items: center;
}

.preview-container {
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--el-fill-color-lighter);
  border-radius: 4px;
}

.preview-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.preview-image img {
  max-width: 100%;
  max-height: 300px;
  border-radius: 4px;
}

.timestamp-section .timestamp-info {
  margin-left: 8px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.color-controls h4 {
  margin: 0 0 16px 0;
  border-bottom: 1px solid var(--el-border-color);
  padding-bottom: 8px;
}

.control-group {
  margin-bottom: 16px;
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
