import { useEffect, useRef } from "react";
import Button from "../Button/Button";
import styles from "./Modal.module.scss";

const Modal = ({
  isOpen,
  onClose,
  title,
  children,
  size = "medium",
  showCloseButton = true,
  footer = null,
  footerAlignment = "right",
  onConfirm = null,
  confirmText = "Подтвердить",
  cancelText = "Отмена",
  confirmVariant = "primary",
  loading = false,
  closeOnOverlayClick = true,
  className = "",
}) => {
  const modalRef = useRef(null);

  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };

    const handleClickOutside = (e) => {
      if (
        closeOnOverlayClick &&
        modalRef.current &&
        !modalRef.current.contains(e.target)
      ) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener("keydown", handleEsc);
      document.addEventListener("mousedown", handleClickOutside);
      document.body.style.overflow = "hidden";
    }

    return () => {
      document.removeEventListener("keydown", handleEsc);
      document.removeEventListener("mousedown", handleClickOutside);
      document.body.style.overflow = "unset";
    };
  }, [isOpen, onClose, closeOnOverlayClick]);

  if (!isOpen) return null;

  const renderFooter = () => {
    if (footer) return footer;

    if (onConfirm) {
      return (
        <>
          <Button variant="secondary" onClick={onClose} disabled={loading}>
            {cancelText}
          </Button>
          <Button
            variant={confirmVariant}
            onClick={onConfirm}
            disabled={loading}
            loading={loading}
          >
            {confirmText}
          </Button>
        </>
      );
    }

    return (
      <Button variant="secondary" onClick={onClose}>
        Закрыть
      </Button>
    );
  };

  const footerClasses = [
    styles.footer,
    styles[footerAlignment],
    loading && styles.loading,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={styles.overlay}>
      <div
        ref={modalRef}
        className={`${styles.modal} ${styles[size]} ${className}`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className={styles.header}>
          <h2 className={styles.title}>{title}</h2>
          {showCloseButton && (
            <button
              className={styles.closeBtn}
              onClick={onClose}
              aria-label="Закрыть"
            >
              ✕
            </button>
          )}
        </div>

        <div className={styles.body}>{children}</div>

        {(footer || onConfirm) && (
          <div className={footerClasses}>{renderFooter()}</div>
        )}
      </div>
    </div>
  );
};

export default Modal;
