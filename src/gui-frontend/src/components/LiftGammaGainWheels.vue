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
import { ref, watch, onMounted } from 'vue'
import { RefreshLeft } from '@element-plus/icons-vue'
import ColorWheel from './common/ColorWheel.vue'
import { buildLggFilterFromWheels } from '@/utils/lgg'

interface Emits {
  (e: 'advanced-filter-changed', filter: string): void
}

const emit = defineEmits<Emits>()

// State
const liftHex = ref('#ffffff')
const midHex = ref('#ffffff')
const gainHex = ref('#ffffff')
// Wheel radial (sat) captured from drag; Amount is the user intensity (0..1)
const liftSat = ref(0)
const midSat = ref(0)
const gainSat = ref(0)
// Slider midpoint (0.5) is neutral (no change), 0 darkens/lowers, 1 brightens/boosts
const liftAmount = ref(0.5)
const midAmount = ref(0.5)
const gainAmount = ref(0.5)
const globalGamma = ref(1)
const wheelSize = 140

function computeFilter(): string {
  const f = buildLggFilterFromWheels(
    {
  lift: { hex: liftHex.value, strength: liftSat.value, neutral: liftAmount.value },
  mid: { hex: midHex.value, strength: midSat.value, neutral: midAmount.value },
  gain: { hex: gainHex.value, strength: gainSat.value, neutral: gainAmount.value }
    },
    globalGamma.value
  )
  return f
}

function emitChange() {
  emit('advanced-filter-changed', computeFilter())
}

onMounted(() => emitChange())

// Recompute any time a value changes (v-model or slider)
watch([liftHex, midHex, gainHex, liftSat, midSat, gainSat, liftAmount, midAmount, gainAmount, globalGamma], () => {
  emitChange()
})

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
