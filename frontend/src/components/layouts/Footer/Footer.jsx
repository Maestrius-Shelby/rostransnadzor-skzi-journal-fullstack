import styles from "./Footer.module.scss";

const Footer = () => {
  const year = new Date().getFullYear();

  return (
    <footer className={styles.footer}>
      <div className={styles.container}>
        <span>© {year} Росказна Парсер</span>
        <span className={styles.version}>v1.0.0</span>
      </div>
    </footer>
  );
};

export default Footer;
