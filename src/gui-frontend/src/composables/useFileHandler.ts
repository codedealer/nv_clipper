import { computed } from 'vue'
import { ElMessage } from 'element-plus'
import type { UploadFile } from 'element-plus'
import { useClipperStore } from '@/stores/counter'
import { useVideoOperations } from './useVideoOperations'
import { useMarkupOperations } from './useMarkupOperations'
import type { CachedVideo } from '@/types/cache'
import {
  UI_MESSAGES,
  ELEMENT_CONFIGS
} from '@/constants'

/**
 * Composable for handling file selection, validation, and processing operations
 */
export function useFileHandler(
  markupOps?: ReturnType<typeof useMarkupOperations>,
  videoOps?: ReturnType<typeof useVideoOperations>
) {
  // Stores and composables
  const clipperStore = useClipperStore()

  // Use passed instances or create new ones (for backward compatibility)
  const { getVideoInfo, createMockMarkupForVideo, clearVideoState, isVideoFile, hasValidVideoInfo } = videoOps || useVideoOperations()
  const { parseMarkupFile, setMarkupData, isMarkupFile, resetMarkupState, hasValidMarkup } = markupOps || useMarkupOperations()

  // Computed properties from store
  const selectedFiles = computed(() => clipperStore.selectedFiles)
  const isProcessing = computed(() => clipperStore.isProcessing)
  const hasMarkupFile = computed(() => clipperStore.hasMarkupFile)
  const hasVideoFile = computed(() => clipperStore.hasVideoFile)

  // Guard against races when files are changed while async work is in-flight
  let selectionOpId = 0

  /**
   * Process can start if we have markup or clips and selected clips, and not already processing
   */
  const canProcess = computed(() =>
    (hasMarkupFile.value || hasValidMarkup()) && !isProcessing.value
  )

  /**
   * Handle multiple selected files from dialog or drag/drop
   */
  async function handleSelectedFiles(filePaths: string[]): Promise<void> {
    // Start a new selection operation; invalidates in-flight work
    const opId = ++selectionOpId
    const newFiles = { markup: null as string | null, video: null as string | null }

    // Categorize files
    for (const filePath of filePaths) {
      if (isMarkupFile(filePath)) {
        newFiles.markup = filePath
      } else if (isVideoFile(filePath)) {
        newFiles.video = filePath
      }
    }

    // Update store with new files
    if (newFiles.markup) {
      clipperStore.setMarkupFile(newFiles.markup)
      resetMarkupState() // Clear any mock markup when real markup is selected
    }

    if (newFiles.video) {
      clipperStore.setVideoFile(newFiles.video)

      // Get video info for the new video file
      try {
        await getVideoInfo(newFiles.video)
      } catch (error) {
        console.error('Failed to get video info:', error)
        // Don't fail the entire operation, just log the error
      }
    }

    // Handle markup and mock markup logic
    if (newFiles.markup || clipperStore.selectedFiles.markup) {
      // Parse real markup file
      const markupPath = newFiles.markup || clipperStore.selectedFiles.markup
      if (markupPath) {
        await parseMarkupFile(markupPath)
      }
    } else if (newFiles.video && !hasMarkupFile.value) {
      // Create mock markup for video-only scenario; apply only if this op is still current
      if (opId === selectionOpId) {
        await handleMockMarkupCreation(newFiles.video)
      }
    }
  }  /**
   * Handle file selection via file dialog
   */
  async function handleSelectFiles(): Promise<void> {
    try {
      const files = await clipperStore.selectFiles()
      if (files && files.length > 0) {
        await handleSelectedFiles(files)
      }
    } catch (error) {
      console.error('File selection failed:', error)
      ElMessage.error(UI_MESSAGES.FILE_SELECTION_FAILED)
    }
  }

  /**
   * Handle file change from upload component
   */
  async function handleFileChange(file: UploadFile): Promise<void> {
    if (!file.raw) return

    // In a real implementation, we'd handle file paths properly
    // For now, use the file name as a placeholder
    if (isMarkupFile(file.name)) {
      clipperStore.setMarkupFile(file.name)
      await parseMarkupFile(file.name)
    } else if (isVideoFile(file.name)) {
      clipperStore.setVideoFile(file.name)
      await getVideoInfo(file.name)
    }

    ElMessage.success(`Added ${file.name}`)
  }

  /**
   * Clear markup file and create mock markup if video exists
   */
  async function clearMarkupFile(): Promise<void> {
    // Invalidate any in-flight operations tied to previous selection
    selectionOpId++
    clipperStore.setMarkupFile(null)
    resetMarkupState()

    // If we still have a video file, create mock markup as fallback
    if (hasVideoFile.value && clipperStore.selectedFiles.video) {
      ElMessage.info('Markup file removed - creating mock markup for video')
      await handleMockMarkupCreation(clipperStore.selectedFiles.video)
    }
  }

  /**
   * Clear video file and related state
   */
  function clearVideoFile(): void {
    // Invalidate any in-flight operations tied to previous selection
    selectionOpId++
    clipperStore.setVideoFile(null)
    clearVideoState()
  // Do NOT reset markup state; allow color grading with markup-only
  }

  /**
   * Handle video selection from cache or external source
   */
  async function selectVideoAndUpdateUI(video: CachedVideo): Promise<void> {
    const opId = ++selectionOpId
    clipperStore.setVideoFile(video.file_path)

    // Get video info for the selected video
    try {
      await getVideoInfo(video.file_path)
    } catch (error) {
      console.error('Failed to get video info:', error)
    }

    // Create mock markup if no markup file exists
    if (!hasMarkupFile.value && opId === selectionOpId) {
      await handleMockMarkupCreation(video.file_path)
    }

    ElMessage.success({
      message: UI_MESSAGES.VIDEO_SELECTED(video.title),
      duration: ELEMENT_CONFIGS.MESSAGE_DURATION
    })
  }  /**
   * Handle mock markup creation for video-only scenarios
   */
  async function handleMockMarkupCreation(videoPath: string): Promise<void> {
    const opId = selectionOpId
    try {
      const mockResult = await createMockMarkupForVideo(videoPath, hasValidVideoInfo ? undefined : null)

      if (mockResult && opId === selectionOpId) {
        setMarkupData(mockResult.markupData, mockResult.clips)
      }
    } catch (error) {
      console.error('Failed to create mock markup:', error)
      ElMessage.error('Failed to create mock markup for video')
    }
  }

  /**
   * Start processing with current selection and markup data
   */
  async function handleProcessFiles(selectedClips: number[], markupData?: Record<string, unknown>): Promise<void> {
    if (!canProcess.value) {
      ElMessage.warning('Cannot start processing: missing required files or already processing')
      return
    }

    try {
  if (markupData) {
        // Use provided markup data (modified or mock)
        await clipperStore.startProcessing(selectedClips, markupData)
      } else if (clipperStore.selectedFiles.markup) {
        // Use real markup file with no modifications
        await clipperStore.startProcessing(selectedClips)
      } else {
        throw new Error('No markup file or data available for processing')
      }
  // Rely on push events for completion toasts
    } catch (error) {
      console.error('Processing failed:', error)
      ElMessage.error(UI_MESSAGES.PROCESSING_FAILED)
    }
  }

  return {
    // Computed properties
    selectedFiles,
    isProcessing,
    hasMarkupFile,
    hasVideoFile,
    canProcess,

    // File handling methods
    handleSelectedFiles,
    handleSelectFiles,
    handleFileChange,
    clearMarkupFile,
    clearVideoFile,
    selectVideoAndUpdateUI,
    handleProcessFiles
  }
}
