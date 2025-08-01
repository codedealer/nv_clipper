<template>
  <el-card class="section-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <el-icon><FolderOpened /></el-icon>
        <span>File Selection</span>
      </div>
    </template>

    <!-- File Selection Buttons -->
    <div class="button-group">
      <el-button
        @click="handleSelectFiles"
        :loading="isProcessing"
        type="primary"
        :icon="FolderOpened"
        style="width: 100%; margin-bottom: 8px;"
      >
        Select Files
      </el-button>

      <div class="button-row">
        <el-button
          @click="$emit('show-video-cache')"
          type="default"
          :icon="VideoCamera"
          style="flex: 1;"
          plain
        >
          Video Cache
        </el-button>

        <el-button
          @click="$emit('show-settings')"
          type="default"
          :icon="Setting"
          style="flex: 1; margin-left: 8px;"
          plain
        >
          Settings
        </el-button>
      </div>
    </div>

    <!-- Drop Zone -->
    <el-upload
      ref="uploadRef"
      class="upload-drop-zone"
      drag
      :auto-upload="false"
      :on-change="handleFileChange"
      :show-file-list="false"
      multiple
      accept=".json,.mp4,.webm,.avi,.mkv,.mov"
    >
      <el-icon class="upload-icon"><UploadFilled /></el-icon>
      <div class="upload-text">
        <p>Drop JSON markup here</p>
        <p class="upload-hint">Optionally include video file</p>
      </div>
    </el-upload>

    <!-- Selected Files Display -->
    <div v-if="hasMarkupFile || hasVideoFile" class="selected-files">
      <el-divider content-position="left">Selected Files</el-divider>

      <el-space direction="vertical" style="width: 100%;" size="small">
        <div v-if="selectedFiles.markup" class="file-item">
          <el-tag type="warning" :icon="Document" closable @close="clearMarkupFile">
            {{ getFileName(selectedFiles.markup) }}
          </el-tag>
        </div>

        <div v-if="selectedFiles.video" class="file-item">
          <el-tag type="danger" :icon="VideoCamera" closable @close="clearVideoFile">
            {{ getFileName(selectedFiles.video) }}
          </el-tag>
        </div>
      </el-space>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { UploadFile } from 'element-plus'
import { ElMessage } from 'element-plus'
import {
  FolderOpened,
  VideoCamera,
  UploadFilled,
  Document,
  Setting
} from '@element-plus/icons-vue'

interface Props {
  selectedFiles: {
    markup: string | null
    video: string | null
  }
  isProcessing: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'files-selected': [filePaths: string[]]
  'file-changed': [file: UploadFile]
  'clear-markup': []
  'clear-video': []
  'show-video-cache': []
  'show-settings': []
}>()

// Computed
const hasMarkupFile = computed(() => !!props.selectedFiles.markup)
const hasVideoFile = computed(() => !!props.selectedFiles.video)

// Methods
function getFileName(path: string): string {
  return path.split(/[\\/]/).pop() || path
}

async function handleSelectFiles() {
  try {
    // This would call the store method via emit
    emit('files-selected', [])
  } catch (error) {
    console.error('File selection failed:', error)
    ElMessage.error('File selection failed')
  }
}

function handleFileChange(file: UploadFile) {
  emit('file-changed', file)
}

function clearMarkupFile() {
  emit('clear-markup')
}

function clearVideoFile() {
  emit('clear-video')
}
</script>

<style scoped>
.section-card {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.button-group {
  margin-bottom: 16px;
}

.button-row {
  display: flex;
  gap: 0;
  width: 100%;
}

.upload-drop-zone {
  width: 100%;
}

.upload-drop-zone :deep(.el-upload-dragger) {
  width: 100%;
  height: 120px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.upload-icon {
  font-size: 32px;
  color: var(--el-color-primary);
  margin-bottom: 8px;
}

.upload-text {
  text-align: center;
}

.upload-text p {
  margin: 4px 0;
}

.upload-hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.selected-files {
  margin-top: 16px;
}

.file-item {
  margin-bottom: 8px;
}
</style>
