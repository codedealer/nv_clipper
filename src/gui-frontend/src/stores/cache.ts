import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type {
  CachedVideo,
  CacheInfo,
  CacheDownloadProgress,
  CacheDownloadRequest,
  CacheOperationResult,
  CachePurgeOptions
} from '@/types/cache'
import { waitForPywebview } from '@/utils/api'

export const useCacheStore = defineStore('cache', () => {
  // State
  const cacheInfo = ref<CacheInfo | null>(null)
  const downloadProgress = ref<Map<string, CacheDownloadProgress>>(new Map())
  const isLoading = ref(false)
  const lastError = ref<string | null>(null)

  // Getters
  const cachedVideos = computed(() => cacheInfo.value?.videos ?? [])
  const totalCachedSize = computed(() => cacheInfo.value?.total_size ?? 0)
  const totalCachedCount = computed(() => cacheInfo.value?.total_count ?? 0)
  const cacheDirectory = computed(() => cacheInfo.value?.cache_dir ?? '')
  const maxCacheSize = computed(() => cacheInfo.value?.max_size ?? 0)

  const activeDownloads = computed(() => {
    return Array.from(downloadProgress.value.values()).filter(
      p => p.status === 'downloading' ||
          p.status === 'starting' ||
          p.status === 'initializing' ||
          p.status === 'processing' ||
          p.status === 'finalizing'
    )
  })

  const isDownloading = computed(() => activeDownloads.value.length > 0)

  // Actions
  async function loadCacheInfo(): Promise<void> {
    isLoading.value = true
    lastError.value = null

    try {
      const api = await waitForPywebview()
      const result = await api.get_cache_info()

      if (result.status === 'success') {
        cacheInfo.value = result.data as CacheInfo
      } else {
        throw new Error(result.message || 'Failed to load cache info')
      }
    } catch (error) {
      lastError.value = error instanceof Error ? error.message : 'Unknown error'
      console.error('Failed to load cache info:', error)
    } finally {
      isLoading.value = false
    }
  }

  async function downloadVideo(request: CacheDownloadRequest): Promise<CacheOperationResult> {
    lastError.value = null

    try {
      const api = await waitForPywebview()

      // Simply pass the request to the backend - it will handle settings retrieval
      const result = await api.download_video_to_cache(request)

      if (result.status === 'success' && result.video_id) {
        // Initialize progress tracking
        downloadProgress.value.set(result.video_id, {
          video_id: result.video_id,
          url: request.url,
          status: 'starting',
          progress: 0
        })

        // Start polling for progress
        pollDownloadProgress(result.video_id)
      }

      return result as CacheOperationResult
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Unknown error'
      lastError.value = errorMsg
      return {
        status: 'error',
        message: errorMsg
      }
    }
  }

  async function pollDownloadProgress(videoId: string): Promise<void> {
    try {
      const api = await waitForPywebview()

      const poll = async () => {
        try {
          const result = await api.get_download_progress(videoId)

          if (result.status === 'success' && result.progress) {
            const progress = result.progress as CacheDownloadProgress
            downloadProgress.value.set(videoId, progress)

            // Continue polling if still downloading
            if (progress.status === 'downloading' ||
                progress.status === 'starting' ||
                progress.status === 'processing' ||
                progress.status === 'initializing' ||
                progress.status === 'finalizing') {
              setTimeout(poll, 1000) // Poll every second
            } else if (progress.status === 'error') {
              // For error status, set the error message and keep the download visible
              lastError.value = progress.message || 'Download failed with unknown error'
              console.error('Download failed:', progress.message)
              // Don't remove from progress tracking immediately - let user see the error
              // We'll remove it when cache is refreshed or user dismisses the error
            } else if (progress.status === 'completed') {
              // Download completed successfully, refresh cache info
              await loadCacheInfo()
            }
          } else if (result.status === 'error') {
            // API error - set error message and remove from tracking
            lastError.value = result.message || 'Failed to get download progress'
            downloadProgress.value.delete(videoId)
          }
        } catch (error) {
          console.error('Error polling download progress:', error)
          lastError.value = 'Lost connection to download progress'
          // Remove from progress tracking on connection error
          downloadProgress.value.delete(videoId)
        }
      }

      // Start polling
      poll()
    } catch (error) {
      console.error('Failed to start progress polling:', error)
    }
  }

  async function deleteVideo(videoId: string): Promise<CacheOperationResult> {
    lastError.value = null

    try {
      const api = await waitForPywebview()
      const result = await api.delete_cached_video(videoId)

      if (result.status === 'success') {
        // Refresh cache info after deletion
        await loadCacheInfo()
      }

      return result as CacheOperationResult
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Unknown error'
      lastError.value = errorMsg
      return {
        status: 'error',
        message: errorMsg
      }
    }
  }

  async function purgeCache(options: CachePurgeOptions = {}): Promise<CacheOperationResult> {
    lastError.value = null

    try {
      const api = await waitForPywebview()
      const result = await api.purge_cache(options)

      if (result.status === 'success') {
        // Refresh cache info after purge
        await loadCacheInfo()
      }

      return result as CacheOperationResult
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Unknown error'
      lastError.value = errorMsg
      return {
        status: 'error',
        message: errorMsg
      }
    }
  }

  async function selectVideoFromCache(videoId: string): Promise<CachedVideo | null> {
    const video = cachedVideos.value.find(v => v.id === videoId)
    if (video) {
      // Update last accessed time
      try {
        const api = await waitForPywebview()
        await api.update_video_access_time(videoId)
        // Refresh cache info to update the access time
        await loadCacheInfo()
      } catch (error) {
        console.warn('Failed to update access time:', error)
      }
    }
    return video ?? null
  }

  function getVideoById(videoId: string): CachedVideo | null {
    return cachedVideos.value.find(v => v.id === videoId) ?? null
  }

  function formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  function formatDuration(seconds: number): string {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = Math.floor(seconds % 60)

    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    } else {
      return `${minutes}:${secs.toString().padStart(2, '0')}`
    }
  }

  // Clear error when new operations start
  function clearError(): void {
    lastError.value = null
  }

  // Clear downloads with error status
  function clearErrorDownloads(): void {
    for (const [videoId, progress] of downloadProgress.value.entries()) {
      if (progress.status === 'error') {
        downloadProgress.value.delete(videoId)
      }
    }
  }

  return {
    // State
    cacheInfo,
    downloadProgress,
    isLoading,
    lastError,

    // Getters
    cachedVideos,
    totalCachedSize,
    totalCachedCount,
    cacheDirectory,
    maxCacheSize,
    activeDownloads,
    isDownloading,

    // Actions
    loadCacheInfo,
    downloadVideo,
    deleteVideo,
    purgeCache,
    selectVideoFromCache,
    getVideoById,
    formatFileSize,
    formatDuration,
    clearError,
    clearErrorDownloads
  }
})
