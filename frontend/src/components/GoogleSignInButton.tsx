import React, { useEffect, useRef, useState } from 'react';
import { ErrorState } from './UIStates';

interface GoogleIdentityServices {
  initialize: (config: { client_id: string; callback: (response: { credential: string }) => void }) => void;
  renderButton: (parent: HTMLElement, options: Record<string, string | number>) => void;
}

declare global {
  interface Window {
    google?: { accounts: { id: GoogleIdentityServices } };
  }
}

const CLIENT_ID: string | undefined = import.meta.env.VITE_GOOGLE_CLIENT_ID;
const SCRIPT_URL = 'https://accounts.google.com/gsi/client';
const MAX_BUTTON_WIDTH = 400; // Límite que impone Google.

let scriptPromise: Promise<void> | null = null;
let initialized = false;
let onCredentialReceived: ((credential: string) => void) | null = null;

const loadScript = (): Promise<void> => {
  scriptPromise ??= new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = SCRIPT_URL;
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => {
      // Permite reintentar al volver a montar el botón.
      scriptPromise = null;
      script.remove();
      reject(new Error('No se pudo cargar Google Identity Services'));
    };
    document.head.append(script);
  });
  return scriptPromise;
};

export const GoogleSignInButton: React.FC<{ onCredential: (credential: string) => void }> = ({ onCredential }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [loadFailed, setLoadFailed] = useState(false);

  useEffect(() => {
    onCredentialReceived = onCredential;
    return () => {
      onCredentialReceived = null;
    };
  });

  useEffect(() => {
    if (!CLIENT_ID) return;
    const clientId = CLIENT_ID;
    let cancelled = false;
    loadScript()
      .then(() => {
        const container = containerRef.current;
        const identity = window.google?.accounts.id;
        if (cancelled || !container || !identity) return;
        // Google avisa si se inicializa más de una vez.
        if (!initialized) {
          identity.initialize({
            client_id: clientId,
            callback: ({ credential }) => onCredentialReceived?.(credential),
          });
          initialized = true;
        }
        identity.renderButton(container, {
          theme: 'outline',
          size: 'large',
          shape: 'pill',
          text: 'continue_with',
          locale: 'es',
          width: Math.min(container.clientWidth, MAX_BUTTON_WIDTH),
        });
      })
      .catch(() => {
        if (!cancelled) setLoadFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (!CLIENT_ID) return <ErrorState message="Falta configurar el acceso con Google (VITE_GOOGLE_CLIENT_ID)." />;
  if (loadFailed) {
    return <ErrorState message="No se pudo cargar el acceso con Google. Revisa tu conexión o tu bloqueador de contenido y recarga la página." />;
  }
  return <div ref={containerRef} className="w-full min-h-11" />;
};
