import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import { errorMessage } from '../services/api';
import { fetchFlow, type Flow } from '../services/contrastaFlow';

const POLL_INTERVAL_MS = 3000;

export interface FlowContextValue {
  roomId: string;
  token: string;
  userId: string;
  flow: Flow;
  readOnly: boolean;
  apply: (flow: Flow) => void;
  refresh: () => Promise<void>;
  openForm: (form: FormKey) => void;
  focusComposer: () => void;
  insertInComposer: (text: string) => void;
}

export type FormKey = 'start' | 'hint' | 'idea' | 'practice' | 'conclusion' | 'check';

export const FlowContext = createContext<FlowContextValue | null>(null);

export const useFlowContext = () => {
  const value = useContext(FlowContext);
  if (!value) throw new Error('useFlowContext outside FlowContext');
  return value;
};

/** Consulta aparte de la del chat: si esto falla, los mensajes siguen llegando igual. */
export const useContrastaFlow = (token: string | null, roomId: string | undefined) => {
  const [flow, setFlow] = useState<Flow | null>(null);
  // Una consulta que salió antes de una acción no debe pisar su resultado.
  const version = useRef(0);

  const refresh = useCallback(async () => {
    if (!token || !roomId) return;
    const started = version.current;
    try {
      const latest = await fetchFlow(token, roomId);
      if (version.current === started) setFlow(latest);
    } catch {
      // La sala ya avisa de la conexión perdida; aquí se reintenta en la siguiente consulta.
    }
  }, [token, roomId]);

  const apply = useCallback((latest: Flow) => {
    version.current += 1;
    setFlow(latest);
  }, []);

  useEffect(() => {
    if (!token || !roomId) return;
    void refresh();
    const timer = setInterval(refresh, POLL_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [token, roomId, refresh]);

  return { flow, apply, refresh };
};

/** Ejecuta una acción de una tarjeta con su propio estado: un fallo aquí no afecta al chat. */
export const useFlowAction = () => {
  const { apply, refresh } = useFlowContext();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const run = useCallback(
    async (action: () => Promise<Flow | unknown>, onDone?: () => void) => {
      setBusy(true);
      setError('');
      try {
        const result = await action();
        if (result && typeof result === 'object' && 'actions' in result) apply(result as Flow);
        else await refresh();
        onDone?.();
        return true;
      } catch (err) {
        setError(errorMessage(err));
        // El estado pudo cambiar: otra persona se adelantó o quedó registrado el fallo.
        void refresh();
        return false;
      } finally {
        setBusy(false);
      }
    },
    [apply, refresh],
  );

  return { busy, error, run };
};

/** Borrador privado: sobrevive a recargas de esta pestaña y no sale de ella hasta enviarlo. */
export const useDraft = (key: string, initial = ''): [string, (value: string) => void] => {
  const storageKey = `peersync_draft:${key}`;
  const [value, setValue] = useState(() => {
    try {
      return sessionStorage.getItem(storageKey) ?? initial;
    } catch {
      return initial;
    }
  });
  const update = useCallback(
    (next: string) => {
      setValue(next);
      try {
        if (next) sessionStorage.setItem(storageKey, next);
        else sessionStorage.removeItem(storageKey);
      } catch {
        // Sin almacenamiento, el borrador vive solo en memoria.
      }
    },
    [storageKey],
  );
  return [value, update];
};
