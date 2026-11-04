// En producción la API comparte dominio con el frontend.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? (import.meta.env.PROD ? '/api' : 'http://localhost:8000/api');

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

interface ValidationIssue {
  loc: (string | number)[];
}

const validationMessage = (issues: ValidationIssue[]): string => {
  const { loc } = issues[0];
  const field = loc[loc.length - 1];
  if (field === 'name') return 'Revisa el nombre: no puede estar vacío ni superar los 100 caracteres.';
  if (field === 'bio') return 'La biografía no puede superar los 1000 caracteres.';
  return 'Revisa los datos introducidos.';
};

export async function apiRequest<T>(path: string, options: { method?: string; body?: unknown; token?: string } = {}): Promise<T> {
  const { method = 'GET', body, token } = options;

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: {
        ...(body !== undefined && { 'Content-Type': 'application/json' }),
        ...(token && { Authorization: `Bearer ${token}` }),
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(0, 'No se pudo conectar con el servidor. Inténtalo de nuevo.');
  }

  if (response.ok) return response.json() as Promise<T>;

  const detail: unknown = await response.json().then(data => data.detail, () => undefined);
  if (response.status === 422 && Array.isArray(detail) && detail.length > 0) {
    throw new ApiError(422, validationMessage(detail as ValidationIssue[]));
  }
  throw new ApiError(response.status, typeof detail === 'string' ? detail : 'Ocurrió un error inesperado. Inténtalo de nuevo.');
}
