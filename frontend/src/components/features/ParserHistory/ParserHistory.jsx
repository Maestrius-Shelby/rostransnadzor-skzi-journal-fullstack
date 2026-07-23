import { useState, useEffect, useCallback } from "react";
import { Card, Button } from "../../ui";
import { getHistory } from "../../../api/apiServices";
import toast from "react-hot-toast";
import styles from "./ParserHistory.module.scss";

const ParserHistory = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);

  // Загружаем историю
  const loadHistory = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getHistory(100); // 100 записей
      setHistory(Array.isArray(data) ? data : []);
    } catch (error) {
      toast.error(
        "❌ Ошибка загрузки истории: " +
          (error.message || "Неизвестная ошибка"),
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadHistory();
    // Обновляем каждые 30 секунд
    const interval = setInterval(loadHistory, 30000);
    return () => clearInterval(interval);
  }, [loadHistory]);

  const formatDate = (dateStr) => {
    if (!dateStr) return "—";
    const date = new Date(dateStr);
    return date.toLocaleString("ru-RU", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case "completed":
        return (
          <span className={`${styles.badge} ${styles.success}`}>
            ✅ Завершен
          </span>
        );
      case "running":
        return (
          <span className={`${styles.badge} ${styles.running}`}>
            🔄 Выполняется
          </span>
        );
      case "error":
        return (
          <span className={`${styles.badge} ${styles.error}`}>❌ Ошибка</span>
        );
      case "stopped":
        return (
          <span className={`${styles.badge} ${styles.stopped}`}>
            ⏹ Остановлен
          </span>
        );
      default:
        return (
          <span className={`${styles.badge} ${styles.idle}`}>⏸ Ожидание</span>
        );
    }
  };

  const getTypeBadge = (type) => {
    if (type === "mock") {
      return (
        <span className={`${styles.typeBadge} ${styles.mock}`}>
          🧪 Имитация
        </span>
      );
    }
    return (
      <span className={`${styles.typeBadge} ${styles.real}`}>🚀 Реальный</span>
    );
  };

  const formatDuration = (start, end) => {
    if (!start || !end) return "—";
    const startTime = new Date(start);
    const endTime = new Date(end);
    const diff = (endTime - startTime) / 1000; // секунды

    if (diff < 60) return `${Math.round(diff)} сек`;
    if (diff < 3600)
      return `${Math.floor(diff / 60)} мин ${Math.round(diff % 60)} сек`;
    return `${Math.floor(diff / 3600)} ч ${Math.floor((diff % 3600) / 60)} мин`;
  };

  return (
    <div className={styles.history}>
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <h2>📋 История парсинга</h2>
          <span className={styles.count}>Всего: {history.length}</span>
        </div>
        <Button
          variant="secondary"
          size="small"
          onClick={loadHistory}
          disabled={loading}
          icon="🔄"
        >
          {loading ? "Загрузка..." : "Обновить"}
        </Button>
      </div>

      <Card className={styles.historyCard}>
        {loading && history.length === 0 ? (
          <div className={styles.loading}>
            <span className={styles.loaderSpinner}></span>
            <span>Загрузка истории...</span>
          </div>
        ) : history.length === 0 ? (
          <div className={styles.empty}>
            <span className={styles.emptyIcon}>📭</span>
            <p>История парсинга пуста</p>
            <span className={styles.emptyHint}>
              Запустите парсер, чтобы появились записи
            </span>
          </div>
        ) : (
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>№</th>
                  <th>Дата и время</th>
                  <th>Тип</th>
                  <th>Статус</th>
                  <th>Записей</th>
                  <th>Длительность</th>
                  <th>Файлы</th>
                </tr>
              </thead>
              <tbody>
                {history.map((item, index) => (
                  <tr
                    key={item.id || index}
                    className={`${styles.row} ${item.status === "running" ? styles.runningRow : ""}`}
                    onClick={() =>
                      setSelectedItem(selectedItem === index ? null : index)
                    }
                  >
                    <td>{history.length - index}</td>
                    <td>{formatDate(item.started_at)}</td>
                    <td>{getTypeBadge(item.type)}</td>
                    <td>{getStatusBadge(item.status)}</td>
                    <td className={styles.recordCount}>
                      {item.records_count || 0}
                    </td>
                    <td>
                      {formatDuration(item.started_at, item.completed_at)}
                    </td>
                    <td>
                      <div className={styles.files}>
                        {item.files?.excel && (
                          <a
                            href={`/api/export/download?path=${encodeURIComponent(item.files.excel)}`}
                            className={styles.fileLink}
                            target="_blank"
                            rel="noopener noreferrer"
                            title="Скачать Excel"
                          >
                            📊
                          </a>
                        )}
                        {item.files?.json && (
                          <a
                            href={`/api/export/download?path=${encodeURIComponent(item.files.json)}`}
                            className={styles.fileLink}
                            target="_blank"
                            rel="noopener noreferrer"
                            title="Скачать JSON"
                          >
                            📄
                          </a>
                        )}
                        {!item.files?.excel && !item.files?.json && (
                          <span className={styles.noFiles}>—</span>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
};

export default ParserHistory;
