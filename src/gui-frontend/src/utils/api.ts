// Utility to wait for pywebview API to be ready
export function waitForPywebview(): Promise<Window['pywebview']['api']> {
  return new Promise((resolve) => {
    // If API is already available, resolve immediately
    if (window.pywebview?.api) {
      console.log('pywebview API already available')
      resolve(window.pywebview.api)
      return
    }

    // Wait for pywebviewready event
    const handleReady = () => {
      console.log('pywebviewready event fired')
      if (window.pywebview?.api) {
        console.log('pywebview API is now available')
        resolve(window.pywebview.api)
      } else {
        console.error('pywebviewready fired but API still not available')
        // Fallback - try again after a short delay
        setTimeout(() => {
          if (window.pywebview?.api) {
            resolve(window.pywebview.api)
          }
        }, 100)
      }
    }

    document.addEventListener('pywebviewready', handleReady, { once: true })
  })
}

// Simple API access for pywebview (throws if not ready)
export function getAPI() {
  if (!window.pywebview?.api) {
    throw new Error('pywebview API not available')
  }

  // Debug: log available methods
  console.log('Available API methods:', Object.getOwnPropertyNames(window.pywebview.api))
  console.log('API object:', window.pywebview.api)

  return window.pywebview.api
}
