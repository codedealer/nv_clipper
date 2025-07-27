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

// Pywebview API interface
declare global {
  interface Window {
    pywebview: {
      api: {
        process_files: (markupPath: string, videoPath?: string) => Promise<ProcessingResult>
        get_job_status: (jobId: string) => Promise<JobStatus>
        get_status: () => Promise<EngineStatus>
        select_files: () => Promise<string[]>
        cleanup_old_jobs: () => Promise<{ cleaned: number }>
      }
    }
  }
}
