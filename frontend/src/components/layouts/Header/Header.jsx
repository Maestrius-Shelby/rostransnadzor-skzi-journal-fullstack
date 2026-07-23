import { useState, useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useSelector, useDispatch } from "react-redux";
import { selectIsAuthenticated } from "../../../store/selectors/authSelectors";
import { logoutUser } from "../../../store/slices/authSlice";
import styles from "./Header.module.scss";

const Header = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const [scrolled, setScrolled] = useState(false);
  const isAuthenticated = useSelector(selectIsAuthenticated);

  const navItems = [
    { path: "/", label: "📊 Дашборд" },
    { path: "/parser", label: "🚀 Парсер" },
  ];

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const handleLogout = () => {
    dispatch(logoutUser());
    navigate("/login");
  };

  return (
    <header className={`${styles.header} ${scrolled ? styles.scrolled : ""}`}>
      <div className={styles.container}>
        <Link to="/" className={styles.logo}>
          <span>🏦</span>
          <h1>Росказна Парсер</h1>
        </Link>

        <nav className={styles.nav}>
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`${styles.link} ${
                location.pathname === item.path ? styles.active : ""
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className={styles.status}>
          {isAuthenticated ? (
            <>
              <span className={styles.adminBadge}>👑 Админ</span>
              <button
                onClick={handleLogout}
                className={styles.logoutBtn}
                title="Выйти"
              >
                🚪 Выйти
              </button>
            </>
          ) : (
            <>
              <span className={styles.statusDot}></span>
              Online
            </>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;
