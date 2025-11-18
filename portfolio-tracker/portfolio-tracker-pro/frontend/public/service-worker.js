// Service Worker for Portfolio Tracker PWA
// DISABLED in development mode to prevent conflicts with Hot Module Replacement
// ALWAYS unregister in development mode
const isDevelopment = self.location.hostname === 'localhost';

// If in development, immediately unregister and stop all processing
if (isDevelopment) {
  // Immediately unregister
  self.addEventListener('install', () => {
    self.skipWaiting();
  });
  
  self.addEventListener('activate', (event) => {
    event.waitUntil(
      Promise.all([
        // Unregister this service worker
        self.registration.unregister(),
        // Delete all caches
        caches.keys().then((cacheNames) => {
          return Promise.all(
            cacheNames.map((cacheName) => caches.delete(cacheName))
          );
        }),
        // Claim clients to ensure cleanup
        self.clients.claim()
      ]).then(() => {
        console.log('Service Worker fully unregistered and caches cleared in development mode');
      })
    );
  });
  
  // Don't process ANY fetch events in development - just pass through
  self.addEventListener('fetch', (event) => {
    // In development, always fetch from network without caching
    // This prevents the Service Worker from interfering with HMR
    event.respondWith(
      fetch(event.request).catch(() => {
        // If fetch fails, return a proper Response, not undefined
        return new Response('Network error', { status: 503 });
      })
    );
  });
  
  // Stop execution here - don't process production code
  return;
}

const CACHE_NAME = 'portfolio-tracker-v2';
const RUNTIME_CACHE = 'portfolio-tracker-runtime-v2';
const API_CACHE = 'portfolio-tracker-api-v2';

// Assets to cache on install
const PRECACHE_ASSETS = [
  '/',
  '/static/css/main.css',
  '/static/js/main.js',
  '/manifest.json',
];

// API endpoints to cache (with short TTL)
const CACHEABLE_API_PATHS = [
  '/api/portfolio/summary',
  '/api/portfolio/assets',
  '/api/portfolio/history',
  '/api/market/watchlist',
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      // Add each asset individually to avoid one failure blocking others
      return Promise.allSettled(
        PRECACHE_ASSETS.map((asset) =>
          cache.add(asset).catch((err) => {
            // Silently fail for missing assets in dev mode
            console.debug(`Service Worker: Failed to cache ${asset}`, err);
            return null;
          })
        )
      ).then(() => {
        console.log('Service Worker: Precache completed');
      });
    })
  );
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME && name !== RUNTIME_CACHE && name !== API_CACHE)
          .map((name) => caches.delete(name))
      );
    })
  );
  return self.clients.claim();
});

// Fetch event - network first, fallback to cache
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip cross-origin requests
  if (url.origin !== location.origin) {
    return;
  }

  // API requests - network first with cache fallback
  if (url.pathname.startsWith('/api/')) {
    const isCacheable = CACHEABLE_API_PATHS.some(path => url.pathname.includes(path));
    
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Clone response for potential caching
          const responseClone = response.clone();
          // Cache successful GET requests for cacheable endpoints
          if (request.method === 'GET' && response.status === 200 && isCacheable) {
            caches.open(API_CACHE).then((cache) => {
              // Set cache with expiration (5 minutes for API data)
              const cacheRequest = request.clone();
              cache.put(cacheRequest, responseClone).catch(() => {
                // Silently fail if cache is full
              });
            });
          }
          return response;
        })
        .catch(() => {
          // Network failed - try cache for GET requests
          if (request.method === 'GET') {
            return caches.match(request).then((cachedResponse) => {
              if (cachedResponse) {
                // Return cached response with a header indicating it's stale
                const headers = new Headers(cachedResponse.headers);
                headers.set('X-Served-From-Cache', 'true');
                return new Response(cachedResponse.body, {
                  status: cachedResponse.status,
                  statusText: cachedResponse.statusText,
                  headers: headers,
                });
              }
              return new Response(
                JSON.stringify({ error: 'Offline', message: 'No cached data available' }),
                { 
                  status: 503,
                  headers: { 'Content-Type': 'application/json' }
                }
              );
            });
          }
          return new Response(
            JSON.stringify({ error: 'Offline', message: 'Request cannot be cached' }),
            { 
              status: 503,
              headers: { 'Content-Type': 'application/json' }
            }
          );
        })
    );
    return;
  }

  // Static assets - cache first, fallback to network
  if (
    request.destination === 'script' ||
    request.destination === 'style' ||
    request.destination === 'image' ||
    request.destination === 'font'
  ) {
    event.respondWith(
      caches.match(request).then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse;
        }
        return fetch(request).then((response) => {
          if (response.status === 200) {
            const responseClone = response.clone();
            caches.open(RUNTIME_CACHE).then((cache) => {
              cache.put(request, responseClone);
            });
          }
          return response;
        });
      })
    );
    return;
  }

  // HTML pages - network first, fallback to cache
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response.status === 200) {
            const responseClone = response.clone();
            caches.open(RUNTIME_CACHE).then((cache) => {
              cache.put(request, responseClone);
            });
          }
          return response;
        })
        .catch(() => {
          return caches.match('/') || new Response('Offline', { status: 503 });
        })
    );
    return;
  }

  // Default - network first
  event.respondWith(
    fetch(request).catch(() => {
      return caches.match(request);
    })
  );
});

// Background sync for offline actions (future enhancement)
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync') {
    event.waitUntil(
      // Handle background sync tasks
      Promise.resolve()
    );
  }
});

// Push notifications (future enhancement)
self.addEventListener('push', (event) => {
  const data = event.data ? event.data.json() : {};
  const title = data.title || 'Portfolio Tracker';
  const options = {
    body: data.body || 'You have a new notification',
    icon: '/logo192.png',
    badge: '/logo192.png',
    data: data.url || '/',
  };

  event.waitUntil(self.registration.showNotification(title, options));
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(
    clients.openWindow(event.notification.data || '/')
  );
});

