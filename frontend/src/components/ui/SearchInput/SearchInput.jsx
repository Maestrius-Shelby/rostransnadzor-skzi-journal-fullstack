import { useState, useRef, useEffect } from "react";
import styles from "./SearchInput.module.scss";

const SearchInput = ({
  value,
  onChange,
  placeholder = "Поиск...",
  disabled = false,
  className = "",
  size = "medium",
  onSearch,
  delay = 300,
  ...props
}) => {
  const [isFocused, setIsFocused] = useState(false);
  const [localValue, setLocalValue] = useState(value || "");
  const timeoutRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (value !== undefined) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setLocalValue(value);
    }
  }, [value]);

  const handleChange = (e) => {
    const newValue = e.target.value;
    setLocalValue(newValue);

    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      if (onChange) {
        onChange(e);
      }
      if (onSearch) {
        onSearch(newValue);
      }
    }, delay);
  };

  const handleClear = () => {
    setLocalValue("");
    if (onChange) {
      onChange({ target: { value: "" } });
    }
    if (onSearch) {
      onSearch("");
    }
    inputRef.current?.focus();
  };

  const handleFocus = () => setIsFocused(true);
  const handleBlur = () => setIsFocused(false);

  const sizeClass = styles[size] || styles.medium;

  return (
    <div className={`${styles.searchWrapper} ${className}`}>
      <div
        className={`${styles.searchContainer} ${isFocused ? styles.focused : ""} ${disabled ? styles.disabled : ""}`}
      >
        {/* Иконка поиска */}
        <div className={styles.searchIcon}>
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
        </div>

        {/* Поле ввода */}
        <input
          ref={inputRef}
          type="text"
          value={localValue}
          onChange={handleChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          placeholder={placeholder}
          disabled={disabled}
          className={`${styles.searchInput} ${sizeClass}`}
          {...props}
        />

        {/* Кнопка очистки */}
        {localValue && !disabled && (
          <button
            className={styles.clearButton}
            onClick={handleClear}
            type="button"
            aria-label="Очистить поиск"
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
};

export default SearchInput;
