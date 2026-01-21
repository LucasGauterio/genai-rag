export default defineNuxtConfig({
  modules: ['@nuxt/eslint', '@nuxt/ui'],

  devtools: { enabled: true },

  runtimeConfig: {
    backendApiUrl: process.env.NUXT_BACKEND_API_URL
  },

  css: ['~/assets/css/main.css'],

  serverDir: 'server',

  routeRules: {
    '/': { ssr: false },
    '/api/**': { prerender: false }
  },
  nitro: {
    devProxy: {
      '/api/sessions': {
        target: `${process.env.NUXT_BACKEND_API_URL}/api/sessions`,
        changeOrigin: true
      },
      '/api/chat': {
        target: `${process.env.NUXT_BACKEND_API_URL}/api/chat`,
        changeOrigin: true
      },
      '/api/ingest': {
        target: `${process.env.NUXT_BACKEND_API_URL}/api/ingest`,
        changeOrigin: true
      },
      '/api/ingest-file': {
        target: `${process.env.NUXT_BACKEND_API_URL}/api/ingest-file`,
        changeOrigin: true
      }
    }
  },

  compatibilityDate: '2025-01-15',

  eslint: {
    config: {
      stylistic: {
        commaDangle: 'never',
        braceStyle: '1tbs'
      }
    }
  }
})
