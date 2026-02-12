export default defineNuxtConfig({
  compatibilityDate: '2025-01-01',
  devtools: { enabled: false },
  modules: [
    '@nuxtjs/tailwindcss',
    '@nuxtjs/color-mode',
    '@pinia/nuxt',
  ],
  css: ['~/assets/css/main.css'],
  colorMode: {
    preference: 'dark',
    fallback: 'dark',
    classSuffix: '',
  },
  tailwindcss: {
    cssPath: false,
  },
  runtimeConfig: {
    public: {
      apiBase: '/api',
    },
  },
  nitro: {
    devProxy: {
      '/api': {
        target: 'http://localhost:8000/api',
        changeOrigin: true,
      },
    },
  },
  app: {
    head: {
      title: 'BadPing - Network Monitor',
      meta: [
        { name: 'description', content: 'Network monitoring tool for detecting connectivity problems' },
      ],
      link: [
        { rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' },
      ],
    },
  },
  ssr: false,
})
