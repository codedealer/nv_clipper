<template>
  <div class="api-debug">
    <h3>PyWebView API Debug</h3>
    <el-button @click="testApi" type="primary">Test API</el-button>

    <div v-if="debugInfo" class="debug-info">
      <h4>Debug Information:</h4>
      <pre>{{ debugInfo }}</pre>
    </div>

    <div v-if="apiMethods.length > 0" class="methods-list">
      <h4>Available Methods:</h4>
      <ul>
        <li v-for="method in apiMethods" :key="method">{{ method }}</li>
      </ul>
    </div>

    <div v-if="testResults.length > 0" class="test-results">
      <h4>Test Results:</h4>
      <div v-for="result in testResults" :key="result.method" class="test-result">
        <strong>{{ result.method }}:</strong>
        <span :class="result.success ? 'success' : 'error'">
          {{ result.success ? 'SUCCESS' : 'FAILED' }}
        </span>
        <div v-if="result.error" class="error-details">{{ result.error }}</div>
        <div v-if="result.result" class="result-details">{{ JSON.stringify(result.result, null, 2) }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElButton } from 'element-plus'
import { waitForPywebview, getAPI } from '@/utils/api'

const debugInfo = ref<string>('')
const apiMethods = ref<string[]>([])
const testResults = ref<Array<{
  method: string
  success: boolean
  error?: string
  result?: any
}>>([])

async function testApi() {
  debugInfo.value = ''
  apiMethods.value = []
  testResults.value = []

  try {
    console.log('Starting API test...')

    // Test waiting for pywebview
    const api = await waitForPywebview()
    console.log('API acquired successfully')

    // Get debug info
    const debugApi = getAPI()

    // Collect method names
    const apiAny = api as any
    const allProps = Object.getOwnPropertyNames(apiAny)
    const methods = allProps.filter(prop => typeof apiAny[prop] === 'function')
    apiMethods.value = methods

    debugInfo.value = `API Type: ${typeof api}\nAll Properties: ${allProps.join(', ')}\nMethods: ${methods.join(', ')}`

    // Test specific methods
    const methodsToTest = [
      'get_status',
      'get_all_settings',
      'get_general_settings'
    ]

    for (const method of methodsToTest) {
      try {
        if (typeof apiAny[method] === 'function') {
          console.log(`Testing method: ${method}`)
          const result = await apiAny[method]()
          testResults.value.push({
            method,
            success: true,
            result
          })
        } else {
          testResults.value.push({
            method,
            success: false,
            error: `Method ${method} is not a function (type: ${typeof apiAny[method]})`
          })
        }
      } catch (error) {
        testResults.value.push({
          method,
          success: false,
          error: String(error)
        })
      }
    }

  } catch (error) {
    debugInfo.value = `Error: ${error}`
    console.error('API test failed:', error)
  }
}
</script>

<style scoped>
.api-debug {
  padding: 20px;
  max-width: 800px;
}

.debug-info, .methods-list, .test-results {
  margin-top: 20px;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.debug-info pre {
  white-space: pre-wrap;
  background: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
}

.methods-list ul {
  margin: 0;
  padding-left: 20px;
}

.test-result {
  margin-bottom: 10px;
  padding: 10px;
  border-left: 3px solid #ddd;
}

.success {
  color: green;
  font-weight: bold;
}

.error {
  color: red;
  font-weight: bold;
}

.error-details {
  color: red;
  font-size: 0.9em;
  margin-top: 5px;
}

.result-details {
  background: #f5f5f5;
  padding: 10px;
  margin-top: 5px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.9em;
  white-space: pre-wrap;
}
</style>
