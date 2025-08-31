import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

// Element Plus
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import { useClipperStore } from './stores/counter'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

// Register all Element Plus icons
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// Enable dark mode by default for video editing
document.documentElement.classList.add('dark')

app.mount('#app')

// After app is mounted, register backend push event handler if available
try {
  const store = useClipperStore()
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  ;(window as any).__ytc_onProcessingEvent = (payload: unknown) => {
    try {
      // Forward to store method (to be implemented)
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      store.onProcessingEvent(payload as any)
    } catch (e) {
      console.error('Failed to handle processing event in store', e)
    }
  }
} catch (e) {
  console.warn('Failed to register processing event handler', e)
}
