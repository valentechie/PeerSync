import React, { useState } from 'react';
import { Bell, Shield, Palette, Save, type LucideIcon } from 'lucide-react';
import { SuccessState } from '../components/UIStates';

const ToggleRow: React.FC<{
  icon: LucideIcon;
  title: string;
  description: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}> = ({ icon: Icon, title, description, checked, onChange }) => (
  <label className="flex items-center justify-between gap-4 py-5 first:pt-0 border-b border-line last:border-b-0 cursor-pointer">
    <span className="flex items-start gap-3">
      <Icon className="w-5 h-5 text-teach shrink-0 mt-0.5" />
      <span>
        <span className="block text-sm font-bold">{title}</span>
        <span className="block text-sm text-muted">{description}</span>
      </span>
    </span>
    <input type="checkbox" role="switch" checked={checked} onChange={e => onChange(e.target.checked)} className="switch" />
  </label>
);

export const Settings: React.FC = () => {
  const [notifications, setNotifications] = useState(true);
  const [emailAlerts, setEmailAlerts] = useState(true);
  const [darkMode, setDarkMode] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSuccess(true);
    setTimeout(() => setSuccess(false), 3000);
  };

  return (
    <div className="page max-w-3xl space-y-8">
      <div>
        <h1 className="page-title">Configuración</h1>
        <p className="page-subtitle">Personaliza tus preferencias de la plataforma y notificaciones.</p>
      </div>

      {success && (
        <SuccessState title="Configuración guardada" message="Tus preferencias han sido actualizadas correctamente." />
      )}

      <form onSubmit={handleSave} className="card p-6 sm:p-8 space-y-6">
        <div>
          <ToggleRow
            icon={Bell}
            title="Notificaciones push"
            description="Recibe alertas cuando un compañero acepte tu solicitud de intercambio."
            checked={notifications}
            onChange={setNotifications}
          />
          <ToggleRow
            icon={Shield}
            title="Alertas por correo"
            description="Recibe resúmenes semanales de tus sesiones y progreso."
            checked={emailAlerts}
            onChange={setEmailAlerts}
          />
          <ToggleRow
            icon={Palette}
            title="Modo oscuro automático"
            description="Adaptar la interfaz según las preferencias del sistema operativo."
            checked={darkMode}
            onChange={setDarkMode}
          />
        </div>

        <div className="flex justify-end">
          <button type="submit" className="btn btn-primary">
            <Save className="w-4 h-4" />
            <span>Guardar preferencias</span>
          </button>
        </div>
      </form>
    </div>
  );
};
