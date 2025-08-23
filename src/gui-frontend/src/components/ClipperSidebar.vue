<template>
  <el-aside width="350px" class="sidebar">
    <el-container direction="vertical" style="height: 100%;">
      <!-- Scrollable Content Area -->
      <el-main class="sidebar-main">
        <el-scrollbar height="100%">
          <div class="sidebar-content">
            <!-- File Selection Component -->
            <FileSelection
              :selected-files="selectedFiles"
              :is-processing="isProcessing"
              @files-selected="$emit('files-selected', $event)"
              @select-files-button="$emit('select-files-button')"
              @file-changed="$emit('file-changed', $event)"
              @clear-markup="$emit('clear-markup')"
              @clear-video="$emit('clear-video')"
            />

            <!-- Video URL Extractor - only show when markup has URL but no video is selected -->
            <VideoUrlExtractor
              v-if="parsedMarkupData && !hasVideoFile"
              :markup-data="parsedMarkupData"
              :has-video-source="hasVideoFile"
              @download-requested="$emit('video-download-requested')"
            />

            <div class="sidebar-separator"></div>

            <!-- Clip Selection Component -->
            <ClipSelection
              :clips="parsedClips"
              :model-value="selectedClips"
              :active-color-grading-clip="activeColorGradingClip"
              @update:model-value="$emit('update:selected-clips', $event)"
              @clip-selected-for-color-grading="$emit('clip-selected-for-color-grading', $event)"
            />
          </div>
        </el-scrollbar>
      </el-main>

      <!-- Fixed Processing Footer -->
      <el-footer height="auto" class="processing-footer">
        <ProcessingPanel
          :can-process="canProcess"
          :is-processing="isProcessing"
          :processing-status="processingStatus"
          :processing-result="processingResult"
          :overwrite-enabled="overwriteEnabled"
          @start-processing="$emit('start-processing')"
          @update-overwrite="$emit('update-overwrite', $event)"
        />
      </el-footer>
    </el-container>
  </el-aside>
</template>

<script setup lang="ts">
import { ElAside, ElContainer, ElMain, ElScrollbar, ElFooter } from 'element-plus'
import type { UploadFile } from 'element-plus'
import FileSelection from './FileSelection.vue'
import ClipSelection from './ClipSelection.vue'
import ProcessingPanel from './ProcessingPanel.vue'
import VideoUrlExtractor from './VideoUrlExtractor.vue'
import type { SelectedFiles, ClipInfo, ProcessingResult } from '@/types/api'
import { SIDEBAR_WIDTH } from '@/constants'

interface Props {
  selectedFiles: SelectedFiles
  parsedClips: ClipInfo[]
  selectedClips: number[]
  activeColorGradingClip: number | null
  isProcessing: boolean
  canProcess: boolean
  processingStatus: string
  processingResult: ProcessingResult | null
  parsedMarkupData: { videoUrl?: string; title?: string; [key: string]: unknown } | null
  hasVideoFile: boolean
  overwriteEnabled: boolean
}

interface Emits {
  (e: 'files-selected', files: string[]): void
  (e: 'select-files-button'): void
  (e: 'file-changed', file: UploadFile): void
  (e: 'clear-markup'): void
  (e: 'clear-video'): void
  (e: 'clip-selected-for-color-grading', clipIndex: number): void
  (e: 'start-processing'): void
  (e: 'update-overwrite', value: boolean): void
  (e: 'video-download-requested'): void
  (e: 'update:selected-clips', clips: number[]): void
}

defineProps<Props>()
defineEmits<Emits>()
</script>

<style scoped>
.sidebar {
  background: var(--el-bg-color);
  border-right: 1px solid var(--el-border-color);
  padding: 0;
  height: calc(100vh - 60px);
  overflow: hidden;
}

.sidebar-main {
  padding: 0;
  overflow: hidden;
}

.sidebar-content {
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0;
}

.sidebar-separator {
  height: 1px;
  background-color: var(--el-border-color-light);
  margin: 0;
}

.processing-footer {
  border-top: 1px solid var(--el-border-color);
  background: var(--el-bg-color);
  padding: 0;
}

/* Responsive sidebar adjustments */
@media (min-width: 1024px) {
  .sidebar {
    width: 350px !important;
    min-width: 350px;
    max-width: 400px;
  }
}

@media (min-width: 1440px) {
  .sidebar {
    width: 350px !important;
    max-width: 400px;
  }
}
</style>
