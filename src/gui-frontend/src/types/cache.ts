// Types for video cache management

export interface CachedVideo {
  id: string
  title: string
  url: string
  platform: string
  file_path: string
  file_size: number
  duration: number
  cached_at: string
  last_accessed: string
  video_id: string
  format: string
  thumbnail_path?: string
}

export interface CacheInfo {
  total_size: number
  total_count: number
  max_size: number
  cache_dir: string
  videos: CachedVideo[]
}

export interface CacheDownloadProgress {
  video_id: string
  url: string
  title?: string
  status: 'starting' | 'initializing' | 'downloading' | 'processing' | 'finalizing' | 'completed' | 'error' | 'canceled'
  progress: number
  speed?: string
  eta?: string
  message?: string
}

export interface CacheDownloadRequest {
  url: string
  title?: string
  use_settings_format?: boolean
  auto_update?: boolean
}

export interface CacheOperationResult {
  status: 'success' | 'error'
  message: string
  video?: CachedVideo
  video_id?: string
}

export interface CachePurgeOptions {
  older_than_days?: number
  size_limit_mb?: number
  keep_most_recent?: number
}
