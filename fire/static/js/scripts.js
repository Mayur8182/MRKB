// Fire Shakti PWA JavaScript
console.log('🔥 Fire Shakti PWA Loaded');

// PWA Installation handling
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
  console.log('PWA: beforeinstallprompt event fired');
  e.preventDefault();
  deferredPrompt = e;
  showInstallPromotion();
});

function showInstallPromotion() {
  // Show install button or banner
  const installBtn = document.getElementById('install-btn');
  if (installBtn) {
    installBtn.style.display = 'block';
    installBtn.addEventListener('click', installApp);
  }
}

async function installApp() {
  if (deferredPrompt) {
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    console.log(`PWA: User response: ${outcome}`);
    deferredPrompt = null;
    hideInstallPromotion();
  }
}

function hideInstallPromotion() {
  const installBtn = document.getElementById('install-btn');
  if (installBtn) {
    installBtn.style.display = 'none';
  }
}

// App installed event
window.addEventListener('appinstalled', (evt) => {
  console.log('PWA: App was installed');
  hideInstallPromotion();
});

// Check if running in standalone mode
if (window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true) {
  console.log('PWA: Running in standalone mode');
  document.body.classList.add('pwa-standalone');
}

// Service Worker registration
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js')
      .then(registration => {
        console.log('Service Worker registered: ', registration);
      })
      .catch(error => {
        console.error('Service Worker registration failed: ', error);
      });
  });
}

// Utility functions
function showLoading(element) {
  if (element) {
    element.innerHTML = '<span class="loading"></span> Loading...';
    element.disabled = true;
  }
}

function hideLoading(element, originalText) {
  if (element) {
    element.innerHTML = originalText;
    element.disabled = false;
  }
}

// Form validation helpers
function validateEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
}

function validatePhone(phone) {
  const re = /^[+]?[\d\s\-\(\)]{10,}$/;
  return re.test(phone);
}

// Network status handling
window.addEventListener('online', () => {
  console.log('PWA: Back online');
  document.body.classList.remove('offline');
});

window.addEventListener('offline', () => {
  console.log('PWA: Gone offline');
  document.body.classList.add('offline');
});

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
  console.log('🔥 Fire Shakti PWA Ready');
  
  // Add offline indicator styles
  if (!navigator.onLine) {
    document.body.classList.add('offline');
  }
});
