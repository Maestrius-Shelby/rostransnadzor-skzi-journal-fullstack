import styles from "./Card.module.scss";

const Card = ({
  children,
  className = "",
  variant = "default",
  title = null,
  subtitle = null,
  headerAction = null,
  noPadding = false,
  elevated = false,
  ...props
}) => {
  const cardClass = [
    styles.card,
    styles[variant],
    className,
    noPadding && styles.noPadding,
    elevated && styles.elevated,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={cardClass} {...props}>
      {(title || subtitle || headerAction) && (
        <div className={styles.cardHeader}>
          <div>
            {title && <h3 className={styles.cardTitle}>{title}</h3>}
            {subtitle && <p className={styles.cardSubtitle}>{subtitle}</p>}
          </div>
          {headerAction && <div>{headerAction}</div>}
        </div>
      )}
      {children}
    </div>
  );
};

// Card.Grid для сетки карточек
Card.Grid = ({ children, className = "", ...props }) => (
  <div className={`${styles.cardGrid} ${className}`} {...props}>
    {children}
  </div>
);

export default Card;
