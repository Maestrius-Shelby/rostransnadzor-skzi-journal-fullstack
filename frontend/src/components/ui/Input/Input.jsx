import { useState, useId } from "react";
import styles from "./Input.module.scss";

const Input = ({
  type = "text",
  value,
  onChange,
  placeholder,
  label,
  error,
  helperText,
  disabled = false,
  className = "",
  id,
  size = "medium",
  icon = null,
  iconRight = null,
  required = false,
  optional = false,
  success = false,
  ...props
}) => {
  // Используем useId для генерации уникального ID
  const generatedId = useId();
  const inputId = id || `input-${generatedId}`;
  const [showPassword, setShowPassword] = useState(false);

  const isPassword = type === "password";
  const inputType = isPassword && showPassword ? "text" : type;

  const inputClass = [
    styles.input,
    styles[size],
    error && styles.error,
    success && styles.success,
    icon && styles.hasIconLeft,
    (iconRight || isPassword) && styles.hasIconRight,
  ]
    .filter(Boolean)
    .join(" ");

  const handleTogglePassword = () => {
    setShowPassword(!showPassword);
  };

  return (
    <div className={`${styles.inputGroup} ${className}`}>
      {label && (
        <label htmlFor={inputId} className={styles.label}>
          {label}
          {required && <span className={styles.required}>*</span>}
          {optional && <span className={styles.optional}>(необязательно)</span>}
        </label>
      )}

      <div className={styles.inputWrapper}>
        {icon && <span className={styles.iconLeft}>{icon}</span>}

        <input
          id={inputId}
          type={inputType}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          disabled={disabled}
          className={inputClass}
          {...props}
        />

        {isPassword && (
          <span
            className={styles.iconRight}
            onClick={handleTogglePassword}
            role="button"
            tabIndex={0}
          >
            {showPassword ? "👁️" : "👁️‍🗨️"}
          </span>
        )}

        {iconRight && !isPassword && (
          <span className={styles.iconRight}>{iconRight}</span>
        )}
      </div>

      {error && <span className={styles.errorText}>{error}</span>}
      {helperText && !error && (
        <span className={styles.helperText}>{helperText}</span>
      )}
    </div>
  );
};

export default Input;
