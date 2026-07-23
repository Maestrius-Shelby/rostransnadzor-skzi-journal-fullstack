import { Button } from "../../ui";
import styles from "./ConfirmDialog.module.scss";

const ConfirmDialog = ({
  isOpen,
  onClose,
  onConfirm,
  title = "Подтверждение",
  message = "Вы уверены?",
  confirmText = "Удалить",
  cancelText = "Отмена",
  type = "danger",
  isLoading = false,
}) => {
  if (!isOpen) return null;

  const getIcon = () => {
    switch (type) {
      case "danger":
        return "🗑️";
      case "warning":
        return "⚠️";
      case "info":
        return "ℹ️";
      default:
        return "❓";
    }
  };

  const getTitleColor = () => {
    switch (type) {
      case "danger":
        return styles.dangerTitle;
      case "warning":
        return styles.warningTitle;
      case "info":
        return styles.infoTitle;
      default:
        return "";
    }
  };

  // Очищаем HTML теги из сообщения для отображения как текст
  const cleanMessage = (msg) => {
    return msg.replace(/<[^>]*>/g, "");
  };

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.iconWrapper}>
          <span className={styles.icon}>{getIcon()}</span>
        </div>

        <h3 className={`${styles.title} ${getTitleColor()}`}>{title}</h3>
        <p className={styles.message}>{cleanMessage(message)}</p>

        <div className={styles.actions}>
          <Button
            variant="secondary"
            onClick={onClose}
            disabled={isLoading}
            className={styles.cancelButton}
          >
            {cancelText}
          </Button>
          <Button
            variant={type === "danger" ? "danger" : "primary"}
            onClick={onConfirm}
            disabled={isLoading}
            className={styles.confirmButton}
            loading={isLoading}
          >
            {isLoading ? "Удаление..." : confirmText}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmDialog;
