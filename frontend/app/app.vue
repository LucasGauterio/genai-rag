<script setup lang="ts">
useHead({
  meta: [
    { name: 'viewport', content: 'width=device-width, initial-scale=1' }
  ],
  link: [
    { rel: 'icon', href: '/favicon.ico' }
  ],
  htmlAttrs: {
    lang: 'en'
  }
})

useSeoMeta({
  title: 'Document Chat',
  description: 'A document-based chat application'
})
</script>

<template>
  <UApp>
    <NuxtPage />
  </UApp>
</template>

<style>
/* Ensure UApp fills the full height */
.u-app {
  height: 100%;
  display: flex;
  flex-direction: column;
}
</style>
