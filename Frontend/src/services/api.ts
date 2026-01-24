import axios, { AxiosError } from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1",
  withCredentials: false,
});

// ---- request interceptor (optional logging) ----
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  console.debug("[REQ]", config.method?.toUpperCase(), config.url);
  return config;
});

// ---- response / error handler ----
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response) {
      console.error("[API ERROR]", error.response.status, error.response.data);
      
      // Handle Rate Limit (429)
      if (error.response.status === 429) {
        window.dispatchEvent(
          new CustomEvent('SHOW_SNACKBAR', { 
            detail: { message: "Slow down! You've hit the rate limit. Please wait a moment.", severity: 'warning' } 
          })
        );
      }
      // Handle Unauthorized (401) or Forbidden (403)
      else if (error.response.status === 401 || error.response.status === 403) {
        localStorage.removeItem("access_token");
        window.dispatchEvent(
          new CustomEvent('SHOW_SNACKBAR', { 
            detail: { message: "Session expired or unauthorized. Please log in again.", severity: 'error' } 
          })
        );
      }
      // Handle Server Errors (5xx)
      else if (error.response.status >= 500) {
        window.dispatchEvent(
          new CustomEvent('SHOW_SNACKBAR', { 
            detail: { message: "Server error occurred. Please try again later.", severity: 'error' } 
          })
        );
      }
    } else if (error.request) {
      console.error("[NETWORK ERROR]", error.message);
      window.dispatchEvent(
        new CustomEvent('SHOW_SNACKBAR', { 
          detail: { message: "Network error. Please check your connection.", severity: 'error' } 
        })
      );
    } else {
      console.error("[CLIENT ERROR]", error.message);
    }

    return Promise.reject(error);
  }
);

type Method = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

export async function apiRequest<T = unknown>(
  method: Method,
  url: string,
  payload?: unknown
): Promise<T> {
  const res = await api({
    method,
    url,
    data: payload ?? undefined,
  });

  return res.data as T;
}



export default api;
