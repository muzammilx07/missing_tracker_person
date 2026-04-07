import axios from "axios";
import { clearAuth, getToken } from "@/lib/auth";

const baseURL =
  process.env.NEXT_PUBLIC_API_URL ||
  "https://missing-tracker-person.onrender.com";

const api = axios.create({
  baseURL,
});

api.interceptors.request.use(
  (config) => {
    if (typeof window !== "undefined") {
      const token = getToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401 && typeof window !== "undefined") {
      clearAuth();
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default api;
