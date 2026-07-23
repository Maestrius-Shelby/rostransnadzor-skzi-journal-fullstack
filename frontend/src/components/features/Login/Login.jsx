import { useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";
import { loginUser } from "../../../store/slices/authSlice";
import {
  selectAuthLoading,
  selectIsAuthenticated,
} from "../../../store/selectors/authSelectors";
import { Card } from "../../ui";
import toast from "react-hot-toast";
import styles from "./Login.module.scss";

const Login = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState({});
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const dispatch = useDispatch();
  const navigate = useNavigate();
  const loading = useSelector(selectAuthLoading);
  const isAuthenticated = useSelector(selectIsAuthenticated);

  // Редирект после успешного входа
  useEffect(() => {
    if (isAuthenticated) {
      const timer = setTimeout(() => navigate("/"), 800);
      return () => clearTimeout(timer);
    }
  }, [isAuthenticated, navigate]);

  const validateFields = (user, pass) => {
    const newErrors = {};
    if (!user.trim()) newErrors.username = "Введите логин";
    if (!pass.trim()) newErrors.password = "Введите пароль";
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitted(true);
    if (!validateFields(username, password)) return;

    try {
      await dispatch(loginUser({ username, password })).unwrap();
      toast.success("✅ Добро пожаловать, Администратор!", {
        icon: "🔐",
        duration: 3000,
      });
    } catch (error) {
      toast.error(error || "Ошибка входа");
      setErrors({ auth: error || "Неверный логин или пароль" });
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") handleSubmit(e);
  };

  // Успешный вход — показываем приветствие
  if (isAuthenticated) {
    return (
      <div className={styles.login}>
        <Card className={styles.successCard}>
          <div className={styles.successIcon}>🔐</div>
          <h2>Вход выполнен</h2>
          <p className={styles.successRole}>
            <span className={styles.adminBadge}>👑 Администратор</span>
          </p>
          <p className={styles.successHint}>Перенаправление...</p>
          <div className={styles.successBar}>
            <div className={styles.successFill} />
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className={styles.login}>
      <Card className={styles.loginCard}>
        {/* Заголовок */}
        <div className={styles.loginHeader}>
          <div className={styles.loginIcon}>🛡️</div>
          <h2>Вход в систему</h2>
          <p className={styles.loginSubtitle}>Панель администратора СКЗИ</p>
        </div>

        <form onSubmit={handleSubmit} className={styles.form}>
          {/* Логин */}
          <div className={styles.field}>
            <label className={styles.label}>
              <span className={styles.labelIcon}>👤</span> Логин
            </label>
            <input
              type="text"
              name="username"
              value={username}
              onChange={(e) => {
                setUsername(e.target.value.slice(0, 50));
                if (isSubmitted) validateFields(e.target.value, password);
              }}
              onKeyDown={handleKeyDown}
              className={`${styles.input} ${isSubmitted && errors.username ? styles.inputError : ""}`}
              placeholder="admin"
              disabled={loading}
              autoComplete="username"
            />
            {isSubmitted && errors.username && (
              <span className={styles.errorMessage}>{errors.username}</span>
            )}
          </div>

          {/* Пароль */}
          <div className={styles.field}>
            <label className={styles.label}>
              <span className={styles.labelIcon}>🔑</span> Пароль
            </label>
            <div className={styles.passwordWrapper}>
              <input
                type={showPassword ? "text" : "password"}
                name="password"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value.slice(0, 50));
                  if (isSubmitted) validateFields(username, e.target.value);
                }}
                onKeyDown={handleKeyDown}
                className={`${styles.input} ${isSubmitted && errors.password ? styles.inputError : ""}`}
                placeholder="••••••"
                disabled={loading}
                autoComplete="current-password"
              />
              <button
                type="button"
                className={styles.togglePassword}
                onClick={() => setShowPassword(!showPassword)}
                tabIndex={-1}
              >
                {showPassword ? "🙈" : "👁️"}
              </button>
            </div>
            {isSubmitted && errors.password && (
              <span className={styles.errorMessage}>{errors.password}</span>
            )}
          </div>

          {/* Ошибка авторизации */}
          {errors.auth && (
            <div className={styles.authError}>
              <span>⚠️</span> {errors.auth}
            </div>
          )}

          {/* Кнопка */}
          <button
            type="submit"
            className={`${styles.submitBtn} ${loading ? styles.loading : ""}`}
            disabled={loading || !username.trim() || !password.trim()}
          >
            {loading ? (
              <span className={styles.spinner} />
            ) : (
              <>
                <span className={styles.btnIcon}>🔐</span>
                Войти как администратор
              </>
            )}
          </button>
        </form>

        {/* Подсказка */}
        <p className={styles.hint}>
          Доступ только для авторизованного персонала
        </p>
      </Card>
    </div>
  );
};

export default Login;
