import { useEffect, useCallback, useState, useRef } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  fetchStatus,
  fetchRecords,
  startParser,
  stopParser,
  exportData,
  clearError,
  updateFromWebSocket,
  selectStatus,
  selectIsRunning,
  selectProgress,
  selectRecords,
  selectTotalRecords,
  selectCurrentRecord,
  selectMessage,
  selectError,
  selectLoading,
} from "../store/slices/parserSlice";

export const useParser = () => {
  const dispatch = useDispatch();
  const [wsStatus, setWsStatus] = useState("disconnected");
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 10;
  const isMountedRef = useRef(true);
  const isConnectingRef = useRef(false);

  const status = useSelector(selectStatus);
  const isRunning = useSelector(selectIsRunning);
  const progress = useSelector(selectProgress);
  const records = useSelector(selectRecords);
  const totalRecords = useSelector(selectTotalRecords);
  const currentRecord = useSelector(selectCurrentRecord);
  const message = useSelector(selectMessage);
  const error = useSelector(selectError);
  const loading = useSelector(selectLoading);

  // ============================================
  // МЕТОДЫ
  // ============================================

  const loadStatus = useCallback(() => {
    dispatch(fetchStatus());
  }, [dispatch]);

  const loadRecords = useCallback(
    (limit = 100, offset = 0) => {
      dispatch(fetchRecords({ limit, offset }));
    },
    [dispatch],
  );

  const start = useCallback(
    (config) => {
      return dispatch(startParser({ config })).unwrap();
    },
    [dispatch],
  );

  const stop = useCallback(
    (force = false) => {
      return dispatch(stopParser(force)).unwrap();
    },
    [dispatch],
  );

  const exportRecords = useCallback(
    (format = "excel") => {
      return dispatch(exportData({ format })).unwrap();
    },
    [dispatch],
  );

  const clearErrorHandler = useCallback(() => {
    dispatch(clearError());
  }, [dispatch]);

  // ============================================
  // ОЧИСТКА И УДАЛЕНИЕ
  // ============================================
  const clearAllRecords = useCallback(async () => {
    try {
      const response = await fetch("/api/records/clear", { method: "DELETE" });
      if (!response.ok) throw new Error("Ошибка при очистке записей");
      const data = await response.json();
      dispatch({ type: "parser/setRecords", payload: [] });
      dispatch({ type: "parser/setTotalRecords", payload: 0 });
      dispatch({ type: "parser/setProgress", payload: 0 });
      dispatch({ type: "parser/setStatus", payload: "idle" });
      return data;
    } catch (error) {
      console.error("❌ Ошибка очистки записей:", error);
      throw error;
    }
  }, [dispatch]);

  const deleteRecords = useCallback(
    async (ids) => {
      try {
        const response = await fetch("/api/records/delete", {
          method: "DELETE",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ids }),
        });
        if (!response.ok) throw new Error("Ошибка при удалении записей");
        const data = await response.json();
        dispatch({ type: "parser/setRecords", payload: data.records });
        dispatch({ type: "parser/setTotalRecords", payload: data.count });
        return data;
      } catch (error) {
        console.error("❌ Ошибка удаления записей:", error);
        throw error;
      }
    },
    [dispatch],
  );

  // ============================================
  // WEBSOCKET
  // ============================================
  useEffect(() => {
    isMountedRef.current = true;

    const checkBackend = async () => {
      try {
        const response = await fetch("http://localhost:8000/health");
        return response.ok;
      } catch {
        return false;
      }
    };

    const connectWebSocket = async () => {
      if (isConnectingRef.current || !isMountedRef.current) return;

      const isBackendAvailable = await checkBackend();
      if (!isBackendAvailable) {
        setIsConnected(false);
        setWsStatus("disconnected");
        reconnectTimerRef.current = setTimeout(connectWebSocket, 3000);
        return;
      }

      if (wsRef.current) {
        try {
          wsRef.current.close();
        } catch {
          // Нет необходимости обрабатывать ошибку закрытия
        }
        wsRef.current = null;
      }

      isConnectingRef.current = true;

      try {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const host = window.location.hostname || "localhost";
        const wsUrl = `${protocol}//${host}:8000/api/ws`;

        const wsInstance = new WebSocket(wsUrl);
        wsRef.current = wsInstance;

        const connectionTimeout = setTimeout(() => {
          if (wsInstance.readyState !== WebSocket.OPEN) {
            wsInstance.close();
            isConnectingRef.current = false;
            setIsConnected(false);
            setWsStatus("disconnected");
            if (reconnectAttemptsRef.current < maxReconnectAttempts) {
              const delay = Math.min(
                1000 * Math.pow(1.5, reconnectAttemptsRef.current),
                30000,
              );
              reconnectAttemptsRef.current++;
              reconnectTimerRef.current = setTimeout(connectWebSocket, delay);
            }
          }
        }, 10000);

        wsInstance.onopen = () => {
          clearTimeout(connectionTimeout);
          if (!isMountedRef.current) {
            isConnectingRef.current = false;
            return;
          }
          console.log("✅ WebSocket подключен");
          setIsConnected(true);
          setWsStatus("connected");
          reconnectAttemptsRef.current = 0;
          isConnectingRef.current = false;
          loadRecords(1000);
          loadStatus();
        };

        wsInstance.onmessage = (event) => {
          if (!isMountedRef.current) return;
          try {
            const data = JSON.parse(event.data);
            dispatch(updateFromWebSocket(data));

            if (data.type === "excel_updated") {
              console.log("🔄 Excel обновлен, перезагружаем данные...");
              loadRecords(1000);
              loadStatus();
            }

            if (data.records && Array.isArray(data.records)) {
              dispatch({ type: "parser/setRecords", payload: data.records });
            }
          } catch (e) {
            console.error("❌ Ошибка парсинга WebSocket:", e);
          }
        };

        wsInstance.onclose = (event) => {
          clearTimeout(connectionTimeout);
          isConnectingRef.current = false;
          if (!isMountedRef.current) return;

          console.log(`🔌 WebSocket отключен (код: ${event.code})`);
          setIsConnected(false);
          setWsStatus("disconnected");

          if (event.code === 1000 || event.code === 1001) {
            console.log("👋 WebSocket закрыт штатно");
            return;
          }

          if (reconnectAttemptsRef.current < maxReconnectAttempts) {
            const delay = Math.min(
              1000 * Math.pow(1.5, reconnectAttemptsRef.current),
              30000,
            );
            reconnectAttemptsRef.current++;
            console.log(
              `🔄 Переподключение через ${delay}мс (попытка ${reconnectAttemptsRef.current}/${maxReconnectAttempts})`,
            );
            reconnectTimerRef.current = setTimeout(connectWebSocket, delay);
          } else {
            console.log("❌ Достигнут лимит попыток переподключения");
          }
        };

        wsInstance.onerror = (error) => {
          console.error("❌ WebSocket ошибка:", error);
        };
      } catch (e) {
        console.error("❌ Ошибка подключения WebSocket:", e);
        isConnectingRef.current = false;
        setIsConnected(false);
        setWsStatus("disconnected");
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          const delay = Math.min(
            1000 * Math.pow(1.5, reconnectAttemptsRef.current),
            30000,
          );
          reconnectAttemptsRef.current++;
          reconnectTimerRef.current = setTimeout(connectWebSocket, delay);
        }
      }
    };

    const initialTimer = setTimeout(connectWebSocket, 1000);

    return () => {
      isMountedRef.current = false;
      isConnectingRef.current = false;
      if (wsRef.current) {
        try {
          wsRef.current.close(1000, "Component unmount");
        } catch {
          // Нет необходимости обрабатывать ошибку закрытия
        }
        wsRef.current = null;
      }
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      if (initialTimer) clearTimeout(initialTimer);
    };
  }, [dispatch, loadRecords, loadStatus]);

  // ============================================
  // ЗАГРУЗКА ПРИ МОНТИРОВАНИИ
  // ============================================
  useEffect(() => {
    loadRecords(1000);
    loadStatus();
  }, [loadRecords, loadStatus]);

  // ============================================
  // ОБНОВЛЕНИЕ СТАТУСА ПРИ РАБОТЕ ПАРСЕРА
  // ============================================
  useEffect(() => {
    if (!isRunning) return;
    const interval = setInterval(() => loadStatus(), 3000);
    return () => clearInterval(interval);
  }, [isRunning, loadStatus]);

  return {
    status,
    isRunning,
    progress,
    records,
    totalRecords,
    currentRecord,
    message,
    error,
    loading,
    wsStatus,
    isConnected,
    loadStatus,
    loadRecords,
    start,
    stop,
    exportRecords,
    clearError: clearErrorHandler,
    clearAllRecords,
    deleteRecords,
  };
};
