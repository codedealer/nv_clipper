// Utilities to build a Lift/Gamma/Gain (LGG) filter matching MLT's math using FFmpeg lutrgb expressions
// Reference: mlt/src/modules/plus/filter_lift_gamma_gain.c

export interface LGGParams {
  rlift: number
  glift: number
  blift: number
  rgamma: number
  ggamma: number
  bgamma: number
  rgain: number
  ggain: number
  bgain: number
}

export function clamp(x: number, lo: number, hi: number): number {
  return Math.min(Math.max(x, lo), hi)
}

export function hexToRgbNorm(hex: string): { r: number; g: number; b: number } {
  const s = hex.replace('#', '')
  const n = s.length === 3 ? s.split('').map((c) => c + c).join('') : s
  const int = parseInt(n, 16)
  const r = (int >> 16) & 255
  const g = (int >> 8) & 255
  const b = int & 255
  const sum = r + g + b || 1
  return { r: r / sum, g: g / sum, b: b / sum }
}

export interface LGGWheelInput {
  hex: string
  // Effective radial intensity from the wheel (0..1). Typically sat * amount from UI.
  strength: number // [0, 1]
  // Neutral slider value controlling overall band intensity regardless of hue (0..1). 0.5 = no change.
  neutral?: number
}

export interface LGGFromWheelsInput {
  lift: LGGWheelInput
  mid: LGGWheelInput
  gain: LGGWheelInput
}


// Extract hue angle in degrees [0,360)
function hexToHueDeg(hex: string): number {
  const s = hex.replace('#', '')
  const n = s.length === 3 ? s.split('').map((c) => c + c).join('') : s
  const int = parseInt(n, 16)
  const r = ((int >> 16) & 255) / 255
  const g = ((int >> 8) & 255) / 255
  const b = (int & 255) / 255
  const max = Math.max(r, g, b)
  const min = Math.min(r, g, b)
  const d = max - min
  let h = 0
  if (d === 0) h = 0
  else if (max === r) h = ((g - b) / d) % 6
  else if (max === g) h = (b - r) / d + 2
  else h = (r - g) / d + 4
  h *= 60
  if (h < 0) h += 360
  return h
}

// Shotcut V1 wheel mapping helpers
// Given wheel RGB [0,1] at V=1 and an effective amount a in [0,1],
// compute per-channel wheel value w in [0,1] with pivot at 0.5.
// w_c = 0.5 + a * 1.5 * (rgb_c - avg_rgb)
// Clamp to [0,1]. This yields w≈0.5 at center; near pure red: {1,0,0} -> {1,0,0} after clamp.
// (RGB-based mapping variant intentionally removed; using angle-based projection)

// Angle-based mapping: aligned axis remains neutral (base), complementary axes reduce.
// w_c = clamp(base - GAIN * amount * ((1 - cos(delta))/2), 0, 1)
const PROJECTION_GAIN = 1.5
function wheelAngleToW(angleDeg: number, amount: number, base: number): { wr: number; wg: number; wb: number } {
  const rad = Math.PI / 180
  const a = clamp(amount, 0, 1)
  const b = clamp(base, 0, 1)
  const del = (ax: number) => (1 - Math.cos((angleDeg - ax) * rad)) / 2 // 0..1
  const wr = clamp(b - PROJECTION_GAIN * a * del(0), 0, 1)
  const wg = clamp(b - PROJECTION_GAIN * a * del(120), 0, 1)
  const wb = clamp(b - PROJECTION_GAIN * a * del(240), 0, 1)
  return { wr, wg, wb }
}

// Shotcut scaleWheelToValue V1 mapping: w in [0,1] -> value in [0.5, 2] with pivot at 0.5 => 1.0
function scaleWheelToValueV1(w: number): number {
  if (w < 0.5) return 0.5 + w
  if (w === 0.5) return 1.0
  return w * 2
}

export function lggParamsFromWheels(input: LGGFromWheelsInput): LGGParams {
  // Map color wheel + amount to per-channel parameters using Shotcut V1 semantics
  const liftHue = hexToHueDeg(input.lift.hex)
  const midHue = hexToHueDeg(input.mid.hex)
  const hiHue = hexToHueDeg(input.gain.hex)

  const la = clamp(Math.abs(input.lift.strength), 0, 1)
  const ma = clamp(Math.abs(input.mid.strength), 0, 1)
  const ha = clamp(Math.abs(input.gain.strength), 0, 1)
  const ln = input.lift.neutral !== undefined ? clamp(input.lift.neutral, 0, 1) : 0.5
  const mn = input.mid.neutral !== undefined ? clamp(input.mid.neutral, 0, 1) : 0.5
  const hn = input.gain.neutral !== undefined ? clamp(input.gain.neutral, 0, 1) : 0.5

  const lw = wheelAngleToW(liftHue, la, ln)
  const mw = wheelAngleToW(midHue, ma, mn)
  const hw = wheelAngleToW(hiHue, ha, hn)

  // Lift per channel in [-1, 1] -> Shotcut uses liftwheel.channelF * 2 - 1
  const rlift = +(lw.wr * 2 - 1).toFixed(6)
  const glift = +(lw.wg * 2 - 1).toFixed(6)
  const blift = +(lw.wb * 2 - 1).toFixed(6)

  // Gamma and Gain per channel (>0). Shotcut V1: w->[0.5..2] piecewise with 0.5->1
  const rgamma = +scaleWheelToValueV1(mw.wr).toFixed(6)
  const ggamma = +scaleWheelToValueV1(mw.wg).toFixed(6)
  const bgamma = +scaleWheelToValueV1(mw.wb).toFixed(6)

  const rgain = +scaleWheelToValueV1(hw.wr).toFixed(6)
  const ggain = +scaleWheelToValueV1(hw.wg).toFixed(6)
  const bgain = +scaleWheelToValueV1(hw.wb).toFixed(6)

  return { rlift, glift, blift, rgamma, ggamma, bgamma, rgain, ggain, bgain }
}

// Build a lutrgb filter string replicating MLT's math per channel.
// For a channel:
//   gamma22 = pow(val/maxval, 1/2.2)
//   x = gamma22 + lift*(1 - gamma22)
//   x = pow(max(x,0), 2.2/gamma)
//   x = x * pow(gain, 1.0/gamma)
//   out = clip(x*maxval, minval, maxval)
function channelExpr(lift: number, gamma: number, gain: number): string {
  const L = lift.toString()
  const G = gamma.toString()
  const A = gain.toString()
  // gamma22 = pow(val/maxval, 1/2.2)
  // x = gamma22 + L*(1 - gamma22)
  // x = pow(max(x,0), 2.2/G)
  // x = x * pow(A, 1.0/G)
  return `'min(max((pow(max(((pow((val/maxval),1/2.2))+(${L})*(1-(pow((val/maxval),1/2.2)))),0),(2.2/(${G})))*pow((${A}),(1.0/(${G}))))*maxval,minval),maxval)'`
}

export function buildLutrgbFromParams(p: LGGParams): string {
  const r = channelExpr(p.rlift, p.rgamma, p.rgain)
  const g = channelExpr(p.glift, p.ggamma, p.ggain)
  const b = channelExpr(p.blift, p.bgamma, p.bgain)
  return `lutrgb=r=${r}:g=${g}:b=${b}`
}

export function buildLggFilterFromWheels(input: LGGFromWheelsInput, globalGamma?: number): string {
  const params = lggParamsFromWheels(input)
  const isLiftNeutral = Math.abs(params.rlift) < 1e-6 && Math.abs(params.glift) < 1e-6 && Math.abs(params.blift) < 1e-6
  const isGammaNeutral = Math.abs(params.rgamma - 1) < 1e-6 && Math.abs(params.ggamma - 1) < 1e-6 && Math.abs(params.bgamma - 1) < 1e-6
  const isGainNeutral = Math.abs(params.rgain - 1) < 1e-6 && Math.abs(params.ggain - 1) < 1e-6 && Math.abs(params.bgain - 1) < 1e-6
  const parts: string[] = []
  // Only include lutrgb if any LGG band deviates from neutral
  if (!(isLiftNeutral && isGammaNeutral && isGainNeutral)) {
    parts.push(buildLutrgbFromParams(params))
  }
  // Global gamma is part of the advanced panel; include only if not neutral
  if (globalGamma !== undefined && Math.abs(globalGamma - 1) > 1e-6) {
    const g = +(1 / clamp(globalGamma, 0.1, 10)).toFixed(6)
    parts.push(`lutyuv=y=gammaval(${g})`)
  }
  return parts.join(',')
}
