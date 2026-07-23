import { useEffect, useCallback } from "react";
import { useDispatch, useSelector } from "react-redux";
import { refreshToken } from "../../store/slices/authSlice";
import {
  selectAuthTokens,
  selectIsAuthenticated,
} from "../../store/selectors/authSelectors";
import { jwtDecode } from "jwt-decode";

const AuthProvider = ({ children }) => {
  const dispatch = useDispatch();
  const authTokens = useSelector(selectAuthTokens);
  const isAuthenticated = useSelector(selectIsAuthenticated);

  const isTokenExpired = (token) => {
    try {
      const decoded = jwtDecode(token);
      return decoded.exp * 1000 < Date.now();
    } catch {
      return true;
    }
  };

  const refresh = useCallback(() => {
    if (authTokens?.access_token && isTokenExpired(authTokens.access_token)) {
      dispatch(refreshToken());
    }
  }, [authTokens, dispatch]);

  // Проверка токена при монтировании
  useEffect(() => {
    if (isAuthenticated) {
      refresh();
    }
  }, [isAuthenticated, refresh]);

  // Проверка каждые 5 минут
  useEffect(() => {
    if (!isAuthenticated) return;
    const interval = setInterval(refresh, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [isAuthenticated, refresh]);

  return children;
};

export default AuthProvider;
