import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";

// ============================================
// THUNK - ОТПРАВКА НАСТРОЕК НА БЭКЕНД
// ============================================
export const saveSettingsToBackend = createAsyncThunk(
  "settings/saveToBackend",
  async (settings, { rejectWithValue }) => {
    try {
      const response = await fetch("/api/settings", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          auto_parse: settings.autoParse,
          auto_parse_time: settings.autoParseTime,
          days_back: settings.daysBack,
          headless: settings.headless,
          export_path: settings.exportPath,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Ошибка сохранения настроек");
      }

      return await response.json();
    } catch (error) {
      return rejectWithValue(error.message);
    }
  },
);

// Загружаем настройки из localStorage
const loadSettings = () => {
  try {
    const saved = localStorage.getItem("parserSettings");
    if (saved) {
      return JSON.parse(saved);
    }
  } catch (e) {
    console.error("Ошибка загрузки настроек:", e);
  }
  return null;
};

const defaultSettings = {
  daysBack: 15,
  maxRecords: 999999,
  headless: false,
  confidenceThreshold: 0.5,
  recognitionTimeout: 10,
  outputFormat: "excel",
  autoParse: true,
  autoParseTime: "09:00",
  exportPath: "./output",
  isSaving: false,
};

const initialState = loadSettings() || defaultSettings;

const settingsSlice = createSlice({
  name: "settings",
  initialState,
  reducers: {
    updateSettings: (state, action) => {
      const newState = { ...state, ...action.payload };
      // Сохраняем в localStorage
      try {
        localStorage.setItem("parserSettings", JSON.stringify(newState));
      } catch (e) {
        console.error("Ошибка сохранения настроек:", e);
      }
      return newState;
    },
    resetSettings: () => {
      try {
        localStorage.removeItem("parserSettings");
      } catch (e) {
        console.error("Ошибка удаления настроек:", e);
      }
      return defaultSettings;
    },
    setSettingsSaving: (state, action) => {
      state.isSaving = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(saveSettingsToBackend.pending, (state) => {
        state.isSaving = true;
      })
      .addCase(saveSettingsToBackend.fulfilled, (state) => {
        state.isSaving = false;
      })
      .addCase(saveSettingsToBackend.rejected, (state) => {
        state.isSaving = false;
      });
  },
});

export const { updateSettings, resetSettings, setSettingsSaving } =
  settingsSlice.actions;

// Селекторы
export const selectSettings = (state) => state.settings;
export const selectDaysBack = (state) => state.settings.daysBack;
export const selectHeadless = (state) => state.settings.headless;
export const selectAutoParse = (state) => state.settings.autoParse;
export const selectAutoParseTime = (state) => state.settings.autoParseTime;
export const selectExportPath = (state) => state.settings.exportPath;
export const selectSettingsSaving = (state) => state.settings.isSaving;

export default settingsSlice.reducer;
