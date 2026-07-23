import axios from "axios";

// Базовый URL для API
const API_BASE_URL = import.meta.env.VITE_API_URL;

// Создаем экземпляр axios
const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 300000, // 300 секунд
  // withCredentials: true,
});

// Перехватчик запросов
axiosInstance.interceptors.request.use(
  (config) => {
    console.log(`📤 [${config.method?.toUpperCase()}] ${config.url}`);
    return config;
  },
  (error) => {
    console.error("❌ Request error:", error);
    return Promise.reject(error);
  },
);

// Перехватчик ответов
axiosInstance.interceptors.response.use(
  (response) => {
    console.log(`📥 [${response.status}] ${response.config.url}`);
    return response;
  },
  (error) => {
    if (error.response) {
      // Сервер ответил с ошибкой
      console.error("❌ Server error:", {
        status: error.response.status,
        data: error.response.data,
        url: error.config?.url,
      });
    } else if (error.request) {
      // Запрос был отправлен, но ответа нет
      console.error("❌ No response:", error.request);
    } else {
      // Ошибка при настройке запроса
      console.error("❌ Request setup error:", error.message);
    }
    return Promise.reject(error);
  },
);

export default axiosInstance;
