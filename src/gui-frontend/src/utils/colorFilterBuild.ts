import type { ColorGradingState } from '@/types/colorGrading'
import { buildBasicFilter } from '@/utils/colorBasics'
import { buildLggFilterFromWheels } from '@/utils/lgg'
import { useSettingsStore } from '@/stores/settings'
import { joinFilters } from '@/utils/filterString'

export function buildFilterFromState(state: ColorGradingState): string {
  // Read projection gain from settings (fallback to default 1.5 if not loaded yet)
  let projectionGain = 1.5
  try {
    const settings = useSettingsStore()
    projectionGain = settings.generalSettings?.lgg_projection_gain ?? 1.5
  } catch {
    // store may not be initialized in some isolated usage contexts; ignore
  }
  const b = state.basic
  const basic = buildBasicFilter({
    brightness: b.brightness,
    contrast: b.contrast,
    saturation: b.saturation,
    hue: b.hue,
    gamma: b.gamma,
  })
  const w = state.lgg
  const adv = buildLggFilterFromWheels({
    lift: { hex: w.lift.hex, strength: w.lift.sat, neutral: w.lift.amount },
    mid: { hex: w.mid.hex, strength: w.mid.sat, neutral: w.mid.amount },
    gain: { hex: w.gain.hex, strength: w.gain.sat, neutral: w.gain.amount },
  }, w.globalGamma, projectionGain)
  return joinFilters(basic, adv)
}