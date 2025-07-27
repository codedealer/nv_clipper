<template>
  <div id="q-app">
    <RouterView />
  </div>
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<style>
#q-app {
  margin: 0;
  padding: 0;
  height: 100vh;
  overflow: hidden; /* Prevent scrollbars as per design requirements */
}

body {
  margin: 0;
  padding: 0;
  height: 100vh;
  overflow: hidden;
}

* {
  box-sizing: border-box;
}
</style>
