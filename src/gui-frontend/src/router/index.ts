import { createRouter, createWebHashHistory } from 'vue-router'
import ClipperView from '../views/ClipperView.vue'

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'clipper',
      component: ClipperView,
    },
  ],
})

export default router
