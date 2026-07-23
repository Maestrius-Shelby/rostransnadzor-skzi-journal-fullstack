import { useState, useEffect, useCallback } from "react";
import { useParser } from "../../../hooks/useParser";
import { Button, Card } from "../../ui";
import ConfirmDialog from "../../ui/ConfirmDialog/ConfirmDialog";
import {
  getHistory,
  addHistoryEntry,
  clearHistory,
} from "../../../api/apiServices";
import toast from "react-hot-toast";
import styles from "./ParserControl.module.scss";

const ParserControl = () => {
  const {
    isRunning,
    progress,
    status,
    records,
    start,
    stop,
    exportRecords,
    loading,
    message,
    error,
  } = useParser();

  const [isStarting, setIsStarting] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [history, setHistory] = useState([]);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);
  const [showClearConfirm, setShowClearConfirm] = useState(false);

  const loadHistory = useCallback(async () => {
    setIsHistoryLoading(true);
    try {
      const data = await getHistory(100);
      setHistory(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("❌ Ошибка загрузки истории:", err);
    } finally {
      setIsHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadHistory();
  }, [loadHistory]);

  const saveHistory = async (newEntry) => {
    try {
      await addHistoryEntry(newEntry);
      setHistory((prev) => [newEntry, ...prev].slice(0, 50));
    } catch (error) {
      console.error("❌ Ошибка сохранения истории:", error);
    }
  };

  const handleStart = async () => {
    if (isRunning || isStarting) return;

    setIsStarting(true);
    const startTime = Date.now();
    try {
      await start({ days_back: null, headless: true });

      const endTime = Date.now();
      const duration = Math.round((endTime - startTime) / 1000);

      await saveHistory({
        id: Date.now(),
        type: "Реальный парсинг",
        startTime: new Date(startTime).toLocaleString(),
        endTime: new Date(endTime).toLocaleString(),
        duration: duration > 0 ? `${duration}с` : "< 1с",
        status: "✅ Завершен",
        recordsCount: records.length || 0,
        files: ["Журнал_СКЗИ.xlsx", "Журнал_СКЗИ.json"],
        error: null,
      });

      toast.success("🚀 Парсинг завершен! Файлы сохранены в output/");
    } catch (err) {
      const endTime = Date.now();
      const duration = Math.round((endTime - startTime) / 1000);

      await saveHistory({
        id: Date.now(),
        type: "Реальный парсинг",
        startTime: new Date(startTime).toLocaleString(),
        endTime: new Date(endTime).toLocaleString(),
        duration: duration > 0 ? `${duration}с` : "< 1с",
        status: "❌ Ошибка",
        recordsCount: 0,
        files: null,
        error: err.message || "Неизвестная ошибка",
      });

      toast.error("❌ Ошибка: " + (err.message || "Неизвестная ошибка"));
    } finally {
      setIsStarting(false);
    }
  };

  const handleStop = async () => {
    if (!isRunning) return;
    try {
      await stop(false);
      toast.success("⏹️ Парсер останавливается...");
    } catch (err) {
      toast.error(
        "❌ Ошибка остановки: " + (err.message || "Неизвестная ошибка"),
      );
    }
  };

  // Функция скачивания файла
  const downloadFile = (blob, filename) => {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  };

  const handleExport = async (format) => {
    if (records.length === 0) {
      toast.error("📭 Нет данных для экспорта");
      return;
    }

    setIsExporting(true);
    const exportTime = Date.now();
    try {
      const result = await exportRecords(format);

      // Проверяем, не заблокирован ли файл
      if (result && result.file_locked) {
        toast.error(
          "⛔ " +
            (result.message ||
              "Файл открыт в Excel. Закройте файл и повторите экспорт."),
          {
            duration: 6000,
            icon: "⛔",
            style: {
              background: "#1e293b",
              color: "#f1f5f9",
              border: "1px solid #ef4444",
            },
          },
        );

        // Добавляем в историю ошибку
        await saveHistory({
          id: Date.now(),
          type: `Экспорт ${format.toUpperCase()}`,
          startTime: new Date(exportTime).toLocaleString(),
          endTime: new Date().toLocaleString(),
          duration: "< 1с",
          status: "⛔ Файл открыт",
          recordsCount: records.length,
          files: null,
          error:
            "Файл Журнал_СКЗИ.xlsx открыт в Excel. Закройте файл и повторите экспорт.",
        });

        setIsExporting(false);
        return;
      }

      // Все форматы — скачиваем через браузер (сохраняется в Загрузки)
      if (format === "excel" && result.filepath) {
        const response = await fetch(
          `/api/export/download?path=${encodeURIComponent(result.filepath)}`,
        );
        if (response.ok) {
          const blob = await response.blob();
          downloadFile(blob, `Журнал_СКЗИ.xlsx`);
        }
      }

      if (format === "json") {
        const jsonData = result.data || records;
        const blob = new Blob([JSON.stringify(jsonData, null, 2)], {
          type: "application/json;charset=utf-8",
        });
        downloadFile(blob, `Журнал_СКЗИ.json`);
      }

      if (format === "csv") {
        const data = result.data || records;
        if (data.length === 0) {
          toast.error("📭 Нет данных для экспорта");
          return;
        }

        const fieldNames = [
          "fio",
          "serial_number",
          "date_from",
          "date_to",
          "key_type",
          "days_left",
        ];
        const headers = [
          "ФИО",
          "Серийный номер",
          "Дата установки",
          "Срок действия",
          "Тип ключа",
          "Осталось дней",
        ];

        const headerRow = headers.map((h) => `"${h}"`).join(",");
        const rows = data
          .map((row) =>
            fieldNames
              .map((f) => `"${String(row[f] || "").replace(/"/g, '""')}"`)
              .join(","),
          )
          .join("\n");

        // BOM + правильный MIME-тип для Excel
        const BOM = "\uFEFF";
        const csvContent = BOM + headerRow + "\n" + rows;

        const blob = new Blob([csvContent], {
          type: "text/csv;charset=utf-8;",
        });

        downloadFile(blob, `Журнал_СКЗИ.csv`);
      }

      await saveHistory({
        id: Date.now(),
        type: `Экспорт ${format.toUpperCase()}`,
        startTime: new Date(exportTime).toLocaleString(),
        endTime: new Date().toLocaleString(),
        duration: "< 1с",
        status: "✅ Завершен",
        recordsCount: records.length,
        files: [`Журнал_СКЗИ.${format}`],
        error: null,
      });

      toast.success(`✅ Экспорт в ${format.toUpperCase()} завершен!`);
    } catch (err) {
      await saveHistory({
        id: Date.now(),
        type: `Экспорт ${format.toUpperCase()}`,
        startTime: new Date(exportTime).toLocaleString(),
        endTime: new Date().toLocaleString(),
        duration: "< 1с",
        status: "❌ Ошибка",
        recordsCount: records.length,
        files: null,
        error: err.message || "Неизвестная ошибка",
      });
      toast.error(
        "❌ Ошибка экспорта: " + (err.message || "Неизвестная ошибка"),
      );
    } finally {
      setIsExporting(false);
    }
  };

  const handleClearHistory = () => setShowClearConfirm(true);

  const confirmClearHistory = async () => {
    try {
      await clearHistory();
      setHistory([]);
      toast.success("🗑️ История очищена");
    } catch {
      setHistory([]);
      toast.success("🗑️ История очищена (локально)");
    }
    setShowClearConfirm(false);
  };

  const getStatusIcon = () => {
    switch (status) {
      case "running":
        return "🔄";
      case "completed":
        return "✅";
      case "error":
        return "❌";
      default:
        return "⏸️";
    }
  };

  const getStatusText = () => {
    switch (status) {
      case "running":
        return "Выполняется";
      case "completed":
        return "Завершен";
      case "error":
        return "Ошибка";
      default:
        return "Ожидание";
    }
  };

  return (
    <div className={styles.parserControl}>
      <ConfirmDialog
        isOpen={showClearConfirm}
        onClose={() => setShowClearConfirm(false)}
        onConfirm={confirmClearHistory}
        title="Очистка истории"
        message="Вы уверены, что хотите очистить всю историю запусков?"
        confirmText="Очистить"
        cancelText="Отмена"
        type="danger"
        isLoading={false}
      />

      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <h2>Управление парсером</h2>
        </div>
        <div className={`${styles.statusBadge} ${styles[status]}`}>
          <span className={styles.statusText}>
            <span className={styles.statusDot}></span>
            {getStatusIcon()} {getStatusText()}
          </span>
        </div>
      </div>

      {error && (
        <div className={styles.error}>
          <span className={styles.errorIcon}>⚠</span>
          <span className={styles.errorText}>{error}</span>
        </div>
      )}

      <div className={styles.content}>
        <div className={styles.actions}>
          <Button
            variant="success"
            onClick={handleStart}
            disabled={isRunning || isStarting || loading}
            size="large"
            className={styles.actionButton}
            icon="▶"
          >
            {isStarting || loading ? "Запуск..." : "Запустить парсинг"}
          </Button>

          <Button
            variant="danger"
            onClick={handleStop}
            disabled={!isRunning || loading}
            size="large"
            className={styles.actionButton}
            icon="⏹"
          >
            Остановить
          </Button>
        </div>

        {isRunning && (
          <div className={styles.progressSection}>
            <div className={styles.progressHeader}>
              <span className={styles.progressLabel}>Выполняется</span>
              <span className={styles.progressPercent}>
                {Math.round(progress)}%
              </span>
            </div>
            <div className={styles.progressBar}>
              <div
                className={styles.progressFill}
                style={{ width: `${Math.round(progress)}%` }}
              >
                <div className={styles.progressGlow}></div>
              </div>
            </div>
            <div className={styles.progressMessage}>
              <span>{message || "Обработка данных..."}</span>
            </div>
          </div>
        )}

        <Card className={styles.exportCard}>
          <div className={styles.cardHeader}>
            <h3 className={styles.cardTitle}>Экспорт данных</h3>
            <span className={styles.recordCount}>
              {records.length > 0
                ? `📊 ${records.length} записей`
                : "📭 Нет данных"}
            </span>
          </div>
          <div className={styles.exportButtons}>
            <Button
              variant="outline"
              onClick={() => handleExport("excel")}
              disabled={records.length === 0 || isExporting}
              className={`${styles.exportBtn} ${styles.excel}`}
              icon="📊"
            >
              Excel
            </Button>
            <Button
              variant="outline"
              onClick={() => handleExport("json")}
              disabled={records.length === 0 || isExporting}
              className={`${styles.exportBtn} ${styles.json}`}
              icon="📄"
            >
              JSON
            </Button>
            <Button
              variant="outline"
              onClick={() => handleExport("csv")}
              disabled={records.length === 0 || isExporting}
              className={`${styles.exportBtn} ${styles.csv}`}
              icon="📋"
            >
              CSV
            </Button>
          </div>
        </Card>

        <Card className={styles.historyCard}>
          <div className={styles.cardHeader}>
            <h3 className={styles.cardTitle}>📋 История запусков</h3>
            <div className={styles.historyControls}>
              <span className={styles.historyCount}>
                {isHistoryLoading ? "Загрузка..." : `Всего: ${history.length}`}
              </span>
              {history.length > 0 && (
                <Button
                  variant="secondary"
                  size="small"
                  onClick={handleClearHistory}
                >
                  🗑️ Очистить
                </Button>
              )}
            </div>
          </div>

          {isHistoryLoading ? (
            <div className={styles.historyEmpty}>
              <p>Загрузка истории...</p>
            </div>
          ) : history.length > 0 ? (
            <div className={styles.historyList}>
              {history.map((entry) => (
                <div key={entry.id} className={styles.historyItem}>
                  <div className={styles.historyItemHeader}>
                    <span
                      className={`${styles.historyStatus} ${entry.status?.includes("Ошибка") ? styles.statusError : styles.statusSuccess}`}
                    >
                      {entry.status}
                    </span>
                    <span className={styles.historyType}>{entry.type}</span>
                    <span className={styles.historyTime}>
                      {entry.startTime}
                    </span>
                    {entry.duration && (
                      <span className={styles.historyDuration}>
                        ⏱️ {entry.duration}
                      </span>
                    )}
                  </div>
                  <div className={styles.historyItemDetails}>
                    {entry.recordsCount > 0 && (
                      <span>📊 {entry.recordsCount} записей</span>
                    )}
                    {entry.files && entry.files.length > 0 && (
                      <div className={styles.historyFiles}>
                        <span>📄 Файлы:</span>
                        {entry.files.map((file, idx) => (
                          <span key={idx} className={styles.historyFile}>
                            {file}
                          </span>
                        ))}
                      </div>
                    )}
                    {entry.error && (
                      <span className={styles.historyError}>
                        ❌ {entry.error}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className={styles.historyEmpty}>
              <span className={styles.historyEmptyIcon}>📭</span>
              <p>История запусков пуста</p>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};

export default ParserControl;
