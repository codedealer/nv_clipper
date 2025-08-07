import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type { SelectedFiles, ProcessingResult, EngineStatus, ParseMarkupResult } from '@/types/api'
import { waitForPywebview } from '@/utils/api'
import { useSettingsStore } from './settings'

export const useClipperStore = defineStore('clipper', () => {
  // State
  const selectedFiles = ref<SelectedFiles>({
    markup: null,
    video: null
  })

  const isProcessing = ref(false)
  const currentJobId = ref<string | null>(null)
  const processingStatus = ref<string>('')
  const processingResult = ref<ProcessingResult | null>(null)
  const engineStatus = ref<EngineStatus | null>(null)

  // Getters
  const hasMarkupFile = computed(() => !!selectedFiles.value.markup)
  const hasVideoFile = computed(() => !!selectedFiles.value.video)
  const canProcess = computed(() => hasMarkupFile.value && !isProcessing.value)

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

  async function startProcessing(selectedClips?: number[]): Promise<ProcessingResult> {
    if (!canProcess.value) {
      throw new Error('Cannot start processing: no markup file selected or already processing')
    }

    isProcessing.value = true
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
        selectedFiles.value.markup!,
        selectedFiles.value.video || undefined,
        selectedClips || undefined
      )

      if (result.status === 'accepted' && result.job_id) {
        currentJobId.value = result.job_id
        processingStatus.value = 'Processing files...'

        // Start polling for status
        await pollJobStatus(result.job_id)
      } else {
        processingResult.value = result
        processingStatus.value = result.message
      }

      return result
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      processingResult.value = {
        status: 'error',
        message: errorMessage
      }
      processingStatus.value = `Processing failed: ${errorMessage}`
      throw error
    } finally {
      isProcessing.value = false
      currentJobId.value = null
    }
  }

  async function pollJobStatus(jobId: string): Promise<void> {
    const pollInterval = 1000 // 1 second
    const maxAttempts = 300 // 5 minutes max

    for (let attempts = 0; attempts < maxAttempts; attempts++) {
      try {
        const api = await waitForPywebview()
        const status = await api.get_job_status(jobId)

        if (status.status === 'processing') {
          processingStatus.value = status.message || 'Processing...'
        } else if (status.status === 'success') {
          processingResult.value = {
            status: 'success',
            message: status.message || 'Processing completed',
            report: status.report,
            output_path: status.output_path
          }
          processingStatus.value = status.message || 'Processing completed successfully'
          return // Job completed successfully
        } else if (status.status === 'error') {
          processingResult.value = {
            status: 'error',
            message: status.message || 'Processing failed'
          }
          processingStatus.value = status.message || 'Processing failed'
          return // Job completed with error
        }

        // Wait before next poll
        await new Promise(resolve => setTimeout(resolve, pollInterval))
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error'
        processingResult.value = {
          status: 'error',
          message: `Failed to get job status: ${errorMessage}`
        }
        processingStatus.value = `Status polling failed: ${errorMessage}`
        return
      }
    }

    // Timeout reached
    processingResult.value = {
      status: 'error',
      message: 'Processing timeout - job may still be running'
    }
    processingStatus.value = 'Processing timeout'
  }

  async function getEngineStatus(): Promise<EngineStatus> {
    try {
      // Wait for pywebview to be ready first
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
    parseMarkupFile
  }
})
