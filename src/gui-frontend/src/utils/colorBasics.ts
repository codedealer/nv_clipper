// Build basic color adjustment FFmpeg filters

export interface BasicParams {
  brightness: number // [-0.5,0.5]
  contrast: number // [0,3]
  saturation: number // [0,3]
  hue: number // [-180,180]
  gamma: number // [0.1,3] UI (inverse applied in lutyuv)
}

export function buildBasicFilter(p: BasicParams): string {
  const filters: string[] = []

  const hueParams: string[] = []
  if (p.brightness !== 0) hueParams.push(`b=${(p.brightness * 10).toFixed(3).replace(/\.0+$/, '')}`)
  if (p.saturation !== 1) hueParams.push(`s=${p.saturation.toFixed(2)}`)
  if (p.hue !== 0) hueParams.push(`h=${p.hue}`)
  if (hueParams.length > 0) filters.push(`hue=${hueParams.join(':')}`)

  if (p.gamma !== 1) {
    const uiG = Math.max(0.1, Math.min(10, Number(p.gamma.toFixed(3))))
    const g = Number((1 / uiG).toFixed(6))
    filters.push(`lutyuv=y=gammaval(${g})`)
  }

  if (p.contrast !== 1) {
    const c = Number(p.contrast.toFixed(3))
    const expr = `y='min(max((val-(maxval+minval)/2)*${c}+(maxval+minval)/2,minval),maxval)'`
    filters.push(`lutyuv=${expr}`)
  }

  return filters.join(',')
}
