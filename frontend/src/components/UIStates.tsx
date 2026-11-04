import React from 'react';
import { Loader2, AlertCircle, Inbox, CheckCircle2, X } from 'lucide-react';

export const LoadingState: React.FC<{ message?: string }> = ({ message = 'Cargando contenido...' }) => (
  <div className="flex flex-col items-center justify-center p-12 space-y-4" role="status">
    <Loader2 className="w-8 h-8 text-teach animate-spin" />
    <p className="text-sm font-semibold text-muted">{message}</p>
  </div>
);

export const ErrorState: React.FC<{ message?: string; onRetry?: () => void }> = ({
  message = 'Ocurrió un error al cargar los datos.',
  onRetry
}) => (
  <div className="flex items-start gap-3 p-4 bg-learn-soft border border-learn/25 rounded-2xl" role="alert">
    <AlertCircle className="w-5 h-5 text-learn shrink-0 mt-0.5" />
    <div className="flex-1 text-sm space-y-2">
      <h3 className="font-sans font-bold text-learn-strong tracking-normal">¡Algo salió mal!</h3>
      <p className="text-learn-strong">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="btn btn-secondary mt-1">
          Intentar nuevamente
        </button>
      )}
    </div>
  </div>
);

export const EmptyState: React.FC<{ title?: string; description?: string; actionLabel?: string; onAction?: () => void }> = ({
  title = 'No hay elementos',
  description = 'Aún no hay registros disponibles para mostrar en esta sección.',
  actionLabel,
  onAction
}) => (
  <div className="card flex flex-col items-center justify-center p-12 text-center space-y-4">
    <div className="w-14 h-14 bg-teach-soft text-teach rounded-full flex items-center justify-center">
      <Inbox className="w-7 h-7" />
    </div>
    <div className="space-y-1">
      <h3 className="text-xl text-ink">{title}</h3>
      <p className="text-sm text-muted max-w-sm">{description}</p>
    </div>
    {actionLabel && onAction && (
      <button onClick={onAction} className="btn btn-primary">
        {actionLabel}
      </button>
    )}
  </div>
);

export const SuccessState: React.FC<{ title: string; message: string; onDismiss?: () => void }> = ({
  title,
  message,
  onDismiss
}) => (
  <div className="flex items-start gap-3 p-4 bg-teach-soft border border-teach/25 rounded-2xl" role="status">
    <CheckCircle2 className="w-5 h-5 text-teach shrink-0 mt-0.5" />
    <div className="flex-1 text-sm">
      <h4 className="font-bold text-teach-strong">{title}</h4>
      <p className="text-teach-strong mt-0.5">{message}</p>
    </div>
    {onDismiss && (
      <button onClick={onDismiss} aria-label="Cerrar aviso" className="text-teach-strong cursor-pointer">
        <X className="w-4 h-4" />
      </button>
    )}
  </div>
);
