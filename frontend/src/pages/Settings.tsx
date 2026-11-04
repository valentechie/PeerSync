import React, { useState } from 'react';
import { Settings as SettingsIcon, Bell, Shield, Palette, Save } from 'lucide-react';
import { SuccessState } from '../components/UIStates';

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
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <div>
        <h1 className="text-2xl font-black text-slate-900 flex items-center space-x-2">
          <SettingsIcon className="w-6 h-6 text-indigo-600" />
          <span>Configuración</span>
        </h1>
        <p className="text-sm text-slate-500">Personaliza tus preferencias de la plataforma y notificaciones</p>
      </div>

      {success && (
        <SuccessState title="Configuración guardada" message="Tus preferencias han sido actualizadas correctamente." />
      )}

      <form onSubmit={handleSave} className="bg-white rounded-3xl border border-slate-200 p-8 shadow-xs space-y-6">
        <div className="space-y-6">
          <div className="flex items-center justify-between p-4 bg-slate-50 border border-slate-200 rounded-2xl">
            <div className="flex items-center space-x-3">
              <Bell className="w-5 h-5 text-indigo-600" />
              <div>
                <h4 className="text-sm font-bold text-slate-900">Notificaciones Push</h4>
                <p className="text-xs text-slate-500">Recibe alertas cuando un compañero acepte tu solicitud de intercambio.</p>
              </div>
            </div>
            <input
              type="checkbox"
              checked={notifications}
              onChange={e => setNotifications(e.target.checked)}
              className="w-5 h-5 text-indigo-600 rounded focus:ring-indigo-500"
            />
          </div>

          <div className="flex items-center justify-between p-4 bg-slate-50 border border-slate-200 rounded-2xl">
            <div className="flex items-center space-x-3">
              <Shield className="w-5 h-5 text-indigo-600" />
              <div>
                <h4 className="text-sm font-bold text-slate-900">Alertas por Correo</h4>
                <p className="text-xs text-slate-500">Recibe resúmenes semanales de tus sesiones y progreso.</p>
              </div>
            </div>
            <input
              type="checkbox"
              checked={emailAlerts}
              onChange={e => setEmailAlerts(e.target.checked)}
              className="w-5 h-5 text-indigo-600 rounded focus:ring-indigo-500"
            />
          </div>

          <div className="flex items-center justify-between p-4 bg-slate-50 border border-slate-200 rounded-2xl">
            <div className="flex items-center space-x-3">
              <Palette className="w-5 h-5 text-indigo-600" />
              <div>
                <h4 className="text-sm font-bold text-slate-900">Modo Oscuro Automático</h4>
                <p className="text-xs text-slate-500">Adaptar la interfaz según las preferencias del sistema operativo.</p>
              </div>
            </div>
            <input
              type="checkbox"
              checked={darkMode}
              onChange={e => setDarkMode(e.target.checked)}
              className="w-5 h-5 text-indigo-600 rounded focus:ring-indigo-500"
            />
          </div>
        </div>

        <div className="pt-4 flex justify-end">
          <button
            type="submit"
            className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm rounded-xl shadow-md shadow-indigo-200 transition flex items-center space-x-2"
          >
            <Save className="w-4 h-4" />
            <span>Guardar Preferencias</span>
          </button>
        </div>
      </form>
    </div>
  );
};
