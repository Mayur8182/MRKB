const CACHE_NAME = 'fire-shakti-cache-v3';
const STATIC_CACHE = 'fire-shakti-static-v3';
const DYNAMIC_CACHE = 'fire-shakti-dynamic-v3';

// Static assets to cache immediately
const STATIC_ASSETS = [
  '/',
  '/manifest.json',
  '/static/icons/icon-72x72.svg',
  '/static/icons/icon-96x96.svg',
  '/static/icons/icon-144x144.svg',
  '/static/icons/icon-192x192.svg',
  '/static/icons/icon-512x512.svg',
  '/static/icons/apple-touch-icon.svg',
  '/static/icons/favicon.ico',
  'https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css'
];

// Routes to cache dynamically
const DYNAMIC_ROUTES = [
  '/dashboard',
  '/login',
  '/register',
  '/profile',
  '/request_inspection',
  '/view_inspections',
  '/settings'
];

// Install event - cache static assets
self.addEventListener('install', event => {
  console.log('Service Worker: Installing...');
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => {
        console.log('Service Worker: Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('Service Worker: Static assets cached');
        return self.skipWaiting();
      })
      .catch(error => {
        console.error('Service Worker: Error caching static assets', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('Service Worker: Activating...');
  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
              console.log('Service Worker: Deleting old cache', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('Service Worker: Activated');
        return self.clients.claim();
      })
  );
});

// Fetch event - serve from cache with network fallback
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip external requests (except CDN assets)
  if (url.origin !== location.origin && !STATIC_ASSETS.includes(request.url)) {
    return;
  }

  event.respondWith(
    caches.match(request)
      .then(cachedResponse => {
        if (cachedResponse) {
          console.log('Service Worker: Serving from cache', request.url);
          return cachedResponse;
        }

        // Network first for API calls
        if (request.url.includes('/api/') || request.url.includes('/upload')) {
          return fetch(request)
            .then(response => {
              return response;
            })
            .catch(() => {
              return new Response(
                JSON.stringify({ error: 'Offline - Please check your connection' }),
                {
                  status: 503,
                  statusText: 'Service Unavailable',
                  headers: { 'Content-Type': 'application/json' }
                }
              );
            });
        }

        // Cache first for static assets and pages
        return fetch(request)
          .then(response => {
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }

            const responseToCache = response.clone();

            if (DYNAMIC_ROUTES.some(route => request.url.includes(route))) {
              caches.open(DYNAMIC_CACHE)
                .then(cache => {
                  cache.put(request, responseToCache);
                });
            }

            return response;
          })
          .catch(() => {
            if (request.destination === 'document') {
              return new Response(
                `<!DOCTYPE html>
                <html>
                <head>
                  <title>Offline - Fire Shakti</title>
                  <meta name="viewport" content="width=device-width, initial-scale=1">
                  <style>
                    body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                    .offline { color: #666; }
                    .retry-btn {
                      background: #FF4444; color: white; padding: 10px 20px;
                      border: none; border-radius: 5px; cursor: pointer; margin-top: 20px;
                    }
                  </style>
                </head>
                <body>
                  <h1>🔥 Fire Shakti</h1>
                  <div class="offline">
                    <h2>You're offline</h2>
                    <p>Please check your internet connection and try again.</p>
                    <button class="retry-btn" onclick="window.location.reload()">Retry</button>
                  </div>
                </body>
                </html>`,
                {
                  headers: { 'Content-Type': 'text/html' }
                }
              );
            }
          });
      })
  );
});