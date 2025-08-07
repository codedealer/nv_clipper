// Utility functions for handling JSON markup files

export interface MarkupData {
  videoUrl?: string
  title?: string
  clips?: Array<{
    title: string
    start: number
    end: number
    [key: string]: unknown
  }>
  [key: string]: unknown
}

export async function parseMarkupFile(filePath: string): Promise<MarkupData | null> {
  try {
    // In a real implementation, we'd read the file from the file system
    // For now, this is a placeholder that would be handled by the Python backend
    const response = await fetch(`file://${filePath}`)
    const content = await response.text()
    return JSON.parse(content) as MarkupData
  } catch (error) {
    console.error('Failed to parse markup file:', error)
    return null
  }
}

export function extractVideoUrlFromMarkup(markup: MarkupData): string | null {
  return markup.videoUrl || null
}

export function getVideoTitleFromMarkup(markup: MarkupData): string | null {
  return markup.title || null
}

export function hasVideoUrlInMarkup(markup: MarkupData): boolean {
  return Boolean(markup.videoUrl)
}

export function formatMarkupInfo(markup: MarkupData): string {
  const clipCount = markup.clips?.length || 0
  const hasVideo = hasVideoUrlInMarkup(markup)

  return `${clipCount} clips${hasVideo ? ' (with video URL)' : ''}`
}
