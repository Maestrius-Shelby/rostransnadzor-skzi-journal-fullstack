import { configureStore } from "@reduxjs/toolkit";
import parserReducer from "./slices/parserSlice";
import settingsReducer from "./slices/settingsSlice";
import authReducer from "./slices/authSlice";

export const store = configureStore({
  reducer: {
    parser: parserReducer,
    settings: settingsReducer,
    auth: authReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ["parser/updateFromWebSocket"],
      },
    }),
  // Node.js (CRA, Next.js)
  // devTools: process.env.NODE_ENV !== "production",
  devTools: import.meta.env.MODE !== "production",
});

// Экспорт всех селекторов из parserSlice для удобства
export * from "./slices/parserSlice";
export * from "./slices/settingsSlice";

export default store;
