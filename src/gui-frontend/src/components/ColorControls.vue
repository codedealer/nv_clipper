<template>
  <div class="color-controls">
    <el-scrollbar height="100%">
      <div class="color-controls-content">
        <el-tabs v-model="activeTab" type="border-card">
          <el-tab-pane label="Color Adjustments" name="basic">
            <div class="control-group">
              <div class="control-label">Brightness</div>
              <el-slider v-model="brightness" :min="-0.5" :max="0.5" :step="0.01" @change="emitFilter" show-input input-size="small" />
            </div>
            <div class="control-group">
              <div class="control-label">Contrast</div>
              <el-slider v-model="contrast" :min="0" :max="3" :step="0.01" @change="emitFilter" show-input input-size="small" />
            </div>
            <div class="control-group">
              <div class="control-label">Saturation</div>
              <el-slider v-model="saturation" :min="0" :max="3" :step="0.01" @change="emitFilter" show-input input-size="small" />
            </div>
            <div class="control-group">
              <div class="control-label">Hue</div>
              <el-slider v-model="hue" :min="-180" :max="180" :step="1" @change="emitFilter" show-input input-size="small" />
            </div>
            <div class="control-group">
              <div class="control-label">Gamma</div>
              <el-slider v-model="gamma" :min="0.1" :max="3" :step="0.01" @change="emitFilter" show-input input-size="small" />
            </div>
          </el-tab-pane>
          <el-tab-pane label="Advanced (Lift/Gamma/Gain)" name="advanced">
            <LiftGammaGainWheels @advanced-filter-changed="handleAdvancedFilterChanged" />
          </el-tab-pane>
        </el-tabs>

        <div class="filter-output-card">
          <div class="filter-card-header">
            <h5>Generated Filter</h5>
            <div class="filter-header-controls">
              <el-checkbox v-model="previewEnabledLocal" @change="$emit('toggle-preview', previewEnabledLocal)" size="small">Preview</el-checkbox>
            </div>
          </div>
          <div class="filter-display">
            <el-input v-model="generatedFilter" type="textarea" :rows="2" readonly placeholder="Color grading filter will appear here" class="filter-textarea" />
          </div>
          <div class="filter-actions">
            <div class="action-group primary-actions">
              <el-button size="small" type="primary" @click="copyFilter" :disabled="!generatedFilter" plain>
                <el-icon><DocumentCopy /></el-icon>
                Copy Filter
              </el-button>
              <el-button size="small" @click="showPasteDialog" plain>
                <el-icon><Document /></el-icon>
                Paste Filter
              </el-button>
            </div>
            <div class="action-group secondary-actions">
              <el-button size="small" type="success" @click="$emit('copy-to-all-clips', generatedFilter)" :disabled="!generatedFilter || isMockMarkup" plain v-if="!isMockMarkup">
                <el-icon><CopyDocument /></el-icon>
                Copy to All Clips
              </el-button>
              <el-button size="small" type="warning" @click="reset" plain>
                <el-icon><RefreshLeft /></el-icon>
                Reset
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </el-scrollbar>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { DocumentCopy, Document, CopyDocument, RefreshLeft } from '@element-plus/icons-vue'
import LiftGammaGainWheels from './LiftGammaGainWheels.vue'
import { buildBasicFilter } from '@/utils/colorBasics'
import { parseFilterString, joinFilters } from '@/utils/filterString'
import { debounce } from '@/utils/debounce'


interface Props {
  isMockMarkup?: boolean
  previewEnabled?: boolean
  initialFilter?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  isMockMarkup: false,
  previewEnabled: true,
  initialFilter: null
})

const emit = defineEmits<{
  (e: 'filter-changed', filter: string): void
  (e: 'toggle-preview', enabled: boolean): void
  (e: 'copy-to-all-clips', filter: string): void
}>()

const activeTab = ref<'basic' | 'advanced'>('basic')
const brightness = ref(0)
const contrast = ref(1)
const saturation = ref(1)
const hue = ref(0)
const gamma = ref(1)
const advancedFilterState = ref('')
const previewEnabledLocal = ref<boolean>(props.previewEnabled)

const basicFilter = computed(() => buildBasicFilter({ brightness: brightness.value, contrast: contrast.value, saturation: saturation.value, hue: hue.value, gamma: gamma.value }))
const advancedFilter = computed(() => advancedFilterState.value)
const generatedFilter = computed(() => joinFilters(basicFilter.value, advancedFilter.value))

const debouncedFilterEmit = debounce(() => emit('filter-changed', generatedFilter.value), 180)
const emitFilter = () => { debouncedFilterEmit() }
const debouncedAdvancedHandler = debounce((filter: string) => { advancedFilterState.value = filter; emitFilter() }, 120)
const handleAdvancedFilterChanged = (filter: string) => { debouncedAdvancedHandler(filter) }

const reset = () => {
  brightness.value = 0; contrast.value = 1; saturation.value = 1; hue.value = 0; gamma.value = 1; advancedFilterState.value = ''
  emitFilter()
}

const copyFilter = async () => {
  try { await navigator.clipboard.writeText(generatedFilter.value); ElMessage.success('Filter copied to clipboard') }
  catch (e) { console.error('Failed to copy filter:', e); ElMessage.error('Failed to copy filter to clipboard') }
}

const showPasteDialog = async () => {
  try {
    const clipboardText = await navigator.clipboard.readText()
    if (clipboardText.trim()) { pasteFilter(clipboardText.trim()) }
    else { ElMessage.warning('Clipboard is empty') }
  } catch (e) { ElMessage.error('Failed to access clipboard. Please check permissions.'); console.error('Clipboard access failed:', e) }
}

const pasteFilter = (text: string) => {
  try { parseAndApplyFilter(text); emitFilter() }
  catch (e) { ElMessage.error(`Failed to apply filter: ${String(e)}`) }
}

const parseAndApplyFilter = (filterString: string) => {
  reset()
  const parsed = parseFilterString(filterString)
  brightness.value = parsed.brightness
  contrast.value = parsed.contrast
  saturation.value = parsed.saturation
  hue.value = parsed.hue
  gamma.value = parsed.gamma
  if (parsed.advanced) advancedFilterState.value = parsed.advanced
}

watch(
  () => props.initialFilter,
  (f) => {
    if (f != null) {
      parseAndApplyFilter(f)
      emitFilter()
    }
  },
  { immediate: true }
)

defineExpose({ generatedFilter })

const isMockMarkup = computed(() => props.isMockMarkup)
</script>

<style scoped>
.color-controls { height: 100%; overflow-y: auto; display: flex; flex-direction: column; gap: 16px; }
.control-group { margin-bottom: 16px; }
.control-label { font-size: 13px; color: var(--el-text-color-regular); margin-bottom: 8px; font-weight: 500; }
.filter-display { border-top: 1px solid var(--el-border-color); padding-top: 16px; }
.filter-output-card { border: 1px solid var(--el-border-color); border-radius: 8px; padding: 16px; background: var(--el-bg-color); margin-top: 16px; }
.filter-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.filter-card-header h5 { margin: 0; font-size: 14px; font-weight: 600; color: var(--el-text-color-primary); }
.filter-header-controls { display: flex; align-items: center; gap: 8px; }
.filter-textarea { margin-bottom: 16px; }
.filter-textarea :deep(.el-textarea__inner) { font-family: monospace; font-size: 12px; line-height: 1.4; background: var(--el-fill-color-lighter); }
.filter-actions { display: flex; flex-direction: column; gap: 12px; }
.action-group { display: flex; gap: 8px; flex-wrap: wrap; }
.primary-actions .el-button { flex: 1; min-width: 120px; }
.secondary-actions .el-button { flex: 1; min-width: 100px; }
</style>
