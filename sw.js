// Service Worker fuer XsiKOM-BewerbungsBOT PWA
const CACHE_NAME = 'xsikom-bot-v1';
const URLS_TO_CACHE = [
    '/',
    '/dashboard',
    '/aaliyah',
    '/lebenslauf',
    '/bewerbungen',
    '/premium',
    '/manifest.json'
];

// Installation
self.addEventListener('install', (event) => {
    console.log('Service Worker installiert');
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(URLS_TO_CACHE);
        })
    );
});

// Aktivierung
self.addEventListener('activate', (event) => {
    console.log('Service Worker aktiv');
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// Fetch (Network First Strategy)
self.addEventListener('fetch', (event) => {
    event.respondWith(
        fetch(event.request)
            .then((response) => {
                // Online: Antwort cachen
                if (response.status === 200) {
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(event.request, responseClone);
                    });
                }
                return response;
            })
            .catch(() => {
                // Offline: Cache verwenden
                return caches.match(event.request);
            })
    );
});

// Push Notifications
self.addEventListener('push', (event) => {
    const options = {
        body: event.data ? event.data.text() : 'Neue Benachrichtigung!',
        icon: '/static/icon-192.png',
        badge: '/static/icon-96.png',
        vibrate: [200, 100, 200],
        data: {
            url: '/'
        }
    };
    event.waitUntil(
        self.registration.showNotification('XsiKOM Bot', options)
    );
});

// Click auf Notification
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    event.waitUntil(
        clients.openWindow(event.notification.data.url)
    );
});