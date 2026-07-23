import Dashboard from "../../components/features/Dashboard/Dashboard";
import DataTable from "../../components/features/DataTable/DataTable";
import styles from "./HomePage.module.scss";

const HomePage = () => {
  return (
    <div className={styles.homePage}>
      <Dashboard />
      <DataTable />
    </div>
  );
};

export default HomePage;
