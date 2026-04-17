import axios, { type AxiosInstance } from "axios";
import { useSettingsStore } from "../store/settings";

function build(): AxiosInstance {
  const instance = axios.create({
    timeout: 10_000,
    headers: { "Content-Type": "application/json" },
  });
  instance.interceptors.request.use((config) => {
    const base = useSettingsStore.getState().backendUrl.replace(/\/+$/, "");
    config.baseURL = base;
    return config;
  });
  return instance;
}

export const apiClient = build();
