import { ref, computed, readonly } from 'vue'
import { ElMessage } from 'element-plus'
import type { VideoInfo, ClipInfo } from '@/types/api'
import type { MarkupData } from '@/utils/markup'
import { SUPPORTED_VIDEO_EXTENSIONS, MOCK_MARKUP_DEFAULTS, UI_MESSAGES } from '@/constants'

/**
 * Composable for video-related operations including video info fetching,
 * duration management, and mock markup creation
 */
export function useVideoOperations() {
  // State
  const videoDuration = ref<number | null>(null)
  const videoInfo = ref<VideoInfo | null>(null)
  const isCreatingMockMarkup = ref(false)

  // Computed
  const hasValidVideoInfo = computed(() =>
    videoInfo.value !== null && videoDuration.value !== null && videoDuration.value > 0
  )

  /**
   * Get video information from a video file path
   */
  async function getVideoInfo(videoPath: string): Promise<VideoInfo | null> {
    try {
      const response = await window.pywebview.api.get_video_info(videoPath)

      if (response.status === 'success' && response.video_info) {
        videoInfo.value = response.video_info
        videoDuration.value = response.video_info.duration ?? null
        return response.video_info
      } else {
        throw new Error(response.message || 'Failed to get video information')
      }
    } catch (error) {
      console.error('Failed to get video info:', error)
      ElMessage.error(`Failed to get video info: ${error}`)
      return null
    }
  }

  /**
   * Create mock markup data for video-only scenarios
   */
  async function createMockMarkupForVideo(
    videoPath: string,
    existingVideoInfo?: VideoInfo | null
  ): Promise<{ markupData: MarkupData; clips: ClipInfo[] } | null> {
    // Prevent concurrent calls
    if (isCreatingMockMarkup.value) {
      return null
    }

    try {
      isCreatingMockMarkup.value = true
      ElMessage.info(UI_MESSAGES.MOCK_MARKUP_CREATING)

      // Use existing video info if available, otherwise fetch it
      let currentVideoInfo = existingVideoInfo || videoInfo.value

      if (!currentVideoInfo) {
        const fetchedInfo = await getVideoInfo(videoPath)
        if (!fetchedInfo) {
          throw new Error('Failed to get video information for mock markup')
        }
        currentVideoInfo = fetchedInfo
      }

      const duration = currentVideoInfo.duration
      if (!duration || duration <= 0) {
        throw new Error('Video duration not available or invalid')
      }

      const videoName = videoPath.split(/[/\\]/).pop()?.replace(/\.[^/.]+$/, '') || 'video'

      // Create a single clip that spans the entire video
      const mockClip: ClipInfo = {
        number: 1,
        title: `Full Video - ${videoName}`,
        start: 0,
        end: duration,
        duration: duration,
        speed: 1.0,
        crop: '',
        enableZoomPan: false,
        overrides: {}
      }

      // Extract directory from video path for output location
      const videoDir = videoPath.substring(0, videoPath.lastIndexOf(/[/\\]/.exec(videoPath)?.[0] || '/'))

      // Create mock markup data structure that follows the proper schema
      const mockMarkupData: MarkupData = {
        platform: MOCK_MARKUP_DEFAULTS.PLATFORM,
        videoID: MOCK_MARKUP_DEFAULTS.VIDEO_ID,
        videoTitle: videoName,
        videoUrl: '',
        videoTag: MOCK_MARKUP_DEFAULTS.VIDEO_TAG,
        newMarkerSpeed: MOCK_MARKUP_DEFAULTS.NEW_MARKER_SPEED,
        newMarkerCrop: MOCK_MARKUP_DEFAULTS.NEW_MARKER_CROP,
        titleSuffix: videoName,
        isVerticalVideo: false,
        markerPairMergeList: '',
        cropResWidth: currentVideoInfo.width || MOCK_MARKUP_DEFAULTS.DEFAULT_RESOLUTION.width,
        cropResHeight: currentVideoInfo.height || MOCK_MARKUP_DEFAULTS.DEFAULT_RESOLUTION.height,
        cropRes: `${currentVideoInfo.width || MOCK_MARKUP_DEFAULTS.DEFAULT_RESOLUTION.width}x${currentVideoInfo.height || MOCK_MARKUP_DEFAULTS.DEFAULT_RESOLUTION.height}`,
        version: MOCK_MARKUP_DEFAULTS.VERSION,
        markerPairs: [{
          number: 1,
          start: 0,
          end: duration,
          speed: 1,
          crop: MOCK_MARKUP_DEFAULTS.CROP_PRESET,
          enableZoomPan: false,
          overrides: {}
        }],
        totalDuration: duration,
        outputDirectory: videoDir
      }

      ElMessage.success(UI_MESSAGES.MOCK_MARKUP_CREATED(videoName, duration))

      return {
        markupData: mockMarkupData,
        clips: [mockClip]
      }

    } catch (error) {
      console.error('Failed to create mock markup:', error)
      ElMessage.error(UI_MESSAGES.MOCK_MARKUP_FAILED + error)
      return null
    } finally {
      isCreatingMockMarkup.value = false
    }
  }

  /**
   * Find the first clip with valid timestamps relative to video duration
   */
  function findFirstValidClip(clips: ClipInfo[], duration: number | null): number | null {
    if (clips.length === 0) return null

    // If no video duration info, use first clip
    if (!duration || duration <= 0) return 0

    // Find first clip that starts within video bounds
    for (let i = 0; i < clips.length; i++) {
      const clip = clips[i]
      if (clip.start < duration) {
        return i
      }
    }

    // If no valid clips found, still return 0 but the ColorGradingPanel will handle bounds
    return 0
  }

  /**
   * Clear all video-related state
   */
  function clearVideoState() {
    videoDuration.value = null
    videoInfo.value = null
  }

  /**
   * Extract video filename from path
   */
  function getVideoFileName(path: string): string {
    return path.split(/[/\\]/).pop()?.replace(/\.[^/.]+$/, '') || 'video'
  }

  /**
   * Check if file extension is a supported video format
   */
  function isVideoFile(filename: string): boolean {
    const extension = filename.split('.').pop()?.toLowerCase()
    if (!extension) return false
    return (SUPPORTED_VIDEO_EXTENSIONS as readonly string[]).includes(extension)
  }

  return {
    // State
    videoDuration: readonly(videoDuration),
    videoInfo: readonly(videoInfo),
    isCreatingMockMarkup: readonly(isCreatingMockMarkup),

    // Computed
    hasValidVideoInfo,

    // Methods
    getVideoInfo,
    createMockMarkupForVideo,
    findFirstValidClip,
    clearVideoState,
    getVideoFileName,
    isVideoFile
  }
}
