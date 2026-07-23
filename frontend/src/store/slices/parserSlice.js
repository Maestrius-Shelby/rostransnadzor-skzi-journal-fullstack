import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import {
  getParserStatus,
  startParser as startParserApi,
  stopParser as stopParserApi,
  getRecords,
  exportData as exportDataApi,
} from "../../api/apiServices";

// В Redux Toolkit НЕТ разделения на reducers/, actions/, selectors/. Всё объединяется в один slice:

// ============================================
// THUNKS (асинхронные действия)
// ============================================

export const fetchStatus = createAsyncThunk(
  "parser/fetchStatus",
  async (_, { rejectWithValue }) => {
    try {
      return await getParserStatus();
    } catch (error) {
      return rejectWithValue(error.message || "Ошибка получения статуса");
    }
  },
);

export const startParser = createAsyncThunk(
  "parser/start",
  async ({ config = {}, mock = false }, { rejectWithValue }) => {
    try {
      return await startParserApi(config, mock);
    } catch (error) {
      return rejectWithValue(error.message || "Ошибка запуска");
    }
  },
);

export const stopParser = createAsyncThunk(
  "parser/stop",
  async (force = false, { rejectWithValue }) => {
    try {
      return await stopParserApi(force);
    } catch (error) {
      return rejectWithValue(error.message || "Ошибка остановки");
    }
  },
);

export const fetchRecords = createAsyncThunk(
  "parser/fetchRecords",
  async ({ limit = 100, offset = 0 }, { rejectWithValue }) => {
    try {
      return await getRecords(limit, offset);
    } catch (error) {
      return rejectWithValue(error.message || "Ошибка получения записей");
    }
  },
);

export const exportData = createAsyncThunk(
  "parser/exportData",
  async ({ format }, { rejectWithValue }) => {
    try {
      const data = await exportDataApi(format);

      // Проверяем, не заблокирован ли файл
      if (data && data.file_locked) {
        return {
          ...data,
          file_locked: true,
          message:
            data.message ||
            "Файл открыт в Excel. Закройте файл и повторите экспорт.",
        };
      }

      return data;
    } catch (error) {
      return rejectWithValue(error);
    }
  },
);

// ============================================
// SLICE (редьюсер + синхронные actions)
// ============================================

const initialState = {
  status: "idle",
  progress: 0,
  totalRecords: 0,
  currentRecord: 0,
  message: null,
  records: [],
  isRunning: false,
  error: null,
  loading: false,
  exportData: null,
  lastUpdated: null,
};

const parserSlice = createSlice({
  name: "parser",
  initialState,

  // Синхронные редьюсеры (для WebSocket и ручного обновления)
  reducers: {
    setStatus: (state, action) => {
      state.status = action.payload;
      state.isRunning = action.payload === "running";
    },
    setProgress: (state, action) => {
      state.progress = action.payload;
    },
    setRecords: (state, action) => {
      state.records = action.payload;
      state.totalRecords = action.payload.length;
      state.lastUpdated = new Date().toISOString();
    },
    setTotalRecords: (state, action) => {
      state.totalRecords = action.payload;
    },

    // ============================================
    // ОСНОВНОЙ - ОБНОВЛЕНИЕ ИЗ WEBSOCKET
    // ============================================
    updateFromWebSocket: (state, action) => {
      const {
        status,
        progress,
        total_records,
        current_record,
        message,
        records: newRecords,
        is_running,
      } = action.payload;

      // Обновляем статус
      if (status) {
        state.status = status;
        state.isRunning = status === "running";
      }
      if (is_running !== undefined) {
        state.isRunning = is_running;
      }

      // Обновляем прогресс
      if (progress !== undefined) {
        state.progress = progress;
      }

      // Обновляем количество записей
      if (total_records !== undefined) {
        state.totalRecords = total_records;
      }

      // Обновляем текущую запись
      if (current_record !== undefined) {
        state.currentRecord = current_record;
      }

      // Обновляем сообщение
      if (message) {
        state.message = message;
      }

      // ============================================
      // ВАЖНО: ОБНОВЛЯЕМ ЗАПИСИ
      // ============================================
      if (newRecords && Array.isArray(newRecords) && newRecords.length > 0) {
        // Полностью заменяем записи на новые из WebSocket
        state.records = newRecords;
        state.totalRecords = newRecords.length;
        state.lastUpdated = new Date().toISOString();
      }

      // Если статус завершен или ошибка - снимаем флаг running
      if (
        status === "completed" ||
        status === "error" ||
        status === "stopped"
      ) {
        state.isRunning = false;
      }

      // Обновляем время
      state.lastUpdated = new Date().toISOString();
    },

    // ============================================
    // ДОБАВЛЕНИЕ НОВЫХ ЗАПИСЕЙ
    // ============================================
    addRecords: (state, action) => {
      const newRecords = action.payload;
      if (Array.isArray(newRecords) && newRecords.length > 0) {
        const existingKeys = new Set(
          state.records.map(
            (r) => `${r.fio}|${r.serial_number}|${r.date_from}`,
          ),
        );

        const uniqueNewRecords = newRecords.filter((r) => {
          const key = `${r.fio}|${r.serial_number}|${r.date_from}`;
          return !existingKeys.has(key);
        });

        if (uniqueNewRecords.length > 0) {
          state.records = [...state.records, ...uniqueNewRecords];
          state.totalRecords = state.records.length;
          state.lastUpdated = new Date().toISOString();
        }
      }
    },

    // ============================================
    // ОБНОВЛЕНИЕ ПРОГРЕССА
    // ============================================
    updateProgress: (state, action) => {
      const { progress, current, total, message } = action.payload;
      if (progress !== undefined) state.progress = progress;
      if (current !== undefined) state.currentRecord = current;
      if (total !== undefined) state.totalRecords = total;
      if (message !== undefined) state.message = message;
      state.lastUpdated = new Date().toISOString();
    },

    clearError: (state) => {
      state.error = null;
    },
    reset: () => initialState,

    // ============================================
    // ОБНОВЛЕНИЕ СТАТУСА (простой)
    // ============================================
    updateStatus: (state, action) => {
      const data = action.payload;
      if (data.status) {
        state.status = data.status;
        state.isRunning = data.status === "running";
      }
      if (data.progress !== undefined) {
        state.progress = data.progress;
      }
      if (data.message) {
        state.message = data.message;
      }
      if (data.total_records !== undefined) {
        state.totalRecords = data.total_records;
      }
      state.lastUpdated = new Date().toISOString();
    },
  },

  // Асинхронные редьюсеры (для thunks)
  extraReducers: (builder) => {
    builder
      // fetchStatus
      .addCase(fetchStatus.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchStatus.fulfilled, (state, action) => {
        state.loading = false;
        const data = action.payload;
        state.status = data.status || "idle";
        state.progress = data.progress || 0;
        state.totalRecords = data.total_records || data.totalRecords || 0;
        state.currentRecord = data.current_record || data.currentRecord || 0;
        state.message = data.message || null;
        state.isRunning = data.is_running || data.isRunning || false;
        state.error = null;
        state.lastUpdated = new Date().toISOString();
      })
      .addCase(fetchStatus.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || "Ошибка получения статуса";
      })

      // startParser
      .addCase(startParser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(startParser.fulfilled, (state) => {
        state.loading = false;
        state.status = "running";
        state.isRunning = true;
        state.message = "Запуск...";
        state.error = null;
        state.lastUpdated = new Date().toISOString();
      })
      .addCase(startParser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || "Ошибка запуска";
      })

      // stopParser
      .addCase(stopParser.pending, (state) => {
        state.loading = true;
      })
      .addCase(stopParser.fulfilled, (state) => {
        state.loading = false;
        state.status = "stopped";
        state.isRunning = false;
        state.message = "Остановлен";
        state.error = null;
        state.lastUpdated = new Date().toISOString();
      })
      .addCase(stopParser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || "Ошибка остановки";
      })

      // fetchRecords
      .addCase(fetchRecords.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchRecords.fulfilled, (state, action) => {
        state.loading = false;
        const records = action.payload || [];
        state.records = records;
        state.totalRecords = records.length;
        state.error = null;
        state.lastUpdated = new Date().toISOString();
      })
      .addCase(fetchRecords.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || "Ошибка получения записей";
      })

      // exportData
      .addCase(exportData.pending, (state) => {
        state.loading = true;
      })
      .addCase(exportData.fulfilled, (state, action) => {
        state.loading = false;
        state.exportData = action.payload;
        state.error = null;
      })
      .addCase(exportData.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || "Ошибка экспорта";
      });
  },
});

// ============================================
// ACTIONS (синхронные)
// ============================================

export const {
  setStatus,
  setProgress,
  setRecords,
  setTotalRecords,
  updateFromWebSocket,
  addRecords,
  updateProgress,
  updateStatus,
  clearError,
  reset,
} = parserSlice.actions;

// ============================================
// SELECTORS (мемоизированные через Reselect)
// ============================================

import { createSelector } from "reselect";

// Базовые селекторы
export const selectParserState = (state) => state.parser;

export const selectStatus = createSelector(
  selectParserState,
  (parser) => parser.status,
);

export const selectIsRunning = createSelector(
  selectParserState,
  (parser) => parser.isRunning,
);

export const selectProgress = createSelector(
  selectParserState,
  (parser) => parser.progress,
);

export const selectRecords = createSelector(
  selectParserState,
  (parser) => parser.records,
);

export const selectTotalRecords = createSelector(
  selectParserState,
  (parser) => parser.totalRecords,
);

export const selectCurrentRecord = createSelector(
  selectParserState,
  (parser) => parser.currentRecord,
);

export const selectMessage = createSelector(
  selectParserState,
  (parser) => parser.message,
);

export const selectError = createSelector(
  selectParserState,
  (parser) => parser.error,
);

export const selectLoading = createSelector(
  selectParserState,
  (parser) => parser.loading,
);

export const selectLastUpdated = createSelector(
  selectParserState,
  (parser) => parser.lastUpdated,
);

// ============================================
// ДОБАВЛЕННЫЕ СЕЛЕКТОРЫ
// ============================================

// Новые записи
export const selectNewRecords = createSelector(selectRecords, (records) =>
  records.filter((r) => r.is_new === true),
);

export const selectNewRecordsCount = createSelector(
  selectNewRecords,
  (records) => records.length,
);

// Истекающие записи
export const selectExpiringRecords = createSelector(selectRecords, (records) =>
  records.filter((r) => r.is_expiring === true),
);

export const selectExpiringRecordsCount = createSelector(
  selectExpiringRecords,
  (records) => records.length,
);

// Истекшие записи
export const selectExpiredRecords = createSelector(selectRecords, (records) =>
  records.filter((r) => r.is_expired === true),
);

export const selectExpiredRecordsCount = createSelector(
  selectExpiredRecords,
  (records) => records.length,
);

// Составные селекторы
export const selectRecordsWithIds = createSelector(selectRecords, (records) =>
  records.map((record, index) => ({
    ...record,
    id: index + 1,
  })),
);

export const selectRecordsCount = createSelector(
  selectRecords,
  (records) => records.length,
);

export const selectLastRecords = createSelector(
  selectRecords,
  (records, limit = 10) => records.slice(0, limit),
);

// Статистика
export const selectStats = createSelector(selectRecords, (records) => ({
  total: records.length,
  uniqueUsers: new Set(records.map((r) => r.fio)).size,
  activeKeys: records.filter((r) => r.serial_number).length,
  newRecords: records.filter((r) => r.is_new).length,
  expiringRecords: records.filter((r) => r.is_expiring).length,
  expiredRecords: records.filter((r) => r.is_expired).length,
}));

// ============================================
// REDUCER (экспорт по умолчанию)
// ============================================

export default parserSlice.reducer;
