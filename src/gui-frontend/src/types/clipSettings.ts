export type LoopOption = 'none' | 'fwrev' | 'fade'

export type VideoEnhancementModel = 'Proteus' | 'Iris'

export interface VideoStabilizationOverride {
  enabled: boolean
  desc?: string
  shakiness?: number
  smoothing?: number
}

export interface ClipSettingsOverrides {
  loop?: LoopOption
  minterpMode?: string | boolean
  minterpProvider?: string
  mirror?: boolean
  videoStabilization?: VideoStabilizationOverride
  videoStabilizationDynamicZoom?: boolean
  videoStabilizationRollingShutter?: boolean
  videoStabilizationJitteryMotion?: boolean
  videoEnhancementEnabled?: boolean
  videoEnhancementModel?: VideoEnhancementModel
  videoEnhancementCompression?: number
  videoEnhancementDetails?: number
  videoEnhancementBlur?: number
  videoEnhancementNoise?: number
  videoEnhancementHalo?: number
  videoEnhancementPreblur?: number
  videoEnhancementBlend?: number
  videoEnhancementPrenoise?: number
}

export interface ClipSettingsState {
  speed: number
  overrides: ClipSettingsOverrides
  effectiveOverrides: ClipSettingsOverrides
}

export interface ClipSettingsUpdatePayload {
  speed?: number | null
  overrides?: Partial<ClipSettingsOverrides>
}
