import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { useParser } from "../../../hooks/useParser";
import { Card, Button } from "../../ui";
import SearchInput from "../../ui/SearchInput/SearchInput";
import ConfirmDialog from "../../ui/ConfirmDialog/ConfirmDialog";
import { importExcel } from "../../../api/apiServices";
import toast from "react-hot-toast";
import styles from "./DataTable.module.scss";

// Компонент стрелки сортировки (специально вынесен за пределы DataTable)
const SortArrow = ({ columnKey, sortConfig }) => {
  const sort = sortConfig.find((s) => s.key === columnKey);
  if (!sort) return <span className={styles.sortArrow}>↕</span>;
  return (
    <span className={`${styles.sortArrow} ${styles.sortActive}`}>
      {sort.direction === "asc" ? "↑" : "↓"}
      <sup className={styles.sortOrder}>
        {sortConfig.findIndex((s) => s.key === columnKey) + 1}
      </sup>
    </span>
  );
};

const DataTable = () => {
  const {
    records,
    totalRecords,
    loading,
    clearAllRecords,
    deleteRecords,
    loadRecords,
  } = useParser();
  const [searchTerm, setSearchTerm] = useState("");
  const [isClearing, setIsClearing] = useState(false);
  const [selectedRows, setSelectedRows] = useState([]);
  const [showScrollTop, setShowScrollTop] = useState(false);
  const [selectionMode, setSelectionMode] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [showShortcuts, setShowShortcuts] = useState(true);
  const fileInputRef = useRef(null);
  const tableContainerRef = useRef(null);
  const shortcutsRef = useRef(null);
  // Реф для хранения selectedRows без перерендера
  const selectedRowsRef = useRef([]);

  const [confirmDialog, setConfirmDialog] = useState({
    isOpen: false,
    title: "",
    message: "",
    type: "danger",
    confirmText: "Удалить",
    onConfirm: null,
    isLoading: false,
  });

  const [quickFilter, setQuickFilter] = useState(null);

  // Синхронизация рефа с состоянием
  useEffect(() => {
    selectedRowsRef.current = selectedRows;
  }, [selectedRows]);

  // Мемоизация статусов
  const recordsWithStatus = useMemo(() => {
    return records.map((record) => {
      const daysLeft = record.days_left;
      let status;

      // Приоритет: флаги от бэкенда
      if (record.is_expired === true) {
        status = "expired";
      } else if (record.is_expiring === true) {
        status = "expiring";
      } else if (record.is_new === true) {
        status = "new";
      } else if (daysLeft === undefined || daysLeft === null) {
        status = "new";
      } else if (daysLeft < 0) {
        status = "expired";
      } else if (daysLeft <= 15) {
        status = "expiring";
      } else {
        status = "new";
      }

      return { ...record, _status: status };
    });
  }, [records]);

  // Мемоизация подсчетов
  const counts = useMemo(
    () => ({
      expired: recordsWithStatus.filter((r) => r._status === "expired").length,
      expiring: recordsWithStatus.filter((r) => r._status === "expiring")
        .length,
      new: recordsWithStatus.filter((r) => r._status === "new").length,
    }),
    [recordsWithStatus],
  );

  // Мемоизация отфильтрованных записей
  const filteredRecords = useMemo(() => {
    return recordsWithStatus.filter((record) => {
      if (quickFilter === "expired" && record._status !== "expired")
        return false;
      if (quickFilter === "expiring" && record._status !== "expiring")
        return false;
      if (quickFilter === "new" && record._status !== "new") return false;
      if (!searchTerm) return true;
      const search = searchTerm.toLowerCase();
      return (
        (record.fio || "").toLowerCase().includes(search) ||
        (record.serial_number || "").toLowerCase().includes(search) ||
        (record.date_from || "").includes(search) ||
        (record.date_to || "").includes(search) ||
        (record.key_type || "").toLowerCase().includes(search) ||
        (record.key_carrier_number || "").toLowerCase().includes(search) ||
        (record.notes || "").toLowerCase().includes(search)
      );
    });
  }, [recordsWithStatus, quickFilter, searchTerm]);

  // Отслеживаем скролл
  useEffect(() => {
    const container = tableContainerRef.current;
    if (!container) return;
    const handleScroll = () => setShowScrollTop(container.scrollTop > 200);
    container.addEventListener("scroll", handleScroll, { passive: true });
    return () => container.removeEventListener("scroll", handleScroll);
  }, []);

  // Скрываем подсказку
  useEffect(() => {
    if (!selectionMode) {
      const timer = setTimeout(() => setShowShortcuts(false), 15000);
      return () => clearTimeout(timer);
    }
  }, [selectionMode]);

  const handleSearch = useCallback((value) => setSearchTerm(value), []);

  const toggleSelectionMode = () => {
    setSelectionMode((prev) => !prev);
    setSelectedRows([]);
    selectedRowsRef.current = [];
    setShowShortcuts(false);
  };

  // ОПТИМИЗИРОВАННАЯ функция выбора с предотвращением выделения
  const toggleRowSelection = useCallback((index, event) => {
    // Предотвращаем выделение текста
    event.preventDefault();

    const isShiftPressed = event?.shiftKey || false;
    const isCtrlPressed = event?.ctrlKey || event?.metaKey || false;

    setSelectedRows((prev) => {
      let newSelection;

      if (isShiftPressed && prev.length > 0) {
        const lastSelected = prev[prev.length - 1];
        const start = Math.min(lastSelected, index);
        const end = Math.max(lastSelected, index);
        const range = [];
        for (let i = start; i <= end; i++) range.push(i);
        newSelection = [...new Set([...prev, ...range])];
      } else if (isCtrlPressed) {
        newSelection = prev.includes(index)
          ? prev.filter((i) => i !== index)
          : [...prev, index];
      } else {
        newSelection = prev.includes(index)
          ? prev.filter((i) => i !== index)
          : [...prev, index];
      }

      selectedRowsRef.current = newSelection;
      return newSelection;
    });
  }, []);

  // Обработчик клика по строке — использует реф для мгновенной проверки
  const handleRowClick = useCallback(
    (index, event) => {
      if (!selectionMode) return;
      event.preventDefault();
      toggleRowSelection(index, event);
    },
    [selectionMode, toggleRowSelection],
  );

  // Мемоизированная функция проверки выделения
  const isRowSelected = useCallback(
    (index) => {
      return selectedRows.includes(index);
    },
    [selectedRows],
  );

  const handleImportExcel = () => fileInputRef.current?.click();

  const handleFileChange = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    if (!file.name.endsWith(".xlsx") && !file.name.endsWith(".xls")) {
      toast.error("❌ Поддерживаются только файлы Excel (.xlsx, .xls)");
      return;
    }
    setIsImporting(true);
    try {
      const result = await importExcel(file);
      toast.success(
        `✅ Импорт завершен! Обновлено записей: ${result.updated_count || 0}` +
          (result.total_errors > 0 ? `. Ошибок: ${result.total_errors}` : ""),
      );
    } catch (error) {
      toast.error(
        "❌ Ошибка импорта: " + (error.message || "Неизвестная ошибка"),
      );
    } finally {
      setIsImporting(false);
      event.target.value = "";
    }
  };

  const handleDeleteSelected = () => {
    if (selectedRows.length === 0) {
      toast.error("⚠️ Выберите записи для удаления");
      return;
    }
    setConfirmDialog({
      isOpen: true,
      title: "Удаление записей",
      message: `Вы уверены, что хотите удалить <strong>${selectedRows.length}</strong> записей?`,
      type: "danger",
      confirmText: "Удалить",
      onConfirm: async () => {
        setConfirmDialog((prev) => ({ ...prev, isLoading: true }));
        try {
          // Находим реальные индексы в полном массиве records
          const realIndexes = selectedRows
            .map((filteredIndex) => {
              const record = filteredRecords[filteredIndex];
              // Ищем эту запись в полном массиве records
              return records.findIndex(
                (r) =>
                  r.fio === record.fio &&
                  r.serial_number === record.serial_number &&
                  r.date_from === record.date_from,
              );
            })
            .filter((i) => i !== -1);

          await deleteRecords(realIndexes);
          toast.success(`🗑️ Удалено ${realIndexes.length} записей`);
          setSelectedRows([]);
          selectedRowsRef.current = [];
          setSelectionMode(false);
          setConfirmDialog({
            isOpen: false,
            isLoading: false,
            onConfirm: null,
          });
          // Перезагружаем записи
          loadRecords(1000);
        } catch (error) {
          toast.error("❌ Ошибка при удалении: " + (error.message || error));
          setConfirmDialog((prev) => ({ ...prev, isLoading: false }));
        }
      },
      isLoading: false,
    });
  };

  const handleClearAll = () => {
    setConfirmDialog({
      isOpen: true,
      title: "Очистка всех записей",
      message: `Вы уверены, что хотите удалить <strong>все ${totalRecords}</strong> записей?`,
      type: "danger",
      confirmText: "Очистить всё",
      onConfirm: async () => {
        setConfirmDialog((prev) => ({ ...prev, isLoading: true }));
        setIsClearing(true);
        try {
          await clearAllRecords();
          toast.success("🗑️ Все записи успешно удалены!");
          setSelectedRows([]);
          selectedRowsRef.current = [];
          setSelectionMode(false);
          setConfirmDialog({
            isOpen: false,
            isLoading: false,
            onConfirm: null,
          });
        } catch (error) {
          toast.error("❌ Ошибка при удалении: " + error.message);
          setConfirmDialog((prev) => ({ ...prev, isLoading: false }));
        } finally {
          setIsClearing(false);
        }
      },
      isLoading: false,
    });
  };

  // ============================================
  // МНОГОУРОВНЕВАЯ СОРТИРОВКА
  // ============================================
  const [sortConfig, setSortConfig] = useState([]); // Массив [{key, direction}]

  const handleSort = (key) => {
    setSortConfig((prev) => {
      const existing = prev.find((s) => s.key === key);

      if (!existing) {
        // Добавляем новую сортировку
        return [...prev, { key, direction: "asc" }];
      }

      if (existing.direction === "asc") {
        // Меняем на desc
        return prev.map((s) =>
          s.key === key ? { key, direction: "desc" } : s,
        );
      }

      // Убираем сортировку
      return prev.filter((s) => s.key !== key);
    });
  };

  // Очистить всю сортировку
  const clearSort = () => setSortConfig([]);

  // Функция парсинга даты
  const parseDate = (dateStr) => {
    if (!dateStr) return 0;
    const cleaned = dateStr.split(",")[0].trim();
    const parts = cleaned.split(".");
    if (parts.length === 3) {
      return new Date(
        parseInt(parts[2]),
        parseInt(parts[1]) - 1,
        parseInt(parts[0]),
      ).getTime();
    }
    return 0;
  };

  // Многоуровневая сортировка
  const sortedRecords = useMemo(() => {
    let result = [...filteredRecords];

    if (sortConfig.length === 0) return result;

    result.sort((a, b) => {
      for (const { key, direction } of sortConfig) {
        let aVal, bVal;

        if (
          key === "date_from" ||
          key === "date_to" ||
          key === "destruction_date"
        ) {
          aVal = parseDate(a[key]);
          bVal = parseDate(b[key]);
        } else if (key === "fio") {
          aVal = (a.fio || "").toLowerCase().trim();
          bVal = (b.fio || "").toLowerCase().trim();
        } else {
          aVal = (a[key] || "").toString().toLowerCase();
          bVal = (b[key] || "").toString().toLowerCase();
        }

        if (aVal !== bVal) {
          return direction === "asc"
            ? aVal < bVal
              ? -1
              : 1
            : aVal > bVal
              ? -1
              : 1;
        }
      }
      return 0;
    });

    return result;
  }, [filteredRecords, sortConfig]);

  const scrollToTop = () => {
    if (tableContainerRef.current) {
      tableContainerRef.current.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  const closeConfirmDialog = () =>
    setConfirmDialog((prev) => ({ ...prev, isOpen: false }));
  const showShortcutsAgain = () => {
    setShowShortcuts(true);
    setTimeout(() => setShowShortcuts(false), 20000);
  };
  const closeShortcuts = (e) => {
    e.stopPropagation();
    setShowShortcuts(false);
  };

  const getStatusBadge = (record) => {
    if (record.is_mock) return { text: "Имитация", class: styles.badgeMock };
    switch (record._status) {
      case "expired":
        return { text: "Истек", class: styles.badgeExpired };
      case "expiring":
        return {
          text: `Истекает (${record.days_left ?? 0} дн.)`,
          class: styles.badgeExpiring,
        };
      case "new":
        return { text: "Новый", class: styles.badgeNew };
      default:
        return { text: "Активен", class: styles.badgeActive };
    }
  };

  const getRowClassName = (record, index) => {
    const classes = [styles.tableRow];
    if (index % 2 === 0) classes.push(styles.rowEven);
    else classes.push(styles.rowOdd);
    if (selectedRows.includes(index)) classes.push(styles.rowSelected);
    switch (record._status) {
      case "expired":
        classes.push(styles.rowExpired);
        break;
      case "expiring":
        classes.push(styles.rowExpiring);
        break;
      case "new":
        classes.push(styles.rowNew);
        break;
    }
    if (record.is_mock) classes.push(styles.rowMock);
    return classes.join(" ");
  };

  const getDaysLeftClass = (daysLeft) => {
    if (daysLeft <= 7) return styles.daysLeftDanger;
    if (daysLeft <= 15) return styles.daysLeftWarning;
    return styles.daysLeftOk;
  };

  return (
    <div className={styles.dataTable}>
      <div className={styles.topBar}>
        <div className={styles.topBarLeft}>
          <h2 className={styles.title}>Журнал ключевых документов</h2>
          <span className={styles.totalCount}>Всего: {totalRecords}</span>
          {selectionMode && selectedRows.length > 0 && (
            <span className={styles.selectionBadge}>
              Выбрано: {selectedRows.length}
            </span>
          )}
        </div>
        <SearchInput
          placeholder="Поиск по ФИО, серийному номеру, дате..."
          value={searchTerm}
          onSearch={handleSearch}
          className={styles.searchInput}
          size="medium"
        />
      </div>

      <div className={styles.actionBar}>
        <div className={styles.actionBarLeft}>
          <div className={styles.quickFilters}>
            <button
              className={`${styles.filterBtn} ${styles.filterExpired} ${quickFilter === "expired" ? styles.filterActive : ""}`}
              onClick={() =>
                setQuickFilter(quickFilter === "expired" ? null : "expired")
              }
            >
              🔴 Истекшие{" "}
              <span className={styles.filterCount}>{counts.expired}</span>
            </button>
            <button
              className={`${styles.filterBtn} ${styles.filterExpiring} ${quickFilter === "expiring" ? styles.filterActive : ""}`}
              onClick={() =>
                setQuickFilter(quickFilter === "expiring" ? null : "expiring")
              }
            >
              🟠 Истекающие{" "}
              <span className={styles.filterCount}>{counts.expiring}</span>
            </button>
            <button
              className={`${styles.filterBtn} ${styles.filterNew} ${quickFilter === "new" ? styles.filterActive : ""}`}
              onClick={() =>
                setQuickFilter(quickFilter === "new" ? null : "new")
              }
            >
              🟢 Новые <span className={styles.filterCount}>{counts.new}</span>
            </button>
            {quickFilter && (
              <button
                className={styles.clearFilterBtn}
                onClick={() => setQuickFilter(null)}
              >
                ✕ Сбросить
              </button>
            )}
          </div>
          {sortConfig.length > 0 && (
            <button
              className={styles.clearSortBtn}
              onClick={clearSort}
              title="Сбросить сортировку"
            >
              🔄 Сбросить сортировку ({sortConfig.length})
            </button>
          )}
        </div>
        <div className={styles.actionBarRight}>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".xlsx,.xls"
            style={{ display: "none" }}
          />
          <Button
            variant="secondary"
            size="small"
            onClick={handleImportExcel}
            disabled={isImporting}
            className={styles.importBtn}
          >
            {isImporting ? "⏳ Импорт..." : "📥 Импорт Excel"}
          </Button>
          <Button
            variant={selectionMode ? "primary" : "secondary"}
            size="small"
            onClick={toggleSelectionMode}
            className={`${styles.selectBtn} ${selectionMode ? styles.selectBtnActive : ""}`}
          >
            {selectionMode ? "✕ Отменить выбор" : "☑️ Выбрать записи"}
          </Button>
          {selectionMode && (
            <Button
              variant="danger"
              size="small"
              onClick={handleDeleteSelected}
              disabled={selectedRows.length === 0 || isClearing}
            >
              🗑️ Удалить ({selectedRows.length})
            </Button>
          )}
          <Button
            variant="danger"
            size="small"
            onClick={handleClearAll}
            disabled={isClearing || records.length === 0}
          >
            {isClearing ? "⏳ Очистка..." : "🗑️ Очистить всё"}
          </Button>
        </div>
      </div>

      {showShortcuts && !selectionMode && (
        <div className={styles.shortcutsBar} ref={shortcutsRef}>
          <span className={styles.shortcutsIcon}>💡</span>
          <span className={styles.shortcutsText}>
            <strong>Выбор записей:</strong>
            <span className={styles.shortcutKey}>Клик</span> выбрать/снять
            <span className={styles.shortcutKey}>Ctrl+Клик</span> добавить
            <span className={styles.shortcutKey}>Shift+Клик</span> диапазон
          </span>
          <button className={styles.shortcutsClose} onClick={closeShortcuts}>
            ✕
          </button>
        </div>
      )}

      <Card className={styles.tableCard}>
        <div className={styles.tableContainer} ref={tableContainerRef}>
          {loading ? (
            <div className={styles.loadingState}>
              <div className={styles.spinner} />
              <span>Загрузка данных...</span>
            </div>
          ) : (
            <>
              <table className={styles.table}>
                <thead className={styles.tableHead}>
                  <tr>
                    {selectionMode && <th className={styles.colCheck}>☑️</th>}
                    <th className={styles.colNum}>№</th>
                    <th
                      className={styles.colDate}
                      onClick={() => handleSort("date_from")}
                    >
                      Дата установки{" "}
                      <SortArrow
                        columnKey="date_from"
                        sortConfig={sortConfig}
                      />
                    </th>
                    <th className={styles.colSkzi}>Тип СКЗИ</th>
                    <th className={styles.colService}>Обслуживание</th>
                    <th
                      className={styles.colFio}
                      onClick={() => handleSort("fio")}
                    >
                      ФИО пользователя{" "}
                      <SortArrow columnKey="fio" sortConfig={sortConfig} />
                    </th>
                    <th
                      className={styles.colDate}
                      onClick={() => handleSort("date_to")}
                    >
                      Срок действия{" "}
                      <SortArrow columnKey="date_to" sortConfig={sortConfig} />
                    </th>
                    <th className={styles.colKeyType}>Тип ключа</th>
                    <th className={styles.colSerial}>Серийный номер</th>
                    <th className={styles.colCarrier}>№ носителя</th>
                    <th
                      className={styles.colDestructionDate}
                      onClick={() => handleSort("destruction_date")}
                    >
                      Дата уничтожения{" "}
                      <SortArrow
                        columnKey="destruction_date"
                        sortConfig={sortConfig}
                      />
                    </th>
                    <th className={styles.colSign}>Подпись</th>
                    <th className={styles.colNotes}>Примечание</th>
                    <th className={styles.colStatus}>Статус</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedRecords.length > 0 ? (
                    sortedRecords.map((record, index) => {
                      const status = getStatusBadge(record);
                      return (
                        <tr
                          key={`row-${index}`}
                          className={getRowClassName(record, index)}
                          onMouseDown={(e) => handleRowClick(index, e)}
                          style={{
                            cursor: selectionMode ? "pointer" : "default",
                            userSelect: "none",
                          }}
                        >
                          {selectionMode && (
                            <td className={styles.colCheck}>
                              <input
                                type="checkbox"
                                checked={isRowSelected(index)}
                                readOnly
                                onMouseDown={(e) => {
                                  e.stopPropagation();
                                  toggleRowSelection(index, e);
                                }}
                                className={styles.checkbox}
                              />
                            </td>
                          )}
                          <td className={styles.colNum}>{index + 1}</td>
                          <td className={styles.dateValue}>
                            {record.date_from || (
                              <span className={styles.emptyField}>—</span>
                            )}
                          </td>
                          <td>{record.skzi_type || "КриптоПро CSP 5.0"}</td>
                          <td>
                            {record.service_type ||
                              "Установка ключевых документов"}
                          </td>
                          <td className={styles.fioName}>
                            {record.fio || (
                              <span className={styles.emptyField}>—</span>
                            )}
                          </td>

                          {/* ✅ ИСПРАВЛЕННЫЙ БЛОК СРОКА ДЕЙСТВИЯ */}
                          <td className={styles.dateValue}>
                            {record.date_to || (
                              <span className={styles.emptyField}>—</span>
                            )}

                            {/* Показываем только если статус НЕ expired */}
                            {record._status !== "expired" &&
                              record.days_left != null && (
                                <>
                                  {record.days_left > 0 && (
                                    <span
                                      className={`${styles.daysLeft} ${getDaysLeftClass(record.days_left)}`}
                                    >
                                      {record.days_left} дн.
                                    </span>
                                  )}
                                  {record.days_left === 0 && (
                                    <span
                                      className={`${styles.daysLeft} ${styles.daysLeftWarning}`}
                                    >
                                      Истекает сегодня
                                    </span>
                                  )}
                                </>
                              )}
                          </td>

                          <td>{record.key_type || "ЭЦП"}</td>
                          <td>
                            <span className={styles.serialCode}>
                              {record.serial_number || (
                                <span className={styles.emptyField}>—</span>
                              )}
                            </span>
                          </td>
                          <td className={styles.centeredCell}>
                            {record.key_carrier_number || (
                              <span className={styles.emptyField}>—</span>
                            )}
                          </td>
                          <td className={styles.centeredCell}>
                            {record.destruction_date || (
                              <span className={styles.emptyField}>—</span>
                            )}
                          </td>
                          <td className={styles.centeredCell}>
                            {record.destruction_signature || (
                              <span className={styles.emptyField}>—</span>
                            )}
                          </td>
                          <td className={styles.notesCell}>
                            {record.notes || (
                              <span className={styles.emptyField}>—</span>
                            )}
                          </td>
                          <td className={styles.colStatus}>
                            <span
                              className={`${styles.statusBadge} ${status.class}`}
                            >
                              {status.text}
                            </span>
                          </td>
                        </tr>
                      );
                    })
                  ) : (
                    <tr>
                      <td
                        colSpan={selectionMode ? 15 : 14}
                        className={styles.emptyState}
                      >
                        <div className={styles.emptyIcon}>
                          {searchTerm || quickFilter ? "🔍" : "📭"}
                        </div>
                        <div className={styles.emptyText}>
                          {searchTerm || quickFilter
                            ? "Ничего не найдено"
                            : "Нет данных"}
                        </div>
                        <div className={styles.emptyHint}>
                          {searchTerm || quickFilter
                            ? "Попробуйте изменить параметры поиска"
                            : "Запустите парсер или загрузите JSON/Excel файл"}
                        </div>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
              {showScrollTop && (
                <button
                  className={styles.scrollTopBtn}
                  onClick={scrollToTop}
                  title="Вернуться к началу таблицы"
                />
              )}
            </>
          )}
        </div>
        <div className={styles.footerBar}>
          <div className={styles.footerInfo}>
            Показано {filteredRecords.length} из {totalRecords} записей
            {quickFilter &&
              ` · Фильтр: ${quickFilter === "expired" ? "истекшие" : quickFilter === "expiring" ? "истекающие" : "новые"}`}
          </div>
          <div className={styles.footerLegend}>
            <div className={styles.legendItem}>
              <span className={`${styles.legendDot} ${styles.dotNew}`}></span>{" "}
              Новые
            </div>
            <div className={styles.legendItem}>
              <span
                className={`${styles.legendDot} ${styles.dotExpiring}`}
              ></span>{" "}
              Истекают
            </div>
            <div className={styles.legendItem}>
              <span
                className={`${styles.legendDot} ${styles.dotExpired}`}
              ></span>{" "}
              Истекли
            </div>
          </div>
          {!showShortcuts && !selectionMode && (
            <button
              className={styles.showShortcutsBtn}
              onClick={showShortcutsAgain}
            >
              💡 Подсказка
            </button>
          )}
        </div>
      </Card>
      <ConfirmDialog
        isOpen={confirmDialog.isOpen}
        onClose={closeConfirmDialog}
        onConfirm={confirmDialog.onConfirm}
        title={confirmDialog.title}
        message={confirmDialog.message}
        confirmText={confirmDialog.confirmText}
        cancelText="Отмена"
        type={confirmDialog.type}
        isLoading={confirmDialog.isLoading}
      />
    </div>
  );
};

export default DataTable;
