<template>
  <div class="settings-panel">
    <el-tabs v-model="activeTab" type="border-card">

      <!-- === LOGGING OPTIONS === -->
      <el-tab-pane label="Logging" name="logging">
        <div class="settings-section">
          <h4>Logging Configuration</h4>
          <el-form label-width="220px" label-position="left">
            <el-form-item label="Log Level (0-56)">
              <el-input-number
                :model-value="props.settings?.log_level || 15"
                @change="(value) => handleNumberChange('log_level', value)"
                :min="0"
                :max="56"
                :disabled="isLoading"
                style="width: 150px"
              />
              <el-text class="setting-help" type="info">
                VERBOSE=15, INFO=20, WARNING=30, ERROR=40, CRITICAL=50
              </el-text>
            </el-form-item>
            <el-form-item label="Disable rich colored logs">
              <el-switch
                :model-value="props.settings?.no_rich_logs || false"
                @update:model-value="(value) => updateBooleanSetting('no_rich_logs', value)"
                :loading="isLoading"
              />
              <el-text class="setting-help" type="info">Use simpler colored logging instead</el-text>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>

      <!-- === INPUT OPTIONS === -->
      <el-tab-pane label="Input" name="input">
        <div class="settings-section">
          <h4>Input Video Settings</h4>
          <el-form label-width="220px" label-position="left">
            <el-form-item label="Download video">
              <el-switch
                :model-value="props.settings?.download_video || false"
                @update:model-value="(value) => updateBooleanSetting('download_video', value)"
                :loading="isLoading"
              />
              <el-text class="setting-help" type="info">Download video from internet for processing</el-text>
            </el-form-item>
                        <el-form-item label="Format">
              <el-input
                :model-value="getCurrentTextValue('format', '(bestvideo+(bestaudio[acodec=opus]/bestaudio))/best')"
                @input="(value) => handleTextInput('format', value)"
                @blur="() => handleTextBlur('format')"
                @keyup.enter="() => handleTextEnter('format')"
                :disabled="isLoading"
                placeholder="Video format for yt-dlp"
              />
              <el-text class="setting-help" type="info">Format string passed to yt-dlp for video selection</el-text>
            </el-form-item>
            <el-form-item label="Format sort">
              <el-input
                :model-value="Array.isArray(props.settings?.format_sort) ? props.settings.format_sort.join(' ') : (props.settings?.format_sort || '')"
                @update:model-value="(value) => updateStringArraySetting('format_sort', value)"
                :disabled="isLoading"
                type="textarea"
                :rows="2"
                placeholder="hasvid,ie_pref,lang,quality,res,fps,br,size,hdr:1,vcodec:vp9.2,vcodec:vp9,asr,proto,ext,hasaud,source,id"
              />
              <el-text class="setting-help" type="info">Sorting for best audio/video formats</el-text>
            </el-form-item>
            <el-form-item label="Disable auto find input video">
              <el-switch
                :model-value="props.settings?.no_auto_find_input_video || false"
                @update:model-value="(value) => updateBooleanSetting('no_auto_find_input_video', value)"
                :loading="isLoading"
              />
            </el-form-item>
            <el-form-item label="Enable HLS protocol">
              <el-switch
                :model-value="props.settings?.enable_video_streaming_protocol_hls || false"
                @update:model-value="(value) => updateBooleanSetting('enable_video_streaming_protocol_hls', value)"
                :loading="isLoading"
              />
              <el-text class="setting-help" type="info">Enable HTTP Live Streaming (unreliable)</el-text>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>

      <!-- === OUTPUT OPTIONS === -->
      <el-tab-pane label="Output" name="output">
        <div class="settings-section">
          <h4>Output Settings</h4>
          <el-form label-width="220px" label-position="left">
            <el-form-item label="Enable audio">
              <el-switch
                :model-value="props.settings?.audio !== false"
                @update:model-value="(value) => updateBooleanSetting('audio', value)"
                :loading="isLoading"
              />
              <el-text class="setting-help" type="info">Include audio in output clips</el-text>
            </el-form-item>
            <el-form-item label="Fast trim mode">
              <el-switch
                :model-value="props.settings?.fast_trim || false"
                @update:model-value="(value) => updateBooleanSetting('fast_trim', value)"
                :loading="isLoading"
              />
              <el-text class="setting-help" type="info">Quick clips without re-encoding (less precise)</el-text>
            </el-form-item>
            <el-form-item label="Overwrite existing clips">
              <el-switch
                :model-value="props.settings?.overwrite || false"
                @update:model-value="(value) => updateBooleanSetting('overwrite', value)"
                :loading="isLoading"
              />
            </el-form-item>
            <el-form-item label="Target max bitrate (kbps)">
              <el-input-number
                :model-value="props.settings?.target_max_bitrate"
                @change="(value) => handleNumberChange('target_max_bitrate', value)"
                :min="100"
                :max="50000"
                :disabled="isLoading"
                style="width: 150px"
                placeholder="Auto"
              />
            </el-form-item>
            <el-form-item label="Target file size (MB)">
              <el-input-number
                :model-value="props.settings?.target_size || 0"
                @change="(value) => handleNumberChange('target_size', value)"
                :min="0"
                :disabled="isLoading"
                style="width: 150px"
                placeholder="Unlimited"
              />
              <el-text class="setting-help" type="info">0 = unlimited size</el-text>
            </el-form-item>
            <el-form-item label="Target FPS">
              <el-input-number
                :model-value="props.settings?.target_fps || null"
                @change="(value) => handleNumberChange('target_fps', value)"
                :min="1"
                :max="300"
                :disabled="isLoading"
                style="width: 150px"
                placeholder="Auto"
              />
              <el-text class="setting-help" type="info">Force the video's frame rate to this value (affects interpolation calculations)</el-text>
            </el-form-item>
          </el-form>

          <h4>H.264 Settings</h4>
          <el-form label-width="220px" label-position="left">
            <el-form-item label="Disable reduce stutter">
              <el-switch
                :model-value="props.settings?.h264_disable_reduce_stutter || false"
                @update:model-value="(value) => updateBooleanSetting('h264_disable_reduce_stutter', value)"
                :loading="isLoading"
              />
              <el-text class="setting-help" type="info">For H.264: disable stutter reduction</el-text>
            </el-form-item>
          </el-form>

          <h4>Subtitle Settings</h4>
          <el-form label-width="220px" label-position="left">
                        <el-form-item label="Auto subtitles language">
              <el-input
                :model-value="getCurrentTextValue('auto_subs_lang')"
                @input="(value) => handleTextInput('auto_subs_lang', value)"
                @blur="() => handleTextBlur('auto_subs_lang')"
                @keyup.enter="() => handleTextEnter('auto_subs_lang')"
                :disabled="isLoading"
                placeholder="Language code (e.g., 'en')"
                maxlength="5"
              />
              <el-text class="setting-help" type="info">Two-letter language code for automatic subtitle download</el-text>
            </el-form-item>
            <el-form-item label="Subtitle file path">
              <el-input
                :model-value="getCurrentTextValue('subs_file_path')"
                @input="(value) => handleTextInput('subs_file_path', value)"
                @blur="() => handleTextBlur('subs_file_path')"
                @keyup.enter="() => handleTextEnter('subs_file_path')"
                :disabled="isLoading"
                placeholder="Path to .vtt, .sbv, or .srt file"
              />
            </el-form-item>
                        <el-form-item label="Subtitles style">
              <el-input
                :model-value="getCurrentTextValue('subs_style', 'FontSize=12,PrimaryColour=&H32FFFFFF,SecondaryColour=&H32000000,MarginV=5')"
                @input="(value) => handleTextInput('subs_style', value)"
                @blur="() => handleTextBlur('subs_style')"
                @keyup.enter="() => handleTextEnter('subs_style')"
                :disabled="isLoading"
                placeholder="ASS format string for styling"
              />
            </el-form-item>
          </el-form>

          <h4>Advanced Output</h4>
          <el-form label-width="220px" label-position="left">
            <el-form-item label="Disable auto-scale crop">
              <el-switch
                :model-value="props.settings?.no_auto_scale_crop_res || false"
                @update:model-value="(value) => updateBooleanSetting('no_auto_scale_crop_res', value)"
                :loading="isLoading"
              />
            </el-form-item>
            <el-form-item label="Remove metadata">
              <el-switch
                :model-value="props.settings?.remove_metadata || false"
                @update:model-value="(value) => updateBooleanSetting('remove_metadata', value)"
                :loading="isLoading"
              />
            </el-form-item>
            <el-form-item label="Extra FFmpeg arguments">
              <el-input
                :model-value="getCurrentTextValue('extra_ffmpeg_args')"
                @input="(value) => handleTextInput('extra_ffmpeg_args', value)"
                @blur="() => handleTextBlur('extra_ffmpeg_args')"
                :disabled="isLoading"
                type="textarea"
                :rows="2"
                placeholder="Additional FFmpeg arguments"
              />
            </el-form-item>
            <el-form-item label="Extra video filters">
              <el-input
                :model-value="getCurrentTextValue('extra_video_filters')"
                @input="(value) => handleTextInput('extra_video_filters', value)"
                @blur="() => handleTextBlur('extra_video_filters')"
                :disabled="isLoading"
                type="textarea"
                :rows="2"
                placeholder="Additional video filters for FFmpeg"
              />
              <el-text class="setting-help" type="info">Extra video filters to be passed to ffmpeg</el-text>
            </el-form-item>
            <el-form-item label="Extra audio filters">
              <el-input
                :model-value="getCurrentTextValue('extra_audio_filters')"
                @input="(value) => handleTextInput('extra_audio_filters', value)"
                @blur="() => handleTextBlur('extra_audio_filters')"
                :disabled="isLoading"
                type="textarea"
                :rows="2"
                placeholder="Additional audio filters for FFmpeg"
              />
              <el-text class="setting-help" type="info">Extra audio filters to be passed to ffmpeg</el-text>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>

      <!-- === AI/GPU PROCESSING OPTIONS === -->
      <el-tab-pane label="AI & GPU" name="ai_gpu">
        <div class="settings-section">
          <h4>GPU Configuration</h4>
          <el-form label-width="220px" label-position="left">
            <el-form-item label="GPU ID">
              <el-input-number
                :model-value="props.settings?.gpu_id || 0"
                @change="(value) => handleNumberChange('gpu_id', value)"
                :min="0"
                :max="15"
                :disabled="isLoading"
                style="width: 150px"
              />
              <el-text class="setting-help" type="info">GPU device ID for AI interpolation (0 = first GPU)</el-text>
            </el-form-item>
          </el-form>

          <h4>RIFE Interpolation</h4>
          <el-form label-width="220px" label-position="left">
            <el-form-item label="RIFE model path">
              <el-input
                :model-value="getCurrentTextValue('rife_model_path')"
                @input="(value) => handleTextInput('rife_model_path', value)"
                @blur="() => handleTextBlur('rife_model_path')"
                @keyup.enter="() => handleTextEnter('rife_model_path')"
                :disabled="isLoading"
                placeholder="Path to RIFE model file (.onnx)"
              />
              <el-text class="setting-help" type="info">Path to RIFE ONNX model for AI frame interpolation</el-text>
            </el-form-item>
            <el-form-item label="Worker threads">
              <el-input-number
                :model-value="props.settings?.rife_worker_threads || 1"
                @change="(value) => handleNumberChange('rife_worker_threads', value)"
                :min="1"
                :max="32"
                :disabled="isLoading"
                style="width: 150px"
              />
              <el-text class="setting-help" type="info">Number of worker threads for RIFE processing</el-text>
            </el-form-item>
          </el-form>

          <h4>Topaz Video AI</h4>
          <el-form label-width="220px" label-position="left">
            <el-form-item label="Topaz Video AI path">
              <el-input
                :model-value="getCurrentTextValue('topaz_ai_path')"
                @input="(value) => handleTextInput('topaz_ai_path', value)"
                @blur="() => handleTextBlur('topaz_ai_path')"
                @keyup.enter="() => handleTextEnter('topaz_ai_path')"
                :disabled="isLoading"
                placeholder="Path to Topaz Video AI executable"
              />
              <el-text class="setting-help" type="info">Path to the Topaz Video AI application executable</el-text>
            </el-form-item>
            <el-form-item label="Model directory">
              <el-input
                :model-value="getCurrentTextValue('topaz_model_dir')"
                @input="(value) => handleTextInput('topaz_model_dir', value)"
                @blur="() => handleTextBlur('topaz_model_dir')"
                @keyup.enter="() => handleTextEnter('topaz_model_dir')"
                :disabled="isLoading"
                placeholder="Path to Topaz models directory"
              />
              <el-text class="setting-help" type="info">Directory containing Topaz Video AI model files</el-text>
            </el-form-item>
            <el-form-item label="Model data directory">
              <el-input
                :model-value="getCurrentTextValue('topaz_model_data_dir')"
                @input="(value) => handleTextInput('topaz_model_data_dir', value)"
                @blur="() => handleTextBlur('topaz_model_data_dir')"
                @keyup.enter="() => handleTextEnter('topaz_model_data_dir')"
                :disabled="isLoading"
                placeholder="Path to Topaz model data directory"
              />
              <el-text class="setting-help" type="info">Directory containing Topaz Video AI model data</el-text>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>

      <!-- === OTHER OPTIONS === -->
      <el-tab-pane label="Other" name="other">
        <div class="settings-section">
          <h4>General Options</h4>
          <el-form label-width="220px" label-position="left">
            <el-form-item label="Preview mode">
              <el-switch
                :model-value="props.settings?.preview || false"
                @update:model-value="(value) => updateBooleanSetting('preview', value)"
                :loading="isLoading"
              />
              <el-text class="setting-help" type="info">Skip generating clips, preview only</el-text>
            </el-form-item>
            <el-form-item label="Notify on completion">
              <el-switch
                :model-value="props.settings?.notify_on_completion || false"
                @update:model-value="(value) => updateBooleanSetting('notify_on_completion', value)"
                :loading="isLoading"
              />
              <el-text class="setting-help" type="info">Show system notification when done</el-text>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>

      <!-- === YT-DLP OPTIONS === -->
      <el-tab-pane label="YT-DLP" name="ytdl">
        <div class="settings-section">
          <h4>YT-DLP Configuration</h4>
          <el-form label-width="220px" label-position="left">
            <el-form-item label="YT-DLP location">
              <el-input
                :model-value="getCurrentTextValue('ytdl_location')"
                @input="(value) => handleTextInput('ytdl_location', value)"
                @blur="() => handleTextBlur('ytdl_location')"
                @keyup.enter="() => handleTextEnter('ytdl_location')"
                :disabled="isLoading"
                placeholder="Path to yt-dlp executable"
              />
            </el-form-item>
            <el-form-item label="Auto-update YT-DLP">
              <el-switch
                :model-value="props.settings?.ytdl_auto_update !== false"
                @update:model-value="(value) => updateBooleanSetting('ytdl_auto_update', value)"
                :loading="isLoading"
              />
            </el-form-item>
            <el-form-item label="Cookies file">
              <el-input
                :model-value="getCurrentTextValue('cookiefile')"
                @input="(value) => handleTextInput('cookiefile', value)"
                @blur="() => handleTextBlur('cookiefile')"
                @keyup.enter="() => handleTextEnter('cookiefile')"
                :disabled="isLoading"
                placeholder="Path to Netscape cookies file"
              />
            </el-form-item>
            <el-form-item label="Username">
              <el-input
                :model-value="getCurrentTextValue('ytdl_username')"
                @input="(value) => handleTextInput('ytdl_username', value)"
                @blur="() => handleTextBlur('ytdl_username')"
                @keyup.enter="() => handleTextEnter('ytdl_username')"
                :disabled="isLoading"
                placeholder="Authentication username"
              />
            </el-form-item>
            <el-form-item label="Password">
              <el-input
                :model-value="getCurrentTextValue('ytdl_password')"
                @input="(value) => handleTextInput('ytdl_password', value)"
                @blur="() => handleTextBlur('ytdl_password')"
                @keyup.enter="() => handleTextEnter('ytdl_password')"
                :disabled="isLoading"
                type="password"
                placeholder="Authentication password"
                show-password
              />
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- Action buttons -->
    <div class="settings-actions">
      <el-button @click="handleReset" :loading="isLoading" type="warning">
        Reset to Defaults
      </el-button>
      <el-button @click="handleExport" :loading="isLoading">
        Export to Args File
      </el-button>
      <el-button @click="handleImport" :loading="isLoading">
        Import from Args File
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import {
  ElTabs,
  ElTabPane,
  ElForm,
  ElFormItem,
  ElInputNumber,
  ElSwitch,
  ElInput,
  ElButton,
  ElText
} from 'element-plus'
import type { GeneralSettings } from '@/types/settings'

// Props
interface Props {
  settings?: GeneralSettings | null
  isLoading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  settings: null,
  isLoading: false
})

// Emits
const emit = defineEmits<{
  'update-setting': [key: string, value: unknown]
  'reset-settings': []
  'export-settings': []
  'import-settings': []
}>()

// State
const activeTab = ref('logging')
const pendingTextChanges = ref<Record<string, string>>({})

// Methods
function updateSetting(key: string, value: unknown) {
  emit('update-setting', key, value)
}

// Immediate update for non-text inputs
function updateSettingImmediate(key: string, value: unknown) {
  emit('update-setting', key, value)
}

// Handle text input changes (store locally, don't save yet)
function handleTextInput(key: string, value: string) {
  pendingTextChanges.value[key] = value
}

// Save text input when user finishes editing (blur event)
function handleTextBlur(key: string) {
  const value = pendingTextChanges.value[key]
  if (value !== undefined) {
    updateSetting(key, value)
    delete pendingTextChanges.value[key]
  }
}

// Save text input on Enter key press
function handleTextEnter(key: string) {
  handleTextBlur(key)
}

// Get current text value (either pending or from settings)
function getCurrentTextValue(key: string, fallback: string = ''): string {
  if (key in pendingTextChanges.value) {
    return pendingTextChanges.value[key]
  }
  if (props.settings && key in props.settings) {
    const value = props.settings[key as keyof GeneralSettings]
    return typeof value === 'string' ? value : (value?.toString() ?? fallback)
  }
  return fallback
}

// Handle number change event (save immediately)
function handleNumberChange(key: string, value: number | null | undefined) {
  updateSetting(key, value ?? null)
}

// Typed handlers for different value types
function updateNumberSetting(key: string, value: number | null | undefined) {
  updateSettingImmediate(key, value ?? null)
}

function updateBooleanSetting(key: string, value: boolean | string | number) {
  updateSettingImmediate(key, Boolean(value))
}

function updateStringSetting(key: string, value: string | number | boolean) {
  updateSettingImmediate(key, String(value))
}

function updateStringArraySetting(key: string, value: string) {
  // Convert string to array, filtering out empty strings
  // If the entire string is empty/whitespace, this results in an empty array
  // which will trigger schema default application in the backend
  const arrayValue = value.trim() === '' ? [] : value.split(' ').filter(Boolean)
  updateSettingImmediate(key, arrayValue)
}

function handleReset() {
  emit('reset-settings')
}

function handleExport() {
  emit('export-settings')
}

function handleImport() {
  emit('import-settings')
}
</script>

<style scoped>
.settings-panel {
  min-height: 400px;
}

.settings-section {
  padding: 16px;
}

.settings-section h4 {
  margin: 0 0 16px 0;
  color: var(--el-text-color-primary);
  font-weight: 600;
  border-bottom: 1px solid var(--el-border-color-lighter);
  padding-bottom: 8px;
}

.setting-help {
  display: block;
  margin-top: 4px;
  margin-left: 8px;
  font-size: 12px;
  line-height: 1.4;
}

.settings-actions {
  padding: 16px;
  border-top: 1px solid var(--el-border-color-lighter);
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}
</style>
