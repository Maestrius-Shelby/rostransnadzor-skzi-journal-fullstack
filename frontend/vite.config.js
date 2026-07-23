import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import { fileURLToPath } from "url";

// Создаем __dirname для ES модулей
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default defineConfig({
  plugins: [react()],

  // ============================================
  // АЛИАСЫ ПУТЕЙ (Resolve Aliases)
  // ============================================
  resolve: {
    alias: {
      // Позволяет использовать @ вместо полного пути к src/
      // Пример: @/components/Button вместо src/components/Button
      "@": path.resolve(__dirname, "./src"),
    },
  },

  // ============================================
  // НАСТРОЙКА CSS / SCSS
  // ============================================
  css: {
    // Настройка CSS Modules
    modules: {
      // Преобразует имена классов в camelCase
      // Пример: .my-class → myClass
      localsConvention: "camelCase",
    },

    // Настройка препроцессоров
    preprocessorOptions: {
      scss: {
        // ВАЖНО: @use вместо @import (современный синтаксис Sass)
        // @use подключает переменные, миксины и функции из файла
        // as * - делает все переменные доступными без префикса
        //
        // ПРАВИЛЬНО: @use "@/styles/variables.scss" as *;
        // НЕПРАВИЛЬНО: @import "./src/styles/variables.scss";
        //
        // ВСЕ переменные из variables.scss доступными ВЕЗДЕ,
        // без необходимости импортировать их в каждом файле.
        additionalData: `@use "@/styles/variables.scss" as *;`,
      },
    },
  },

  // ============================================
  // НАСТРОЙКА DEV СЕРВЕРА
  // ============================================
  server: {
    // Порт для разработки
    port: 5173,

    // Прокси для API запросов
    // Все запросы на /api/... перенаправляются на бэкенд
    proxy: {
      "/api": {
        target: "http://localhost:8000", // Бэкенд на порту 8000
        changeOrigin: true, // Изменяет Origin заголовок
      },
      "/ws": {
        target: "ws://localhost:8000", // WebSocket для реального времени
        ws: true, // Включает WebSocket прокси
      },
    },
  },
});
