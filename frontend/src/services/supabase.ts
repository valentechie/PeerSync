import { createClient } from '@supabase/supabase-js';

// Ambos valores son públicos: la clave publicable está pensada para el navegador,
// y RLS impide que acceda a las tablas. Las variables permiten usar otro proyecto.
const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || 'https://pfsswyaxrczroswnapsl.supabase.co';
const SUPABASE_PUBLISHABLE_KEY = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY || 'sb_publishable_U5sUGuve58Eauo_dQ3bONA_KaN58pqu';

export const supabase = createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY);
