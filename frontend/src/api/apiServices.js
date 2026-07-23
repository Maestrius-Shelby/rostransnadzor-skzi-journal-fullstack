import axiosInstance from "./axiosInstance";

/**
 * Универсальный GET запрос
 */
export const getData = async (endpoint, params = {}) => {
  try {
    const response = await axiosInstance.get(endpoint, { params });
    return response.data;
  } catch (error) {
    console.error(`Error fetching ${endpoint}:`, error);
    throw error.response?.data || error.message || "Ошибка подключения";
  }
};

/**
 * Универсальный POST запрос
 */
export const postData = async (endpoint, data = {}) => {
  try {
    const response = await axiosInstance.post(endpoint, data);
    return response.data;
  } catch (error) {
    console.error(`Error posting to ${endpoint}:`, error);
    throw error.response?.data || error.message || "Ошибка подключения";
  }
};

/**
 * Универсальный PUT запрос
 */
export const putData = async (endpoint, data = {}) => {
  try {
    const response = await axiosInstance.put(endpoint, data);
    return response.data;
  } catch (error) {
    console.error(`Error putting to ${endpoint}:`, error);
    throw error.response?.data || error.message || "Ошибка подключения";
  }
};

/**
 * Универсальный DELETE запрос
 */
export const deleteData = async (endpoint) => {
  try {
    const response = await axiosInstance.delete(endpoint);
    return response.data;
  } catch (error) {
    console.error(`Error deleting ${endpoint}:`, error);
    throw error.response?.data || error.message || "Ошибка подключения";
  }
};

// ============================================
// НАСТРОЙКИ
// ============================================

export const saveSettings = async (settings) => {
  try {
    const response = await axiosInstance.post("/settings", settings);
    return response.data;
  } catch (error) {
    console.error("Error saving settings:", error);
    throw error;
  }
};

export const getSettings = async () => {
  try {
    const response = await axiosInstance.get("/settings");
    return response.data;
  } catch (error) {
    console.error("Error getting settings:", error);
    throw error;
  }
};

// ============================================
// ИСТОРИЯ
// ============================================

export const getHistory = async (limit = 50, offset = 0) => {
  try {
    const response = await axiosInstance.get(
      `/history?limit=${limit}&offset=${offset}`,
    );
    return response.data;
  } catch (error) {
    console.error("Error getting history:", error);
    throw error;
  }
};

export const addHistoryEntry = async (entry) => {
  try {
    const response = await axiosInstance.post("/history", entry);
    return response.data;
  } catch (error) {
    console.error("Error adding history entry:", error);
    throw error;
  }
};

export const clearHistory = async () => {
  try {
    const response = await axiosInstance.delete("/history");
    return response.data;
  } catch (error) {
    console.error("Error clearing history:", error);
    throw error;
  }
};

export const deleteHistoryEntry = async (entryId) => {
  try {
    const response = await axiosInstance.delete(`/history/${entryId}`);
    return response.data;
  } catch (error) {
    console.error("Error deleting history entry:", error);
    throw error;
  }
};

// ============================================
// ИМПОРТ EXCEL
// ============================================

/**
 * Импорт пользовательских полей из Excel файла
 * @param {File} file - Файл Excel
 */
export const importExcel = async (file) => {
  try {
    const formData = new FormData();
    formData.append("file", file);

    const response = await axiosInstance.post(
      "/records/import-excel",
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      },
    );
    return response.data;
  } catch (error) {
    console.error("Error importing Excel:", error);
    throw error.response?.data || error.message || "Ошибка импорта";
  }
};

// ============================================
// ВОТЧЕР
// ============================================

/**
 * Получить статус вотчера
 */
export const getWatcherStatus = () => {
  return getData("/watcher/status");
};

// ============================================
// СПЕЦИФИЧНЫЕ МЕТОДЫ ДЛЯ ПАРСЕРА
// ============================================

/**
 * Получить статус парсера
 */
export const getParserStatus = () => {
  return getData("/status");
};

/**
 * Запустить парсер (с поддержкой режима имитации)
 * @param {Object} config - Конфигурация парсинга
 * @param {boolean} mock - Режим имитации (true = без браузера)
 */
export const startParser = (config, mock = false) => {
  const data = { config: { ...config, mock } };
  return postData("/start", data);
};

/**
 * Остановить парсер
 */
export const stopParser = (force = false) => {
  return postData("/stop", { force });
};

/**
 * Получить записи
 */
export const getRecords = (limit = 100, offset = 0) => {
  return getData("/records", { limit, offset });
};

/**
 * Получить количество записей
 */
export const getRecordsCount = () => {
  return getData("/records/count");
};

/**
 * Экспорт данных
 */
export const exportData = async (format = "excel") => {
  try {
    const response = await axiosInstance.post("/export", { format });
    return response.data;
  } catch (error) {
    console.error("Error exporting data:", error);
    throw error.response?.data || error.message || "Ошибка экспорта";
  }
};

// ============================================
// АВТОРИЗАЦИЯ
// ============================================

export const loginRequest = async (username, password) => {
  return postData("/auth/login", { username, password });
};

export const refreshTokenRequest = async (refresh) => {
  return postData("/auth/refresh", { refresh });
};

export const logoutRequest = async () => {
  return postData("/auth/logout");
};
