import Sidebar from "./Sidebar";
import { Outlet } from 'react-router-dom';

function AnalyticsLayout() {
    return (
      <div className="d-flex" style={{ minHeight: "100vh" }}>
        <Sidebar />
        <div
          className="d-flex justify-content-center flex-grow-1 p-4 bg-light main-content"
          style={{ marginLeft: "280px", maxWidth: "calc(100% - 280px)" }}
        >
          <div className="w-100" style={{ maxWidth: "1200px" }}>
           {/* Outlet automatically renders the correct dashboard */}

            <Outlet /> 
          </div>
        </div>
      </div>
    );
  }


export default AnalyticsLayout;
  