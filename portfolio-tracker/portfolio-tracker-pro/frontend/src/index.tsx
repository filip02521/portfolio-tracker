import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// DISABLED: Service Worker causes conflicts with Hot Module Replacement in development
// Service Worker will cause loops with HMR, so it's disabled during development
// Uncomment this for production builds only
// Register Service Worker for PWA
// if ('serviceWorker' in navigator && process.env.NODE_ENV === 'production') {
//   window.addEventListener('load', () => {
//     navigator.serviceWorker
//       .register('/service-worker.js')
//       .then((registration) => {
//         console.log('Service Worker registered:', registration.scope);
//         
//         // Check for updates periodically
//         setInterval(() => {
//           registration.update();
//         }, 60000); // Check every minute
//       })
//       .catch((error) => {
//         console.warn('Service Worker registration failed:', error);
//       });
//   });
// }

// CRITICAL: Unregister ALL service workers in development to prevent loops
// This MUST run BEFORE anything else to prevent Service Worker from intercepting requests
if ('serviceWorker' in navigator) {
  // Immediately unregister all service workers
  navigator.serviceWorker.getRegistrations().then((registrations) => {
    if (registrations.length > 0) {
      console.log('[DEV] Unregistering', registrations.length, 'Service Worker(s) to prevent loops...');
      const unregisterPromises = registrations.map((registration) => {
        return registration.unregister().then((unregistered) => {
          console.log('[DEV] Service Worker unregistered:', unregistered);
          return unregistered;
        });
      });
      
      Promise.all(unregisterPromises).then(() => {
        // Clear all caches after unregistering
        return caches.keys();
      }).then((cacheKeys) => {
        console.log('[DEV] Clearing', cacheKeys.length, 'cache(s)...');
        const deletePromises = cacheKeys.map((key) => {
          return caches.delete(key).then((deleted) => {
            console.log('[DEV] Cache deleted:', key, deleted);
            return deleted;
          });
        });
        return Promise.all(deletePromises);
      }).then(() => {
        console.log('[DEV] All Service Workers and caches cleared. Page should reload normally now.');
        // Force a reload to ensure clean state (but only once)
        if (!sessionStorage.getItem('sw_cleared')) {
          sessionStorage.setItem('sw_cleared', 'true');
          setTimeout(() => {
            window.location.reload();
          }, 100);
        }
      });
    }
  });
  
  // Prevent any new registrations in development
  const originalRegister = navigator.serviceWorker.register;
  navigator.serviceWorker.register = function(...args) {
    console.warn('[DEV] Service Worker registration blocked in development mode');
    return Promise.reject(new Error('Service Worker registration disabled in development'));
  };
}

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
