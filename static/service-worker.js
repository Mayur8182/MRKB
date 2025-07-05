const CACHE_NAME = 'fire-shakti-cache-v2';
const STATIC_CACHE = 'fire-shakti-static-v2';
const DYNAMIC_CACHE = 'fire-shakti-dynamic-v2';

// Static assets to cache immediately
const STATIC_ASSETS = [
  '/',
  '/static/manifest.json',
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
              // Don't cache API responses
              return response;
            })
            .catch(() => {
              // Return offline page for API failures
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
            // Check if response is valid
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }

            // Clone response for caching
            const responseToCache = response.clone();

            // Cache dynamic content
            if (DYNAMIC_ROUTES.some(route => request.url.includes(route))) {
              caches.open(DYNAMIC_CACHE)
                .then(cache => {
                  cache.put(request, responseToCache);
                });
            }

            return response;
          })
          .catch(() => {
            // Return offline page for navigation requests
            if (request.destination === 'document') {
              return caches.match('/') || new Response(
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

// Background sync for form submissions
self.addEventListener('sync', event => {
  console.log('Service Worker: Background sync', event.tag);

  if (event.tag === 'background-sync') {
    event.waitUntil(
      // Handle background sync logic here
      console.log('Service Worker: Performing background sync')
    );
  }
});

// Push notification handling
self.addEventListener('push', event => {
  console.log('Service Worker: Push received', event);

  const options = {
    body: event.data ? event.data.text() : 'New notification from Fire Shakti',
    icon: '/static/icons/icon-192x192.svg',
    badge: '/static/icons/icon-72x72.svg',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'View Details',
        icon: '/static/icons/icon-192x192.svg'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/static/icons/icon-192x192.svg'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification('Fire Shakti', options)
  );
});

// Notification click handling
self.addEventListener('notificationclick', event => {
  console.log('Service Worker: Notification clicked', event);

  event.notification.close();

  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/dashboard')
    );
  }
});