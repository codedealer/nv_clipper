import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type { SelectedFiles, ProcessingResult, EngineStatus, ParseMarkupResult, JobStatus } from '@/types/api'
import { waitForPywebview } from '@/utils/api'
import { useSettingsStore } from './settings'

export const useClipperStore = defineStore('clipper', () => {
  // State
  const selectedFiles = ref<SelectedFiles>({
    markup: null,
    video: null
  })

  const isProcessing = ref(false)
  const isCanceling = ref(false)
  const currentJobId = ref<string | null>(null)
  const processingStatus = ref<string>('')
  const processingResult = ref<ProcessingResult | null>(null)
  const engineStatus = ref<EngineStatus | null>(null)

  // Getters
  const hasMarkupFile = computed(() => !!selectedFiles.value.markup)
  const hasVideoFile = computed(() => !!selectedFiles.value.video)
  const canProcess = computed(() => hasMarkupFile.value && !isProcessing.value && !isCanceling.value)

  // Actions
  function setSelectedFiles(files: SelectedFiles) {
    selectedFiles.value = files
  }

  function setMarkupFile(path: string | null) {
    selectedFiles.value.markup = path
  }

  function setVideoFile(path: string | null) {
    selectedFiles.value.video = path
  }

  function clearSelectedFiles() {
    selectedFiles.value = {
      markup: null,
      video: null
    }
  }

  async function startProcessing(selectedClips?: number[], markupData?: Record<string, unknown>): Promise<ProcessingResult> {
    if (!canProcess.value && !markupData) {
      throw new Error('Cannot start processing: no markup file selected or already processing')
    }

    isProcessing.value = true
    isCanceling.value = false
    processingStatus.value = 'Starting processing...'
    currentJobId.value = null
    processingResult.value = null

    try {
      const api = await waitForPywebview()

      // Use settings store to get current settings
      const settingsStore = useSettingsStore()

      // Ensure settings are loaded
      if (!settingsStore.hasSettings) {
        await settingsStore.loadAllSettings()
      }

      const result = await api.process_files(
        selectedFiles.value.markup || undefined,
        selectedFiles.value.video || undefined,
        selectedClips || undefined,
        markupData || undefined
      )

      if (result.status === 'accepted' && result.job_id) {
        currentJobId.value = result.job_id
        processingStatus.value = 'Processing files...'
        // From here we rely entirely on push events
        return result
      }

      // Immediate completion (success/error)
      processingResult.value = result
      processingStatus.value = result.message
      isProcessing.value = false
      currentJobId.value = null
      return result
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      processingResult.value = {
        status: 'error',
        message: errorMessage
      }
      processingStatus.value = `Processing failed: ${errorMessage}`
      isProcessing.value = false
      currentJobId.value = null
      throw error
    }
  }

  // Handle backend push events
  function onProcessingEvent(payload: JobStatus & { job_id: string }): void {
    if (!payload || !payload.job_id) return
    if (payload.job_id !== currentJobId.value) return

    if (payload.status === 'starting' || payload.status === 'processing') {
      processingStatus.value = payload.message || 'Processing...'
      isProcessing.value = true
      return
    }

    if (payload.status === 'success') {
      processingResult.value = {
        status: 'success',
        message: payload.message || 'Processing completed',
        report: payload.report,
        output_path: payload.output_path
      }
      processingStatus.value = payload.message || 'Processing completed successfully'
      isProcessing.value = false
      isCanceling.value = false
      currentJobId.value = null
      return
    }

    if (payload.status === 'error') {
      processingResult.value = {
        status: 'error',
        message: payload.message || 'Processing failed'
      }
      processingStatus.value = payload.message || 'Processing failed'
      isProcessing.value = false
      isCanceling.value = false
      currentJobId.value = null
      return
    }

    if (payload.status === 'canceled') {
      processingResult.value = {
        status: 'canceled',
        message: payload.message || 'Processing canceled'
      }
      processingStatus.value = payload.message || 'Processing canceled'
      isProcessing.value = false
      isCanceling.value = false
      currentJobId.value = null
      return
    }
  }

  async function cancelCurrentJob(): Promise<void> {
    if (!currentJobId.value) return
    try {
      const api = await waitForPywebview()
      isCanceling.value = true
      processingStatus.value = 'Canceling...'
      await api.cancel_processing(currentJobId.value)
      // We expect a push event to arrive
    } catch (e) {
      console.error('Cancel failed', e)
      isCanceling.value = false
    }
  }

  async function getEngineStatus(): Promise<EngineStatus> {
    try {
      const api = await waitForPywebview()
      const status = await api.get_status()
      engineStatus.value = status
      return status
    } catch (error) {
      throw new Error(`Failed to get engine status: ${error}`)
    }
  }

  async function selectFiles(): Promise<string[]> {
    try {
      const api = await waitForPywebview()
      return await api.select_files()
    } catch (error) {
      throw new Error(`File selection failed: ${error}`)
    }
  }

  async function parseMarkupFile(filePath: string): Promise<ParseMarkupResult> {
    try {
      const api = await waitForPywebview()
      return await api.parse_markup_file(filePath)
    } catch (error) {
      throw new Error(`Failed to parse markup file: ${error}`)
    }
  }

  return {
    // State
    selectedFiles,
    isProcessing,
    isCanceling,
    currentJobId,
    processingStatus,
    processingResult,
    engineStatus,

    // Getters
    hasMarkupFile,
    hasVideoFile,
    canProcess,

    // Actions
    setSelectedFiles,
    setMarkupFile,
    setVideoFile,
    clearSelectedFiles,
    startProcessing,
    getEngineStatus,
    selectFiles,
    parseMarkupFile,
    onProcessingEvent,
    cancelCurrentJob
  }
})
