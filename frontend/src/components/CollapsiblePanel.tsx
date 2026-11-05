import React, { useEffect, useState } from 'react';
import { ChevronRight } from 'lucide-react';

/** Al plegar, el contenido sigue montado: se conservan borradores, estado y consultas. */
export const CollapsiblePanel: React.FC<{
  label: string;
  title: React.ReactNode;
  badge?: React.ReactNode;
  /** Se abre si pasa a ser cierto, pero nunca se pliega solo. */
  openWhen?: boolean;
  bodyClassName?: string;
  children: React.ReactNode;
}> = ({ label, title, badge, openWhen = false, bodyClassName = 'space-y-4', children }) => {
  const [open, setOpen] = useState(openWhen);

  useEffect(() => {
    if (openWhen) setOpen(true);
  }, [openWhen]);

  return (
    <details className="card p-5" aria-label={label} open={open} onToggle={e => setOpen(e.currentTarget.open)}>
      <summary className="flex items-center gap-2 cursor-pointer list-none [&::-webkit-details-marker]:hidden">
        <h2 className="text-lg text-ink flex items-center gap-2 min-w-0">{title}</h2>
        {badge}
        <ChevronRight className={`w-4 h-4 ml-auto shrink-0 text-muted transition-transform ${open ? 'rotate-90' : ''}`} aria-hidden="true" />
      </summary>
      <div className={`mt-4 ${bodyClassName}`}>{children}</div>
    </details>
  );
};
