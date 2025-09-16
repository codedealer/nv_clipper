import type { ColorGradingState } from '@/types/colorGrading'
import { ref } from 'vue'

function cloneState<T>(obj: T): T {
  if (obj == null) return obj
  try {
  if (typeof structuredClone === 'function') return structuredClone(obj)
  } catch { /* ignore */ }
  return JSON.parse(JSON.stringify(obj))
}

// Reactive buffer so components can update enabled state (e.g., Paste button) across clip switches / remounts.
const bufferRef = ref<ColorGradingState | null>(null)

export function setColorGradingBuffer(state: ColorGradingState) { bufferRef.value = cloneState(state) }

export function getColorGradingBuffer(): ColorGradingState | null { return bufferRef.value ? cloneState(bufferRef.value) : null }

export function hasColorGradingBuffer(): boolean {
  return bufferRef.value !== null
}

export function clearColorGradingBuffer() { bufferRef.value = null }

export function useColorGradingBufferReactive() { return bufferRef }
