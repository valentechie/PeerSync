import React, { useEffect, useRef, useState } from 'react';
import { CheckCircle2, Lightbulb, MessageSquareQuote, Scale, Search } from 'lucide-react';
import type { ActionKey, FlowAction } from '../services/contrastaFlow';

const ITEMS: Record<ActionKey, { label: string; icon: React.ElementType }> = {
  start: { label: 'Start a round', icon: Scale },
  hint: { label: 'We need a hint', icon: Lightbulb },
  idea: { label: 'Check an idea', icon: Search },
  practice: { label: 'Practice an explanation', icon: MessageSquareQuote },
  conclusion: { label: "We've reached a conclusion", icon: CheckCircle2 },
};

/** Va dentro del formulario del chat. Las desactivadas se pueden alcanzar para leer el motivo. */
export const ContrastaActionMenu: React.FC<{ actions: FlowAction[]; onSelect: (key: ActionKey) => void }> = ({ actions, onSelect }) => {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const itemsRef = useRef<(HTMLButtonElement | null)[]>([]);

  useEffect(() => {
    if (!open) return;
    itemsRef.current[0]?.focus();
    const handleOutside = (e: MouseEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handleOutside);
    return () => document.removeEventListener('mousedown', handleOutside);
  }, [open]);

  const close = () => {
    setOpen(false);
    buttonRef.current?.focus();
  };

  const handleKey = (e: React.KeyboardEvent, index: number) => {
    const last = actions.length - 1;
    const target = { ArrowDown: index === last ? 0 : index + 1, ArrowUp: index === 0 ? last : index - 1, Home: 0, End: last }[e.key];
    if (target !== undefined) {
      e.preventDefault();
      itemsRef.current[target]?.focus();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      close();
    } else if (e.key === 'Tab') {
      setOpen(false);
    }
  };

  return (
    <div ref={rootRef} className="contents">
      <button
        ref={buttonRef}
        type="button"
        onClick={() => setOpen(current => !current)}
        disabled={actions.length === 0}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label="Contrasta actions"
        title="Contrasta actions"
        className="btn btn-secondary px-4!"
      >
        <Scale className="w-4 h-4" aria-hidden="true" />
      </button>
      {open && (
        <div role="menu" aria-label="Contrasta actions" className="card absolute bottom-full left-4 mb-2 z-10 w-72 max-w-[calc(100%-2rem)] p-2 space-y-1">
          {actions.map((action, index) => {
            const { label, icon: Icon } = ITEMS[action.key];
            return (
              <button
                key={action.key}
                ref={element => {
                  itemsRef.current[index] = element;
                }}
                type="button"
                role="menuitem"
                aria-disabled={!action.enabled}
                onKeyDown={e => handleKey(e, index)}
                onClick={() => {
                  if (!action.enabled) return;
                  setOpen(false);
                  onSelect(action.key);
                }}
                className={`w-full flex items-start gap-2 rounded-xl px-3 py-2.5 text-left text-sm font-bold transition-colors ${action.enabled ? 'cursor-pointer hover:bg-teach-soft' : 'cursor-not-allowed opacity-60'}`}
              >
                <Icon className="w-4 h-4 shrink-0 mt-0.5 text-teach" aria-hidden="true" />
                <span className="min-w-0">
                  {label}
                  {action.reason && <span className="block text-xs font-normal text-muted">{action.reason}</span>}
                </span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};
