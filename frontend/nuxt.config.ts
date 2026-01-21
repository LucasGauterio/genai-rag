// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  modules: [
    '@nuxt/eslint',
    '@nuxt/ui'
  ],

  devtools: {
    enabled: true
  },

  runtimeConfig: {
    // Server-only runtime config
    backendApiUrl: process.env.NUXT_BACKEND_API_URL
  },

  css: ['~/assets/css/main.css'],

  // Ensure the server directory is found
  serverDir: 'server',

  // Don't prerender the main page since it's a dynamic app
  routeRules: {
    // Disable SSR for the main app page - it uses client-only state
    '/': { ssr: false },
    // API routes should not be prerendered
    '/api/**': { prerender: false }
  },

  // Proxy API requests to Flask backend during development
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
