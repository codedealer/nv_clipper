// Types for the Python API interface through pywebview

export interface ProcessingResult {
  status: 'success' | 'error' | 'accepted'
  message: string
  job_id?: string
  report?: string
  output_path?: string
}

export interface JobStatus {
  status: 'processing' | 'success' | 'error' | 'starting'
  message: string
  job_id?: string
  report?: string
  output_path?: string
}

export interface EngineStatus {
  initialized: boolean
  engine_ready: boolean
  version: string
}

export interface SelectedFiles {
  markup: string | null
  video: string | null
}

export interface ClipInfo {
  number: number
  title: string
  start: number
  end: number
  duration: number
  speed: number
  crop: string
  enableZoomPan: boolean
  overrides: Record<string, unknown>
}

export interface VideoInfo {
  title: string
  video_url: string
  video_id: string
  platform: string
  is_vertical: boolean
  crop_res: string
  version: string
}

// Cache API interfaces
export interface CacheApiResponse {
  status: 'success' | 'error'
  message?: string
  data?: unknown
  video_id?: string
  progress?: unknown
}

// Cache request types for API (to avoid circular imports)
export interface ApiCacheDownloadRequest {
  url: string
  title?: string
  use_settings_format?: boolean
  auto_update?: boolean
  format?: string
  format_sort?: string[]
  ytdl_location?: string
}

export interface ApiCachePurgeOptions {
  older_than_days?: number
  size_limit_mb?: number
  keep_most_recent?: number
}

export interface ParseMarkupResult {
  status: 'success' | 'error'
  message?: string
  clips?: ClipInfo[]
  video_info?: VideoInfo
}

// Settings API response types
export interface SettingsApiResponse {
  status: 'success' | 'error'
  message?: string
  settings?: Record<string, unknown>
  general?: Record<string, unknown>
  video?: Record<string, unknown>
  schema?: Record<string, unknown>
  file_path?: string
}

// Pywebview API interface
declare global {
  interface Window {
    pywebview: {
      api: {
        // File processing
        process_files: (markupPath: string, videoPath?: string, selectedClips?: number[]) => Promise<ProcessingResult>
        get_job_status: (jobId: string) => Promise<JobStatus>
        get_status: () => Promise<EngineStatus>
        select_files: () => Promise<string[]>
        parse_markup_file: (filePath: string) => Promise<ParseMarkupResult>
        cleanup_old_jobs: () => Promise<{ cleaned: number }>

        // Settings management
        get_general_settings: () => Promise<SettingsApiResponse>
        get_video_settings: () => Promise<SettingsApiResponse>
        get_all_settings: () => Promise<SettingsApiResponse>
        get_settings_schema: () => Promise<SettingsApiResponse>
        update_general_settings: (settings: Record<string, unknown>) => Promise<SettingsApiResponse>
        update_video_settings: (settings: Record<string, unknown>) => Promise<SettingsApiResponse>
        reset_settings_to_defaults: () => Promise<SettingsApiResponse>
        export_settings_to_args_file: (filePath?: string) => Promise<SettingsApiResponse>
        import_settings_from_args_file: (filePath: string) => Promise<SettingsApiResponse>

        // Cache management
        get_cache_info: () => Promise<CacheApiResponse>
        download_video_to_cache: (request: ApiCacheDownloadRequest) => Promise<CacheApiResponse>
        get_download_progress: (videoId: string) => Promise<CacheApiResponse>
        cancel_download: (videoId: string) => Promise<CacheApiResponse>
        delete_cached_video: (videoId: string) => Promise<CacheApiResponse>
        purge_cache: (options: ApiCachePurgeOptions) => Promise<CacheApiResponse>
        update_video_access_time: (videoId: string) => Promise<CacheApiResponse>

        // Drag and drop
        setup_drag_drop: () => Promise<{ status: string; message?: string }>
        get_current_files: () => Promise<{ status: string; files: string[]; count?: number }>
        clear_current_files: () => Promise<{ status: string; message?: string; previous_count?: number }>
      }
    }
  }
}
