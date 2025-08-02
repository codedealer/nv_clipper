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
                :model-value="settings?.log_level || 15"
                @update:model-value="(value) => updateNumberSetting('log_level', value)"
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
                :model-value="settings?.no_rich_logs || false"
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
                :model-value="settings?.download_video || false"
                @update:model-value="(value) => updateBooleanSetting('download_video', value)"
                :loading="isLoading"
              />
              <el-text class="setting-help" type="info">Download video from internet for processing</el-text>
            </el-form-item>
            <el-form-item label="Format string">
              <el-input
                :model-value="settings?.format || ''"
                @update:model-value="(value) => updateStringSetting('format', value)"
                :disabled="isLoading"
                placeholder="(bestvideo+(bestaudio[acodec=opus]/bestaudio))/best"
              />
              <el-text class="setting-help" type="info">Format string passed to yt-dlp</el-text>
            </el-form-item>
            <el-form-item label="Format sort">
              <el-input
                :model-value="Array.isArray(settings?.format_sort) ? settings.format_sort.join(' ') : (settings?.format_sort || '')"
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
                :model-value="settings?.no_auto_find_input_video || false"
                @update:model-value="(value) => updateBooleanSetting('no_auto_find_input_video', value)"
                :loading="isLoading"
              />
            </el-form-item>
            <el-form-item label="Enable HLS protocol">
              <el-switch
                :model-value="settings?.enable_video_streaming_protocol_hls || false"
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
                :model-value="settings?.audio !== false"
                @update:model-value="(value) => updateBooleanSetting('audio', value)"
                :loading="isLoading"
              />
              <el-text class="setting-help" type="info">Include audio in output clips</el-text>
            </el-form-item>
            <el-form-item label="Fast trim mode">
              <el-switch
                :model-value="settings?.fast_trim || false"
                @update:model-value="(value) => updateBooleanSetting('fast_trim', value)"
                :loading="isLoading"
              />
              <el-text class="setting-help" type="info">Quick clips without re-encoding (less precise)</el-text>
            </el-form-item>
            <el-form-item label="Overwrite existing clips">
              <el-switch
                :model-value="settings?.overwrite || false"
                @update:model-value="(value) => updateBooleanSetting('overwrite', value)"
                :loading="isLoading"
              />
            </el-form-item>
            <el-form-item label="Target max bitrate (kbps)">
              <el-input-number
                :model-value="settings?.target_max_bitrate"
                @update:model-value="(value) => updateNumberSetting('target_max_bitrate', value)"
                :min="100"
                :max="50000"
                :disabled="isLoading"
                style="width: 150px"
                placeholder="Auto"
              />
            </el-form-item>
            <el-form-item label="Target file size (MB)">
              <el-input-number
                :model-value="settings?.target_size || 0"
                @update:model-value="(value) => updateNumberSetting('target_size', value)"
                :min="0"
                :disabled="isLoading"
                style="width: 150px"
                placeholder="Unlimited"
              />
              <el-text class="setting-help" type="info">0 = unlimited size</el-text>
            </el-form-item>
          </el-form>

          <h4>H.264 Settings</h4>
          <el-form label-width="220px" label-position="left">
            <el-form-item label="Disable reduce stutter">
              <el-switch
                :model-value="settings?.h264_disable_reduce_stutter || false"
                @update:model-value="(value) => updateBooleanSetting('h264_disable_reduce_stutter', value)"
                :loading="isLoading"
              />
              <el-text class="setting-help" type="info">For H.264: disable stutter reduction</el-text>
            </el-form-item>
          </el-form>

          <h4>Subtitle Settings</h4>
          <el-form label-width="220px" label-position="left">
            <el-form-item label="Auto-download subtitles">
              <el-input
                :model-value="settings?.auto_subs_lang || ''"
                @update:model-value="(value) => updateStringSetting('auto_subs_lang', value)"
                :disabled="isLoading"
                style="width: 100px"
                placeholder="en"
              />
              <el-text class="setting-help" type="info">Two-letter language code (en, fr, ja, etc.)</el-text>
            </el-form-item>
            <el-form-item label="Subtitle file path">
              <el-input
                :model-value="settings?.subs_file_path || ''"
                @update:model-value="(value) => updateStringSetting('subs_file_path', value)"
                :disabled="isLoading"
                placeholder="Path to .vtt, .sbv, or .srt file"
              />
            </el-form-item>
            <el-form-item label="Subtitle style">
              <el-input
                :model-value="settings?.subs_style || ''"
                @update:model-value="(value) => updateStringSetting('subs_style', value)"
                :disabled="isLoading"
                type="textarea"
                :rows="2"
                placeholder="ASS format styling"
              />
            </el-form-item>
          </el-form>

          <h4>Advanced Output</h4>
          <el-form label-width="220px" label-position="left">
            <el-form-item label="Disable auto-scale crop">
              <el-switch
                :model-value="settings?.no_auto_scale_crop_res || false"
                @update:model-value="(value) => updateBooleanSetting('no_auto_scale_crop_res', value)"
                :loading="isLoading"
              />
            </el-form-item>
            <el-form-item label="Remove metadata">
              <el-switch
                :model-value="settings?.remove_metadata || false"
                @update:model-value="(value) => updateBooleanSetting('remove_metadata', value)"
                :loading="isLoading"
              />
            </el-form-item>
            <el-form-item label="Extra FFmpeg arguments">
              <el-input
                :model-value="settings?.extra_ffmpeg_args || ''"
                @update:model-value="(value) => updateStringSetting('extra_ffmpeg_args', value)"
                :disabled="isLoading"
                type="textarea"
                :rows="2"
                placeholder="Additional FFmpeg arguments"
              />
            </el-form-item>
            <el-form-item label="Extra video filters">
              <el-input
                :model-value="settings?.extra_video_filters || ''"
                @update:model-value="(value) => updateStringSetting('extra_video_filters', value)"
                :disabled="isLoading"
                type="textarea"
                :rows="2"
                placeholder="Additional video filters for FFmpeg"
              />
              <el-text class="setting-help" type="info">Extra video filters to be passed to ffmpeg</el-text>
            </el-form-item>
            <el-form-item label="Extra audio filters">
              <el-input
                :model-value="settings?.extra_audio_filters || ''"
                @update:model-value="(value) => updateStringSetting('extra_audio_filters', value)"
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
                :model-value="settings?.gpu_id || 0"
                @update:model-value="(value) => updateNumberSetting('gpu_id', value)"
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
                :model-value="settings?.rife_model_path || ''"
                @update:model-value="(value) => updateStringSetting('rife_model_path', value)"
                :disabled="isLoading"
                placeholder="Path to RIFE model file (.onnx)"
              />
              <el-text class="setting-help" type="info">Path to RIFE ONNX model for AI frame interpolation</el-text>
            </el-form-item>
            <el-form-item label="Worker threads">
              <el-input-number
                :model-value="settings?.rife_worker_threads || 1"
                @update:model-value="(value) => updateNumberSetting('rife_worker_threads', value)"
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
                :model-value="settings?.topaz_ai_path || ''"
                @update:model-value="(value) => updateStringSetting('topaz_ai_path', value)"
                :disabled="isLoading"
                placeholder="Path to Topaz Video AI executable"
              />
              <el-text class="setting-help" type="info">Path to the Topaz Video AI application executable</el-text>
            </el-form-item>
            <el-form-item label="Model directory">
              <el-input
                :model-value="settings?.topaz_model_dir || ''"
                @update:model-value="(value) => updateStringSetting('topaz_model_dir', value)"
                :disabled="isLoading"
                placeholder="Path to Topaz models directory"
              />
              <el-text class="setting-help" type="info">Directory containing Topaz Video AI model files</el-text>
            </el-form-item>
            <el-form-item label="Model data directory">
              <el-input
                :model-value="settings?.topaz_model_data_dir || ''"
                @update:model-value="(value) => updateStringSetting('topaz_model_data_dir', value)"
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
                :model-value="settings?.preview || false"
                @update:model-value="(value) => updateBooleanSetting('preview', value)"
                :loading="isLoading"
              />
              <el-text class="setting-help" type="info">Skip generating clips, preview only</el-text>
            </el-form-item>
            <el-form-item label="Notify on completion">
              <el-switch
                :model-value="settings?.notify_on_completion || false"
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
                :model-value="settings?.ytdl_location || ''"
                @update:model-value="(value) => updateStringSetting('ytdl_location', value)"
                :disabled="isLoading"
                placeholder="Path to yt-dlp executable"
              />
            </el-form-item>
            <el-form-item label="Auto-update YT-DLP">
              <el-switch
                :model-value="settings?.ytdl_auto_update !== false"
                @update:model-value="(value) => updateBooleanSetting('ytdl_auto_update', value)"
                :loading="isLoading"
              />
            </el-form-item>
            <el-form-item label="Cookies file">
              <el-input
                :model-value="settings?.cookiefile || ''"
                @update:model-value="(value) => updateStringSetting('cookiefile', value)"
                :disabled="isLoading"
                placeholder="Path to Netscape cookies file"
              />
            </el-form-item>
            <el-form-item label="Username">
              <el-input
                :model-value="settings?.ytdl_username || ''"
                @update:model-value="(value) => updateStringSetting('ytdl_username', value)"
                :disabled="isLoading"
                placeholder="Authentication username"
              />
            </el-form-item>
            <el-form-item label="Password">
              <el-input
                :model-value="settings?.ytdl_password || ''"
                @update:model-value="(value) => updateStringSetting('ytdl_password', value)"
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

withDefaults(defineProps<Props>(), {
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

// Methods
function updateSetting(key: string, value: unknown) {
  emit('update-setting', key, value)
}

// Typed handlers for different value types
function updateNumberSetting(key: string, value: number | null | undefined) {
  updateSetting(key, value ?? null)
}

function updateBooleanSetting(key: string, value: boolean | string | number) {
  updateSetting(key, Boolean(value))
}

function updateStringSetting(key: string, value: string | number | boolean) {
  updateSetting(key, String(value))
}

function updateStringArraySetting(key: string, value: string) {
  // Convert string to array, filtering out empty strings
  // If the entire string is empty/whitespace, this results in an empty array
  // which will trigger schema default application in the backend
  const arrayValue = value.trim() === '' ? [] : value.split(' ').filter(Boolean)
  updateSetting(key, arrayValue)
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
