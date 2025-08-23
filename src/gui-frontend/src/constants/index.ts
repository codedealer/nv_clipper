/**
 * Application constants and configuration values
 */

// File Extensions
export const SUPPORTED_VIDEO_EXTENSIONS = ['mp4', 'webm', 'avi', 'mkv', 'mov'] as const
export const SUPPORTED_MARKUP_EXTENSIONS = ['json'] as const

// Dialog Configuration
export const DIALOG_WIDTHS = {
  VIDEO_CACHE: '80%',
  SETTINGS: '900px'
} as const

// Header Configuration
export const HEADER_HEIGHT = '60px'
export const SIDEBAR_WIDTH = '350px'

// Processing Configuration
export const PROCESSING_POLL_INTERVAL = 1000 // 1 second
export const PROCESSING_MAX_ATTEMPTS = 300 // 5 minutes max

// Mock Markup Configuration
export const MOCK_MARKUP_DEFAULTS = {
  PLATFORM: 'ytc_generic',
  VIDEO_ID: 'unknown',
  VIDEO_TAG: '[ytc_generic@unknown]',
  NEW_MARKER_SPEED: 1,
  NEW_MARKER_CROP: '',
  VERSION: '0.0.0',
  CROP_PRESET: '0:0:iw:ih',
  DEFAULT_RESOLUTION: {
    width: 1920,
    height: 1080
  }
} as const

// UI Messages
export const UI_MESSAGES = {
  FILE_SELECTION_FAILED: 'File selection failed',
  PROCESSING_STARTED: 'Processing started successfully',
  PROCESSING_FAILED: 'Processing failed to start',
  MOCK_MARKUP_CREATING: 'Creating mock markup for video file...',
  MOCK_MARKUP_CREATED: (name: string, duration: number) => `Created mock markup for ${name} (${Math.round(duration)}s)`,
  MOCK_MARKUP_FAILED: 'Failed to create mock markup: ',
  VIDEO_SELECTED: (title: string) => `Selected: ${title}`,
  CLIP_SWITCHED: (index: number) => `Switched to clip ${index + 1} for color grading`,
  COLOR_GRADING_APPLIED: 'Color grading applied to clip',
  COLOR_GRADING_REMOVED: 'Color grading removed from clip',
  CLIP_NOT_FOUND: 'Clip not found',
  SETTINGS_UPDATED: (key: string) => `Updated ${key}`,
  SETTINGS_UPDATE_FAILED: (key: string) => `Failed to update ${key}`,
  SETTINGS_RESET: 'Settings reset to defaults',
  SETTINGS_RESET_FAILED: 'Failed to reset settings',
  SETTINGS_EXPORTED: (path: string) => `Settings exported to ${path}`,
  SETTINGS_EXPORT_FAILED: 'Failed to export settings',
  IMPORT_COMING_SOON: 'Import from args file feature coming soon...'
} as const

// Status Configuration
export const ENGINE_STATUS = {
  READY: 'Ready',
  INITIALIZING: 'Initializing...',
  LOADING: 'Loading...'
} as const

// Element Plus Configuration
export const ELEMENT_CONFIGS = {
  MESSAGE_DURATION: 3000,
  TAG_SIZE: 'large'
} as const

export type SupportedVideoExtension = typeof SUPPORTED_VIDEO_EXTENSIONS[number]
export type SupportedMarkupExtension = typeof SUPPORTED_MARKUP_EXTENSIONS[number]
