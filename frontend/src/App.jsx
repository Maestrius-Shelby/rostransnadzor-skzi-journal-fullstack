import { useDispatch } from "react-redux";
import { useEffect } from "react";
import { fetchStatus, fetchRecords } from "./store/slices/parserSlice";
import { useSelector } from "react-redux";
import { selectIsAuthenticated } from "./store/selectors/authSelectors";
import AuthProvider from "./components/AuthProvider/AuthProvider";
import AppRouter from "./AppRouter";
import styles from "./App.module.scss";

function App() {
  const dispatch = useDispatch();
  const isAuthenticated = useSelector(selectIsAuthenticated);

  useEffect(() => {
    if (isAuthenticated) {
      console.log("🚀 App mounted, fetching data...");
      dispatch(fetchStatus());
      dispatch(fetchRecords({ limit: 10 }));
    }
  }, [dispatch, isAuthenticated]);

  return (
    <div className={styles.app}>
      <AuthProvider>
        <AppRouter />
      </AuthProvider>
    </div>
  );
}

export default App;
