import { useState, useEffect } from "react";
import { useParser } from "../../../hooks/useParser";
import { getWatcherStatus } from "../../../api/apiServices";
import styles from "./Dashboard.module.scss";

const Dashboard = () => {
  const { isConnected } = useParser();
  const [watcherRunning, setWatcherRunning] = useState(false);
  const [excelFile, setExcelFile] = useState(null);

  useEffect(() => {
    const checkWatcher = async () => {
      if (!isConnected) {
        setWatcherRunning(false);
        setExcelFile(null);
        return;
      }

      try {
        const data = await getWatcherStatus();
        setWatcherRunning(data.running);
        setExcelFile(data.excel_file);
      } catch {
        setWatcherRunning(false);
        setExcelFile(null);
      }
    };

    checkWatcher();
    const interval = setInterval(checkWatcher, 5000);
    return () => clearInterval(interval);
  }, [isConnected]);

  return (
    <div className={styles.dashboard}>
      <div className={styles.statusRow}>
        <span
          className={`${styles.dot} ${isConnected ? styles.online : styles.offline}`}
        />
        <span>Сервер {isConnected ? "онлайн" : "офлайн"}</span>
        <span className={styles.separator}>|</span>
        <span
          className={`${styles.dot} ${watcherRunning ? styles.online : styles.offline}`}
        />
        <span>
          Вотчер {watcherRunning ? "активен" : "не активен"}
          {excelFile && ` (${excelFile})`}
        </span>
        <span className={styles.hint}>
          💡 Измените Excel в <code>output/Журнал_СКЗИ.xlsx</code> — данные
          обновятся автоматически
        </span>
      </div>
    </div>
  );
};

export default Dashboard;
