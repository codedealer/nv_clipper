export interface BasicColorState {
  brightness: number
  contrast: number
  saturation: number
  hue: number
  gamma: number
}

export interface LggWheelBandState {
  hex: string
  sat: number // radial saturation/strength 0..1
  amount: number // neutral-centered slider 0..1 (0.5 = neutral)
}

export interface LggWheelState {
  lift: LggWheelBandState
  mid: LggWheelBandState
  gain: LggWheelBandState
  globalGamma: number
}

export interface ColorGradingState {
  basic: BasicColorState
  lgg: LggWheelState
}

export function createDefaultColorGradingState(): ColorGradingState {
  return {
    basic: { brightness: 0, contrast: 1, saturation: 1, hue: 0, gamma: 1 },
    lgg: {
      lift: { hex: '#ffffff', sat: 0, amount: 0.5 },
      mid: { hex: '#ffffff', sat: 0, amount: 0.5 },
      gain: { hex: '#ffffff', sat: 0, amount: 0.5 },
      globalGamma: 1,
    },
  }
}

export function cloneColorGradingState(src: ColorGradingState): ColorGradingState {
  return JSON.parse(JSON.stringify(src))
}
