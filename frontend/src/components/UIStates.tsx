import React from 'react';
import { Loader2, AlertCircle, Inbox, CheckCircle2 } from 'lucide-react';

export const LoadingState: React.FC<{ message?: string }> = ({ message = 'Cargando contenido...' }) => (
  <div className="flex flex-col items-center justify-center p-12 space-y-4">
    <Loader2 className="w-8 h-8 text-indigo-400 animate-spin" />
    <p className="text-sm font-medium text-slate-400">{message}</p>
  </div>
);

export const ErrorState: React.FC<{ message?: string; onRetry?: () => void }> = ({ 
  message = 'Ocurrió un error al cargar los datos.', 
  onRetry 
}) => (
  <div className="flex flex-col items-center justify-center p-8 bg-rose-950/40 border border-rose-900/50 rounded-3xl text-center space-y-3 backdrop-blur-xl shadow-xl">
    <AlertCircle className="w-10 h-10 text-rose-400" />
    <h3 className="text-lg font-bold text-rose-200">¡Algo salió mal!</h3>
    <p className="text-sm text-rose-300 max-w-md">{message}</p>
    {onRetry && (
      <button 
        onClick={onRetry}
        className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white text-sm font-bold rounded-xl transition shadow-lg shadow-rose-900/50"
      >
        Intentar nuevamente
      </button>
    )}
  </div>
);

export const EmptyState: React.FC<{ title?: string; description?: string; actionLabel?: string; onAction?: () => void }> = ({
  title = 'No hay elementos',
  description = 'Aún no hay registros disponibles para mostrar en esta sección.',
  actionLabel,
  onAction
}) => (
  <div className="flex flex-col items-center justify-center p-12 bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-3xl text-center space-y-4 shadow-2xl">
    <div className="w-16 h-16 bg-indigo-950 text-indigo-400 rounded-2xl flex items-center justify-center border border-indigo-800/50 shadow-inner">
      <Inbox className="w-8 h-8" />
    </div>
    <div className="space-y-1">
      <h3 className="text-lg font-bold text-slate-100">{title}</h3>
      <p className="text-sm text-slate-400 max-w-sm">{description}</p>
    </div>
    {actionLabel && onAction && (
      <button
        onClick={onAction}
        className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-bold rounded-xl transition shadow-lg shadow-indigo-600/30"
      >
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
  <div className="flex items-start p-4 bg-emerald-950/40 border border-emerald-900/60 rounded-2xl space-x-3 backdrop-blur-xl shadow-xl">
    <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
    <div className="flex-1 text-sm">
      <h4 className="font-bold text-emerald-200">{title}</h4>
      <p className="text-emerald-300 mt-0.5">{message}</p>
    </div>
    {onDismiss && (
      <button onClick={onDismiss} className="text-emerald-400 hover:text-emerald-200 text-sm font-bold">×</button>
    )}
  </div>
);
