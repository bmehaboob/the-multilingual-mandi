import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'robots.txt'],
      manifest: {
        name: 'Multilingual Mandi',
        short_name: 'Mandi',
        description: 'Voice-first platform for multilingual agricultural trade',
        theme_color: '#ffffff',
        icons: [
          {
            src: 'pwa-192x192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ]
      },
      workbox: {
        // Static assets to precache
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff,woff2}'],
        
        // Maximum size for precaching (2MB)
        maximumFileSizeToCacheInBytes: 2 * 1024 * 1024,
        
        // Runtime caching strategies
        runtimeCaching: [
          // API calls - Network First with fallback to cache
          // Requirement 12.7: Network-first strategy for API calls with fallback
          {
            urlPattern: /^https?:\/\/.*\/api\/.*/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              networkTimeoutSeconds: 10,
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 60 * 60 * 24 // 24 hours for offline access (Requirement 12.2)
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          },
          
          // Price data - Network First with longer cache for offline
          // Requirement 12.2: Cache market average for up to 24 hours
          {
            urlPattern: /^https?:\/\/.*\/api\/prices\/.*/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'price-data-cache',
              networkTimeoutSeconds: 5,
              expiration: {
                maxEntries: 200,
                maxAgeSeconds: 60 * 60 * 24 // 24 hours
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          },
          
          // Transaction history - Network First
          // Requirement 12.8: Cache transaction history for offline browsing
          {
            urlPattern: /^https?:\/\/.*\/api\/transactions\/.*/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'transaction-cache',
              networkTimeoutSeconds: 5,
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 60 * 60 * 24 * 7 // 7 days
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          },
          
          // User preferences and profile - Network First
          // Requirement 12.5: Store user preferences locally
          {
            urlPattern: /^https?:\/\/.*\/api\/users\/.*/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'user-data-cache',
              networkTimeoutSeconds: 5,
              expiration: {
                maxEntries: 50,
                maxAgeSeconds: 60 * 60 * 24 * 30 // 30 days
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          },
          
          // Negotiation templates - Cache First for offline access
          // Requirement 12.6: Cache negotiation templates locally
          {
            urlPattern: /^https?:\/\/.*\/api\/templates\/.*/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'template-cache',
              expiration: {
                maxEntries: 50,
                maxAgeSeconds: 60 * 60 * 24 * 7 // 7 days
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          },
          
          // Static assets - Cache First
          // Requirement 19.1: Cache-first strategy for static assets
          {
            urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp|ico)$/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'image-cache',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 60 * 60 * 24 * 30 // 30 days
              }
            }
          },
          
          // Font files - Cache First
          {
            urlPattern: /\.(?:woff|woff2|ttf|eot)$/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'font-cache',
              expiration: {
                maxEntries: 20,
                maxAgeSeconds: 60 * 60 * 24 * 365 // 1 year
              }
            }
          },
          
          // Audio files - Network First with cache fallback
          {
            urlPattern: /\.(?:mp3|wav|ogg|m4a)$/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'audio-cache',
              networkTimeoutSeconds: 10,
              expiration: {
                maxEntries: 50,
                maxAgeSeconds: 60 * 60 * 24 // 24 hours (audio deleted after processing per Requirement 15.2)
              }
            }
          }
        ],
        
        // Clean up old caches
        cleanupOutdatedCaches: true,
        
        // Skip waiting and claim clients immediately
        skipWaiting: true,
        clientsClaim: true
      }
    })
  ],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  build: {
    target: 'esnext',
    minify: 'esbuild',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          store: ['zustand']
        }
      }
    }
  }
})
