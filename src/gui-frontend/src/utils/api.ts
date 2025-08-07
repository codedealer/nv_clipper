// Check if pywebview API is ready with all required methods
function isAPIReady(): boolean {
  if (!window.pywebview?.api) return false

  // Check if critical methods are available and are functions
  const api = window.pywebview.api as Record<string, unknown>
  const requiredMethods = ['get_status', 'get_all_settings', 'process_files']

  return requiredMethods.every(method => typeof api[method] === 'function')
}

// Utility to wait for pywebview API to be ready
export function waitForPywebview(): Promise<Window['pywebview']['api']> {
  return new Promise((resolve, reject) => {
    console.log('Requesting pywebview API...')

    // If API is already ready, resolve immediately
    if (isAPIReady()) {
      console.log('pywebview API already ready')
      resolve(window.pywebview.api)
      return
    }

    console.log('pywebview API not ready, waiting for initialization...')

    let resolved = false
    // eslint-disable-next-line prefer-const
    let timeoutId: number | undefined
    // eslint-disable-next-line prefer-const
    let pollInterval: number | undefined

    const cleanupAndResolve = (api: Window['pywebview']['api']) => {
      if (resolved) return
      resolved = true

      if (timeoutId !== undefined) clearTimeout(timeoutId)
      if (pollInterval !== undefined) clearInterval(pollInterval)

      console.log('pywebview API successfully acquired')
      resolve(api)
    }

    const cleanupAndReject = (error: Error) => {
      if (resolved) return
      resolved = true

      if (timeoutId !== undefined) clearTimeout(timeoutId)
      if (pollInterval !== undefined) clearInterval(pollInterval)

      console.error('Failed to acquire pywebview API:', error.message)
      reject(error)
    }

    // Set timeout
    timeoutId = setTimeout(() => {
      cleanupAndReject(new Error('Timeout waiting for pywebview API'))
    }, 10000)

    const tryResolve = (source: string) => {
      if (resolved) return

      console.log(`Checking API availability from ${source}...`)

      // Small delay to ensure API is fully initialized
      setTimeout(() => {
        if (resolved) return

        if (isAPIReady()) {
          console.log(`pywebview API confirmed ready via ${source}`)
          cleanupAndResolve(window.pywebview.api)
        } else {
          console.log(`API not yet ready via ${source}, continuing to wait...`)
        }
      }, 50)
    }

    // Listen for both possible event names
    const handleStandardReady = () => tryResolve('pywebviewready event')
    const handleUnderscoreReady = () => tryResolve('_pywebviewready event')

    document.addEventListener('pywebviewready', handleStandardReady, { once: true })
    document.addEventListener('_pywebviewready', handleUnderscoreReady, { once: true })

    // Poll as fallback mechanism
    pollInterval = setInterval(() => {
      if (resolved) return

      if (isAPIReady()) {
        console.log('pywebview API detected via polling')
        cleanupAndResolve(window.pywebview.api)
      }
    }, 100)

    // Also check immediately in case we missed the event
    setTimeout(() => tryResolve('immediate check'), 10)
  })
}

// Simple API access for pywebview (throws if not ready)
export function getAPI() {
  if (!isAPIReady()) {
    throw new Error('pywebview API not ready - missing required methods')
  }

  const api = window.pywebview.api
  const apiAny = api as Record<string, unknown> // Cast for debugging purposes

  // Debug: log available methods and properties
  console.log('=== pywebview API Debug Info ===')
  console.log('API object type:', typeof api)
  console.log('API object:', api)

  // Get all property names (including non-enumerable ones)
  const allProps = Object.getOwnPropertyNames(apiAny)
  console.log('All property names:', allProps)

  // Check for specific methods we need
  const requiredMethods = [
    'get_status',
    'get_all_settings',
    'get_general_settings',
    'update_general_settings',
    'process_files',
    'parse_markup_file'
  ]

  const availableMethods: string[] = []
  const missingMethods: string[] = []

  requiredMethods.forEach(method => {
    if (typeof apiAny[method] === 'function') {
      availableMethods.push(method)
    } else {
      missingMethods.push(method)
      console.warn(`Missing or non-function method: ${method}, type:`, typeof apiAny[method])
    }
  })

  console.log('Available required methods:', availableMethods)
  console.log('Missing required methods:', missingMethods)

  // Check if methods exist with different names
  const allMethods = allProps.filter(prop => typeof apiAny[prop] === 'function')
  console.log('All available methods:', allMethods)

  console.log('=== End Debug Info ===')

  return api
}
