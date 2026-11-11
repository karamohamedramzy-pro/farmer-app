/** Capture the browser's one-shot installation prompt as soon as the app loads. */
export interface InstallPromptEvent extends Event {
  prompt(): Promise<void>;
  userChoice: Promise<{outcome: 'accepted' | 'dismissed'; platform: string}>;
}
let deferredPrompt: InstallPromptEvent | null = null;
let installed = false;
const listeners = new Set<() => void>();
const notify = () => listeners.forEach(listener => listener());
if (typeof window !== 'undefined') {
  window.addEventListener('beforeinstallprompt', event => {
    event.preventDefault();
    deferredPrompt = event as InstallPromptEvent;
    notify();
  });
  window.addEventListener('appinstalled', () => {
    deferredPrompt = null;
    installed = true;
    notify();
  });
}
export const hasInstallPrompt = () => deferredPrompt !== null;
export const isStandalone = () => installed || Boolean(window.matchMedia?.('(display-mode: standalone)').matches) || (navigator as Navigator & {standalone?: boolean}).standalone === true;
export const subscribeInstall = (listener: () => void) => { listeners.add(listener); return () => { listeners.delete(listener); }; };
export async function showInstallPrompt(): Promise<'accepted' | 'dismissed' | 'unavailable'> {
  const event = deferredPrompt;
  if (!event) return 'unavailable';
  // A deferred event can only be used once, including when the user dismisses it.
  deferredPrompt = null;
  notify();
  try {
    await event.prompt();
    return (await event.userChoice).outcome;
  } catch {
    return 'unavailable';
  }
}
export function deviceInfo() {
  const ua = navigator.userAgent;
  const ios = /iPad|iPhone|iPod/i.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  return {ios, mobile: ios || /Android|Mobile/i.test(ua)};
}

/** Only the production build contains sw.js; HTTPS or localhost is required. */
export function registerServiceWorker() {
  if (import.meta.env.PROD && 'serviceWorker' in navigator && window.isSecureContext) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js').catch(error => console.warn('Service worker registration failed:', error));
    });
  }
}
