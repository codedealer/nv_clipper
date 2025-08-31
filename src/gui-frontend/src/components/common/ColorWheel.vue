<template>
  <div class="color-wheel" :style="{ width: size + 'px', height: size + 'px' }" @pointerdown="onPointerDown" @pointermove="onPointerMove" @pointerup="onPointerUp" @pointerleave="onPointerUp">
    <canvas ref="canvasRef" class="wheel-canvas" :width="size" :height="size"></canvas>
    <div class="thumb" :style="thumbStyle"></div>
  </div>

</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

interface Props {
  modelValue: string
  size?: number
  markerSat?: number // 0..1 optional external control for thumb radius (e.g., intensity)
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '#ffffff',
  size: 140,
  markerSat: undefined,
})

const emit = defineEmits<{
  (e: 'update:modelValue', v: string): void
  (e: 'change', v: string): void
  (e: 'vector-change', payload: { hex: string; sat: number }): void
}>()

const canvasRef = ref<HTMLCanvasElement | null>(null)
const dragging = ref(false)

const center = computed(() => ({ x: props.size / 2, y: props.size / 2 }))
const radius = computed(() => props.size / 2)

function hsvToRgb(h: number, s: number, v: number): { r: number; g: number; b: number } {
  const c = v * s
  const x = c * (1 - Math.abs(((h / 60) % 2) - 1))
  const m = v - c
  let r = 0,
    g = 0,
    b = 0
  if (h < 60) {
    r = c
    g = x
  } else if (h < 120) {
    r = x
    g = c
  } else if (h < 180) {
    g = c
    b = x
  } else if (h < 240) {
    g = x
    b = c
  } else if (h < 300) {
    r = x
    b = c
  } else {
    r = c
    b = x
  }
  return { r: (r + m) * 255, g: (g + m) * 255, b: (b + m) * 255 }
}

function rgbToHex(r: number, g: number, b: number): string {
  const toHex = (n: number) => Math.round(Math.max(0, Math.min(255, n))).toString(16).padStart(2, '0')
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`
}

function hexToRgb(hex: string): { r: number; g: number; b: number } {
  const s = hex.replace('#', '')
  const n = s.length === 3 ? s.split('').map((c) => c + c).join('') : s
  const int = parseInt(n, 16)
  return { r: (int >> 16) & 255, g: (int >> 8) & 255, b: int & 255 }
}

function rgbToHsv(r: number, g: number, b: number): { h: number; s: number; v: number } {
  r /= 255
  g /= 255
  b /= 255
  const max = Math.max(r, g, b), min = Math.min(r, g, b)
  const d = max - min
  let h = 0
  if (d === 0) h = 0
  else if (max === r) h = ((g - b) / d) % 6
  else if (max === g) h = (b - r) / d + 2
  else h = (r - g) / d + 4
  h = Math.round(h * 60)
  if (h < 0) h += 360
  const s = max === 0 ? 0 : d / max
  const v = max
  return { h, s, v }
}

function drawWheel() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')!
  const { x: cx, y: cy } = center.value
  const R = radius.value
  const img = ctx.createImageData(canvas.width, canvas.height)
  const data = img.data
  for (let y = 0; y < canvas.height; y++) {
    for (let x = 0; x < canvas.width; x++) {
      const dx = x - cx
      const dy = y - cy
      const dist = Math.sqrt(dx * dx + dy * dy)
      const idx = (y * canvas.width + x) * 4
      if (dist <= R) {
        const sat = Math.min(1, dist / R)
        const angle = Math.atan2(dy, dx)
        const hue = (angle * 180) / Math.PI
        const h = (hue + 360) % 360
        const { r, g, b } = hsvToRgb(h, sat, 1)
        data[idx] = r
        data[idx + 1] = g
        data[idx + 2] = b
        data[idx + 3] = 255
      } else {
        data[idx + 3] = 0
      }
    }
  }
  ctx.putImageData(img, 0, 0)
}

const currentPoint = ref({ x: center.value.x, y: center.value.y })

const thumbStyle = computed(() => ({
  transform: `translate(${currentPoint.value.x - 8}px, ${currentPoint.value.y - 8}px)`,
}))

function setFromPoint(px: number, py: number) {
  const { x: cx, y: cy } = center.value
  const dx = px - cx
  const dy = py - cy
  const dist = Math.sqrt(dx * dx + dy * dy)
  const R = radius.value
  const clampedDist = Math.min(dist, R)
  const angle = Math.atan2(dy, dx)
  const hue = (angle * 180) / Math.PI
  const h = (hue + 360) % 360
  const sat = Math.min(1, clampedDist / R)
  const { r, g, b } = hsvToRgb(h, sat, 1)
  const hex = rgbToHex(r, g, b)
  currentPoint.value = { x: cx + Math.cos(angle) * clampedDist, y: cy + Math.sin(angle) * clampedDist }
  emit('update:modelValue', hex)
  emit('change', hex)
  emit('vector-change', { hex, sat })
}

function onPointerDown(e: PointerEvent) {
  dragging.value = true
  const el = e.currentTarget as HTMLElement | null
  if (el && 'setPointerCapture' in el) {
    try { (el as HTMLElement).setPointerCapture(e.pointerId) } catch {}
  }
  const targetEl: Element | null = canvasRef.value ?? el
  const rect = targetEl ? targetEl.getBoundingClientRect() : new DOMRect(0,0,0,0)
  setFromPoint(e.clientX - rect.left, e.clientY - rect.top)
}
function onPointerMove(e: PointerEvent) {
  if (!dragging.value) return
  const el = (canvasRef.value ?? (e.currentTarget as HTMLElement | null))
  const rect = el ? el.getBoundingClientRect() : new DOMRect(0,0,0,0)
  setFromPoint(e.clientX - rect.left, e.clientY - rect.top)
}
function onPointerUp(e?: PointerEvent) {
  dragging.value = false
  const el: HTMLElement | null = (e?.currentTarget as HTMLElement) || canvasRef.value?.parentElement || null
  if (el && 'releasePointerCapture' in el && e && typeof e.pointerId === 'number') {
    try { (el as HTMLElement).releasePointerCapture(e.pointerId) } catch {}
  }
}

function updateThumbFromColor() {
  const { r, g, b } = hexToRgb(props.modelValue)
  const { h, s } = rgbToHsv(r, g, b)
  const angle = (h * Math.PI) / 180
  const R = radius.value
  // Thumb should reflect the actual wheel saturation from modelValue, not the external marker
  const sat = Math.max(0, Math.min(1, s))
  currentPoint.value = { x: center.value.x + Math.cos(angle) * R * sat, y: center.value.y + Math.sin(angle) * R * sat }
}

onMounted(() => {
  drawWheel()
  updateThumbFromColor()
})

watch(() => props.size, () => {
  drawWheel()
  updateThumbFromColor()
})

watch(() => props.modelValue, () => {
  updateThumbFromColor()
})
// markerSat is used only for appearance; it should not affect thumb position
</script>

<style scoped>
.color-wheel {
  position: relative;
  user-select: none;
  touch-action: none;
  overflow: hidden;
  display: inline-block;
}
.wheel-canvas {
  display: block;
  width: 100%;
  height: 100%;
}
.thumb {
  position: absolute;
  top: 0;
  left: 0;
  width: 16px;
  height: 16px;
  border: 2px solid #fff;
  border-radius: 50%;
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.9), 0 0 2px rgba(0,0,0,0.6);
  pointer-events: none;
  z-index: 1;
}
.thumb::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #000;
  transform: translate(-50%, -50%);
}
</style>
