// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  modules: [
    '@nuxt/eslint',
    '@nuxt/ui'
  ],

  devtools: {
    enabled: true
  },

  css: ['~/assets/css/main.css'],

  // Ensure the server directory is found
  serverDir: 'server',

  // Don't prerender the main page since it's a dynamic app
  routeRules: {
    // API routes should not be prerendered
    '/api/**': { prerender: false }
  },

  // Proxy API requests to Flask backend during development
  nitro: {
    devProxy: {
      '/api/sessions': {
        target: 'http://localhost:5000/api/sessions',
        changeOrigin: true
      },
      '/api/chat': {
        target: 'http://localhost:5000/api/chat',
        changeOrigin: true
      },
      '/api/ingest': {
        target: 'http://localhost:5000/api/ingest',
        changeOrigin: true
      },
      '/api/sessions/': {
        target: 'http://localhost:5000/api/sessions/',
        changeOrigin: true
      },
      '/api/ingest-file': {
        target: 'http://localhost:5000/api/ingest-file',
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
