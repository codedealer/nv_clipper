import type { ColorGradingState } from '@/types/colorGrading'
import { buildBasicFilter } from '@/utils/colorBasics'
import { buildLggFilterFromWheels } from '@/utils/lgg'
import { joinFilters } from '@/utils/filterString'

export function buildFilterFromState(state: ColorGradingState): string {
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
  }, w.globalGamma)
  return joinFilters(basic, adv)
}