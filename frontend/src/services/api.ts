// En producción la API comparte dominio con el frontend.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? (import.meta.env.PROD ? '/api' : 'http://localhost:8000/api');

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

/** Dirección completa de un recurso que devuelve la API, como una foto de perfil. */
export const apiAssetUrl = (path: string) => `${API_BASE_URL}${path}`;

export const errorMessage = (err: unknown) =>
  err instanceof Error ? err.message : 'An unexpected error occurred. Please try again.';

interface ValidationIssue {
  loc: (string | number)[];
}

const validationMessage = (issues: ValidationIssue[]): string => {
  const { loc } = issues[0];
  const field = loc[loc.length - 1];
  if (field === 'name') return "Check the name: it can't be empty or longer than 100 characters.";
  if (field === 'bio') return "The bio can't be longer than 1000 characters.";
  return 'Check the details you entered.';
};

const toApiError = async (response: Response): Promise<ApiError> => {
  const detail: unknown = await response.json().then(data => data.detail, () => undefined);
  if (response.status === 422 && Array.isArray(detail) && detail.length > 0) {
    return new ApiError(422, validationMessage(detail as ValidationIssue[]));
  }
  return new ApiError(response.status, typeof detail === 'string' ? detail : 'An unexpected error occurred. Please try again.');
};

const send = async (path: string, init: RequestInit): Promise<Response> => {
  try {
    return await fetch(`${API_BASE_URL}${path}`, init);
  } catch {
    throw new ApiError(0, "Couldn't connect to the server. Please try again.");
  }
};

export async function apiRequest<T>(path: string, options: { method?: string; body?: unknown; token?: string } = {}): Promise<T> {
  const { method = 'GET', body, token } = options;

  const response = await send(path, {
    method,
    headers: {
      ...(body !== undefined && { 'Content-Type': 'application/json' }),
      ...(token && { Authorization: `Bearer ${token}` }),
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (response.status === 204) return undefined as T;
  if (response.ok) return response.json() as Promise<T>;
  throw await toApiError(response);
}

export async function apiUpload<T>(path: string, file: File, token: string, method = 'POST'): Promise<T> {
  const response = await send(path, {
    method,
    headers: { 'Content-Type': 'application/octet-stream', Authorization: `Bearer ${token}` },
    body: file,
  });
  if (response.ok) return response.json() as Promise<T>;
  throw await toApiError(response);
}

export async function apiBlob(path: string, token: string): Promise<Blob> {
  const response = await send(path, { headers: { Authorization: `Bearer ${token}` } });
  if (response.ok) return response.blob();
  throw await toApiError(response);
}
