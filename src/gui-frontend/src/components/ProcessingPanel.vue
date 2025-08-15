<template>
  <el-card class="processing-card" shadow="hover">
    <el-space direction="vertical" style="width: 100%;" size="small">
      <el-checkbox v-model="overwriteFiles">
        Overwrite existing files ({{ overwriteEnabled ? 'enabled' : 'disabled' }} in settings)
      </el-checkbox>

      <el-button
        @click="$emit('start-processing')"
        :loading="isProcessing"
        :disabled="!canProcess"
        type="success"
        :icon="VideoPlay"
        size="large"
        style="width: 100%;"
      >
        {{ isProcessing ? 'Processing...' : 'Start Processing' }}
      </el-button>

      <!-- Processing Progress -->
      <div v-if="isProcessing" class="processing-progress">
        <el-progress
          :percentage="100"
          :indeterminate="true"
          :show-text="false"
        />
        <div class="progress-text">{{ processingStatus }}</div>
      </div>

      <!-- Processing Result -->
      <el-alert
        v-if="processingResult && processingResult.status !== 'accepted'"
        :title="processingResult.message"
        :type="processingResult.status === 'success' ? 'success' : 'error'"
        :icon="processingResult.status === 'success' ? SuccessFilled : CircleCloseFilled"
        show-icon
        :closable="false"
      />
    </el-space>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { VideoPlay, SuccessFilled, CircleCloseFilled } from '@element-plus/icons-vue'

interface ProcessingResult {
  status: 'success' | 'error' | 'accepted'
  message: string
  job_id?: string
  report?: string
  output_path?: string
}

interface Props {
  canProcess: boolean
  isProcessing: boolean
  processingStatus: string
  processingResult: ProcessingResult | null
  overwriteEnabled: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'start-processing': []
  'update-overwrite': [value: boolean]
}>()

// Computed
const overwriteFiles = computed({
  get: () => props.overwriteEnabled,
  set: (value: boolean) => emit('update-overwrite', value)
})
</script>

<style scoped>
.processing-card {
  margin: 0;
  border-radius: 0;
  border: none;
  box-shadow: none;
}

.processing-card :deep(.el-card__body) {
  padding: 12px;
}

.processing-progress {
  width: 100%;
}

.progress-text {
  text-align: center;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 8px;
}
</style>
