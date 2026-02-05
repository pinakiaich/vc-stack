/**
 * API Client Configuration
 * Base client for all API calls
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
    public details?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined>;
}

function isNetworkError(e: unknown): boolean {
  if (!(e instanceof Error)) return false;
  const m = e.message.toLowerCase();
  return (
    m === 'failed to fetch' ||
    m === 'load failed' ||
    m.includes('network request failed') ||
    m.includes('networkerror')
  );
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
    let errorDetails: Record<string, unknown> | undefined;

    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
      errorDetails = errorData;
    } catch {
      /* response body not JSON */
    }

    throw new ApiError(errorMessage, response.status, undefined, errorDetails);
  }

  return response.json();
}

function buildUrl(endpoint: string, params?: Record<string, string | number | boolean | undefined>): string {
  const url = new URL(endpoint, API_BASE_URL);

  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        url.searchParams.append(key, String(value));
      }
    });
  }

  return url.toString();
}

const CONNECTION_MSG = `Cannot connect to API at ${API_BASE_URL}. Start the backend (e.g. \`cd backend && uvicorn app.main:app --reload --port 8000\`) and refresh.`;

async function request<T>(url: string, init: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(url, init);
  } catch (e) {
    if (isNetworkError(e)) {
      throw new ApiError(CONNECTION_MSG, 0, 'NETWORK_ERROR', { cause: e });
    }
    throw e;
  }
  return handleResponse<T>(response);
}

export const apiClient = {
  /**
   * GET request
   */
  async get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    const { params, ...fetchOptions } = options || {};
    const url = buildUrl(endpoint, params);
    return request<T>(url, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json', ...fetchOptions.headers },
      ...fetchOptions,
    });
  },

  /**
   * POST request with JSON body
   */
  async post<T>(endpoint: string, data?: unknown, options?: RequestOptions): Promise<T> {
    const { params, ...fetchOptions } = options || {};
    const url = buildUrl(endpoint, params);
    return request<T>(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...fetchOptions.headers },
      body: data ? JSON.stringify(data) : undefined,
      ...fetchOptions,
    });
  },

  /**
   * POST request with FormData (for file uploads)
   */
  async postForm<T>(endpoint: string, formData: FormData, options?: RequestOptions): Promise<T> {
    const { params, ...fetchOptions } = options || {};
    const url = buildUrl(endpoint, params);
    return request<T>(url, {
      method: 'POST',
      ...fetchOptions,
      body: formData,
    });
  },

  /**
   * PUT request
   */
  async put<T>(endpoint: string, data?: unknown, options?: RequestOptions): Promise<T> {
    const { params, ...fetchOptions } = options || {};
    const url = buildUrl(endpoint, params);
    return request<T>(url, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...fetchOptions.headers },
      body: data ? JSON.stringify(data) : undefined,
      ...fetchOptions,
    });
  },

  /**
   * DELETE request
   */
  async delete<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    const { params, ...fetchOptions } = options || {};
    const url = buildUrl(endpoint, params);
    return request<T>(url, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json', ...fetchOptions.headers },
      ...fetchOptions,
    });
  },

  /**
   * Health check
   */
  async healthCheck(): Promise<{ status: string }> {
    return this.get<{ status: string }>('/health');
  },
};

export default apiClient;
