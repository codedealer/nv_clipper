<template>
  <div class="debug-state" v-if="show">
    <details>
      <summary>Debug State</summary>
      <pre>{{ stateDump }}</pre>
    </details>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useClipperStore } from '@/stores/counter'

// Only show in dev builds
const show = import.meta.env.DEV
const store = useClipperStore()

const stateDump = computed(() => {
  return JSON.stringify({
    selectedFiles: store.selectedFiles,
    hasMarkupFile: store.hasMarkupFile,
    hasVideoFile: store.hasVideoFile,
  parsedClips: store.parsedClips.map(c => ({ n: c.number, start: c.start, end: c.end, cg: (c.overrides as { colorGrading?: string } | undefined)?.colorGrading })),
    selectedClips: store.selectedClips,
    activeColorGradingClip: store.activeColorGradingClip,
    activeSelectedClip: store.activeSelectedClip ? { n: store.activeSelectedClip.number } : null,
  parsedMarkupData: store.parsedMarkupData ? { hasMarkerPairs: !!(store.parsedMarkupData as unknown as { markerPairs?: unknown[] }).markerPairs } : null,
    isProcessing: store.isProcessing,
    processingStatus: store.processingStatus
  }, null, 2)
})
</script>

<style scoped>
.debug-state { position: fixed; bottom: 8px; right: 8px; width: 320px; max-height: 50vh; overflow: auto; font-size: 11px; z-index: 9999; background: rgba(0,0,0,0.75); color: #fff; padding: 6px 8px; border-radius: 4px; box-shadow: 0 2px 6px rgba(0,0,0,0.4); }
summary { cursor: pointer; font-weight: 600; }
pre { white-space: pre-wrap; word-break: break-word; margin: 4px 0 0; }
</style>
