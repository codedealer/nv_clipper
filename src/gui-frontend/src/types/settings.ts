// Types for settings management in the GUI

export interface GeneralSettings {
  // === LOGGING OPTIONS ===
  log_level: number // 0-56
  no_rich_logs: boolean

  // === INPUT OPTIONS ===
  download_video: boolean
  format: string
  format_sort: string[]
  no_auto_find_input_video: boolean
  enable_video_streaming_protocol_hls: boolean

  // === OUTPUT OPTIONS ===
  audio?: boolean
  fast_trim?: boolean
  target_max_bitrate?: number
  h264_disable_reduce_stutter: boolean
  auto_subs_lang: string // Two-letter language code
  subs_file_path: string
  subs_style: string
  no_auto_scale_crop_res: boolean
  remove_metadata: boolean
  extra_ffmpeg_args: string
  extra_video_filters?: string
  extra_audio_filters?: string
  target_size: number // Target file size in MB, 0 = unlimited
  target_fps?: number // Force the video's frame rate to this value
  overwrite: boolean

  // === OTHER OPTIONS ===
  preview: boolean
  notify_on_completion: boolean

  // === AI/GPU PROCESSING OPTIONS ===
  gpu_id: number // GPU ID for interpolation
  rife_model_path: string // Path to RIFE model file
  rife_worker_threads: number // Number of worker threads for RIFE
  topaz_ai_path: string // Path to Topaz Video AI executable
  topaz_model_dir: string // Path to Topaz model directory
  topaz_model_data_dir: string // Path to Topaz model data directory

  // === YT-DLP OPTIONS ===
  ytdl_location: string
  ytdl_username: string
  ytdl_password: string
  cookiefile: string
  ytdl_auto_update: boolean
}

export interface VideoSpecificSettings {
  video_title: string
  video_url: string
  video_id: string
  platform: string
  is_vertical_video: boolean
  crop_res: string
  fps?: number
  width?: number
  height?: number
  duration?: number
  color_space?: string
}

export interface SettingsSchema {
  general: Record<string, SettingDefinition>
  video: Record<string, SettingDefinition>
}

export interface SettingDefinition {
  type: 'boolean' | 'string' | 'integer' | 'number'
  description: string
  min?: number
  max?: number
  options?: string[]
}

// Settings categories for UI organization
export interface SettingsCategory {
  id: string
  name: string
  description: string
  icon: string
  settings: string[]
}

export const SETTINGS_CATEGORIES: SettingsCategory[] = [
  {
    id: 'files',
    name: 'File Processing',
    description: 'File handling and processing options',
    icon: 'FolderOpened',
    settings: ['overwrite', 'format_sort', 'no_ytdl_auto_update']
  },
  {
    id: 'quality',
    name: 'Quality & Encoding',
    description: 'Video and audio quality settings',
    icon: 'Picture',
    settings: ['crf', 'target_max_bitrate', 'two_pass', 'video_codec', 'audio_codec']
  },
  {
    id: 'processing',
    name: 'Video Processing',
    description: 'Video enhancement and processing options',
    icon: 'VideoCamera',
    settings: ['denoise', 'stabilize', 'enhance_video', 'interpolate']
  },
  {
    id: 'ai_gpu',
    name: 'AI & GPU Processing',
    description: 'AI interpolation and GPU acceleration settings',
    icon: 'MagicStick',
    settings: ['gpu_id', 'rife_model_path', 'rife_worker_threads', 'topaz_ai_path', 'topaz_model_dir', 'topaz_model_data_dir']
  },
  {
    id: 'output',
    name: 'Output Options',
    description: 'Output filtering and optimization',
    icon: 'Upload',
    settings: ['enable_video_filters', 'enable_audio_filters', 'remove_duplicate_frames']
  },
  {
    id: 'advanced',
    name: 'Advanced',
    description: 'Advanced settings and debugging',
    icon: 'Setting',
    settings: ['log_level', 'preview_mode']
  },
  {
    id: 'ytdl',
    name: 'yt-dlp Settings',
    description: 'YouTube downloader configuration',
    icon: 'Download',
    settings: ['ytdl_location', 'cookies_file', 'format_selector']
  }
]

// Commonly used codec options
export const VIDEO_CODECS = [
  'libvpx-vp9',
  'libx264',
  'libx265',
  'h264_nvenc',
  'hevc_nvenc',
  'av1'
]

export const AUDIO_CODECS = [
  'libopus',
  'libvorbis',
  'aac',
  'mp3'
]

// Log level definitions
export const LOG_LEVELS = [
  { value: 0, label: 'Silent (0)' },
  { value: 10, label: 'Debug (10)' },
  { value: 15, label: 'Verbose (15)' },
  { value: 20, label: 'Info (20)' },
  { value: 30, label: 'Warning (30)' },
  { value: 40, label: 'Error (40)' },
  { value: 50, label: 'Critical (50)' }
]
