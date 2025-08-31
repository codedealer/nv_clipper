export type ParsedFilters = {
  brightness: number
  contrast: number
  saturation: number
  hue: number
  gamma: number
  advanced?: string
}

// Split a filter chain on commas only at top-level (outside quotes/parentheses)
export function splitTopLevelFilters(s: string): string[] {
  const parts: string[] = []
  let buf = ''
  let inSingle = false
  let inDouble = false
  let paren = 0
  for (let i = 0; i < s.length; i++) {
    const ch = s[i]
    if (ch === "'" && !inDouble) {
      inSingle = !inSingle
      buf += ch
      continue
    }
    if (ch === '"' && !inSingle) {
      inDouble = !inDouble
      buf += ch
      continue
    }
    if (!inSingle && !inDouble) {
      if (ch === '(') paren++
      else if (ch === ')' && paren > 0) paren--
      if (ch === ',' && paren === 0) {
        const part = buf.trim()
        if (part) parts.push(part)
        buf = ''
        continue
      }
    }
    buf += ch
  }
  const tail = buf.trim()
  if (tail) parts.push(tail)
  return parts
}

export function parseFilterString(filterString: string): ParsedFilters {
  const out: ParsedFilters = {
    brightness: 0,
    contrast: 1,
    saturation: 1,
    hue: 0,
    gamma: 1,
    advanced: undefined,
  }

  const filters = splitTopLevelFilters(filterString)
  for (const filter of filters) {
    const trimmed = filter.trim()

    if (trimmed.startsWith('hue=')) {
      const params = trimmed.substring(4).split(':')
      for (const param of params) {
        const [key, value] = param.split('=')
        const numValue = parseFloat(value)
        switch (key) {
          case 'b':
            out.brightness = numValue / 10
            break
          case 's':
            out.saturation = numValue
            break
          case 'h':
            out.hue = numValue
            break
        }
      }
      continue
    }

    if (trimmed.startsWith('lutyuv=')) {
      const afterEq = trimmed.substring('lutyuv='.length)
      const s = afterEq.replace(/^"|^'|"$|'$/g, '')
      const gammaMatch = s.match(/y\s*=\s*gammaval\(([^)]+)\)/)
      if (gammaMatch) {
        const g = parseFloat(gammaMatch[1])
        if (!Number.isNaN(g) && g > 0) out.gamma = 1 / g
        continue
      }
      const contrastMinMax = s.match(/y\s*=\s*'?min\(max\(\(val-\(maxval\+minval\)\/2\)\*([0-9.]+)\+\(maxval\+minval\)\/2\s*,\s*minval\)\s*,\s*maxval\)('?)/)
      if (contrastMinMax) {
        const c = parseFloat(contrastMinMax[1])
        if (!Number.isNaN(c)) out.contrast = c
        continue
      }
      const contrastClip = s.match(/y\s*=\s*'?clip\(\(val-\(maxval\+minval\)\/2\)\*([0-9.]+)\+\(maxval\+minval\)\/2\)'?/)
      if (contrastClip) {
        const c = parseFloat(contrastClip[1])
        if (!Number.isNaN(c)) out.contrast = c
        continue
      }
      continue
    }

    if (trimmed.startsWith('colorbalance=') || trimmed.startsWith('lutrgb=')) {
      out.advanced = trimmed
      continue
    }

    if (trimmed.startsWith('eq=')) {
      const params = trimmed.substring(3).split(':')
      for (const param of params) {
        const [key, value] = param.split('=')
        const numValue = parseFloat(value)
        switch (key) {
          case 'brightness':
            out.brightness = numValue
            break
          case 'contrast':
            out.contrast = numValue
            break
          case 'saturation':
            out.saturation = numValue
            break
          case 'gamma':
            out.gamma = numValue > 0 ? 1 / numValue : numValue
            break
        }
      }
      continue
    }
  }

  return out
}

export function joinFilters(...parts: Array<string | undefined | null>): string {
  return parts.filter(Boolean).join(',')
}
