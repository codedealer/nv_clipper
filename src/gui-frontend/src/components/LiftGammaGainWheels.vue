<template>
  <div class="lgg-wheels">
    <div class="wheel-block">
      <div class="wheel-header">
        <div class="wheel-title">Shadows (Lift)</div>
        <el-button class="reset-btn" text circle size="small" :title="'Reset Shadows'" @click="resetLift">
          <el-icon><RefreshLeft /></el-icon>
        </el-button>
      </div>
      <div class="wheel-and-slider">
        <ColorWheel
          v-model="liftHex"
          :size="wheelSize"
          :markerSat="liftSat * liftAmount"
          @change="emitChange"
          @vector-change="onVectorLift"
        />
        <el-slider
          v-model="liftAmount"
          vertical
          :height="wheelSize + 'px'"
          :min="0"
          :max="1"
          :step="0.01"
          @change="emitChange"
        />
      </div>
    </div>

    <div class="wheel-block">
      <div class="wheel-header">
        <div class="wheel-title">Midtones (Gamma)</div>
        <el-button class="reset-btn" text circle size="small" :title="'Reset Midtones'" @click="resetMid">
          <el-icon><RefreshLeft /></el-icon>
        </el-button>
      </div>
      <div class="wheel-and-slider">
        <ColorWheel
          v-model="midHex"
          :size="wheelSize"
          :markerSat="midSat * midAmount"
          @change="emitChange"
          @vector-change="onVectorMid"
        />
        <el-slider
          v-model="midAmount"
          vertical
          :height="wheelSize + 'px'"
          :min="0"
          :max="1"
          :step="0.01"
          @change="emitChange"
        />
      </div>
    </div>

    <div class="wheel-block">
      <div class="wheel-header">
        <div class="wheel-title">Highlights (Gain)</div>
        <el-button class="reset-btn" text circle size="small" :title="'Reset Highlights'" @click="resetGain">
          <el-icon><RefreshLeft /></el-icon>
        </el-button>
      </div>
      <div class="wheel-and-slider">
        <ColorWheel
          v-model="gainHex"
          :size="wheelSize"
          :markerSat="gainSat * gainAmount"
          @change="emitChange"
          @vector-change="onVectorGain"
        />
        <el-slider
          v-model="gainAmount"
          vertical
          :height="wheelSize + 'px'"
          :min="0"
          :max="1"
          :step="0.01"
          @change="emitChange"
        />
      </div>
    </div>

    <div class="control-group">
      <div class="control-label">Global Gamma</div>
      <el-slider v-model="globalGamma" :min="0.1" :max="3" :step="0.01" @change="emitChange" show-input input-size="small" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { RefreshLeft } from '@element-plus/icons-vue'
import ColorWheel from './common/ColorWheel.vue'
import { buildLggFilterFromWheels } from '@/utils/lgg'
import type { LggWheelState } from '@/types/colorGrading'

interface Emits {
  (e: 'wheel-state-changed', state: LggWheelState, filter: string): void
}

interface Props {
  wheelState: LggWheelState
}

const props = defineProps<Props>()

const emit = defineEmits<Emits>()

// Local refs bound to prop (decoupled so we can debounce & emit consolidated state)
const liftHex = ref(props.wheelState.lift.hex)
const midHex = ref(props.wheelState.mid.hex)
const gainHex = ref(props.wheelState.gain.hex)
const liftSat = ref(props.wheelState.lift.sat)
const midSat = ref(props.wheelState.mid.sat)
const gainSat = ref(props.wheelState.gain.sat)
const liftAmount = ref(props.wheelState.lift.amount)
const midAmount = ref(props.wheelState.mid.amount)
const gainAmount = ref(props.wheelState.gain.amount)
const globalGamma = ref(props.wheelState.globalGamma)
const wheelSize = 140

function buildState(): LggWheelState {
  return {
    lift: { hex: liftHex.value, sat: liftSat.value, amount: liftAmount.value },
    mid: { hex: midHex.value, sat: midSat.value, amount: midAmount.value },
    gain: { hex: gainHex.value, sat: gainSat.value, amount: gainAmount.value },
    globalGamma: globalGamma.value,
  }
}
function computeFilter(): string {
  return buildLggFilterFromWheels(
    {
      lift: { hex: liftHex.value, strength: liftSat.value, neutral: liftAmount.value },
      mid: { hex: midHex.value, strength: midSat.value, neutral: midAmount.value },
      gain: { hex: gainHex.value, strength: gainSat.value, neutral: gainAmount.value }
    },
    globalGamma.value
  )
}
function emitChange() {
  if (import.meta.env.DEV) console.log('[LGGWheels] commit emitChange')
  emit('wheel-state-changed', buildState(), computeFilter())
}

// Sync when parent prop changes (e.g., clip switch, paste state)
watch(() => props.wheelState, (ns) => {
  if (!ns) return
  // Equality guard to prevent redundant reactivity churn
  const same =
    liftHex.value.toLowerCase() === ns.lift.hex.toLowerCase() &&
    midHex.value.toLowerCase() === ns.mid.hex.toLowerCase() &&
    gainHex.value.toLowerCase() === ns.gain.hex.toLowerCase() &&
    liftSat.value === ns.lift.sat &&
    midSat.value === ns.mid.sat &&
    gainSat.value === ns.gain.sat &&
    liftAmount.value === ns.lift.amount &&
    midAmount.value === ns.mid.amount &&
    gainAmount.value === ns.gain.amount &&
    globalGamma.value === ns.globalGamma
  if (same) return
  liftHex.value = ns.lift.hex
  midHex.value = ns.mid.hex
  gainHex.value = ns.gain.hex
  liftSat.value = ns.lift.sat
  midSat.value = ns.mid.sat
  gainSat.value = ns.gain.sat
  liftAmount.value = ns.lift.amount
  midAmount.value = ns.mid.amount
  gainAmount.value = ns.gain.amount
  globalGamma.value = ns.globalGamma
  // Do NOT emit here; this is a parent-driven sync.
}, { deep: true })

// No initial emit; parent will decide when to emit a filter change

// Removed external filter parsing; state is source of truth now.

function resetLift() {
  liftHex.value = '#ffffff'
  liftSat.value = 0
  liftAmount.value = 0.5
}
function resetMid() {
  midHex.value = '#ffffff'
  midSat.value = 0
  midAmount.value = 0.5
}
function resetGain() {
  gainHex.value = '#ffffff'
  gainSat.value = 0
  gainAmount.value = 0.5
}

function onVectorLift(payload: { hex: string; sat: number }) {
  liftSat.value = payload.sat
}
function onVectorMid(payload: { hex: string; sat: number }) {
  midSat.value = payload.sat
}
function onVectorGain(payload: { hex: string; sat: number }) {
  gainSat.value = payload.sat
}
</script>

<style scoped>
.lgg-wheels {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.wheel-block {
  border: 0;
  border-radius: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.wheel-header { display: flex; align-items: center; justify-content: space-between; padding: 0 2px; }
.wheel-title { font-weight: 600; font-size: 12px; opacity: 0.9; }
.reset-btn { --el-button-hover-bg-color: transparent; }
.wheel-and-slider {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8px;
}
.wheel-and-slider :deep(.el-slider--vertical) {
  margin-left: 4px;
}
</style>
