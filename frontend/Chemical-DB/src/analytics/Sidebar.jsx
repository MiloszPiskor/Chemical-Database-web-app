import { useState } from "react";
import { useLocation, Link } from "react-router-dom";

function Sidebar() {
  const location = useLocation();
  const showSidebar = location.pathname.startsWith("/analytics");

  const [homeCollapse, setHomeCollapse] = useState(true);
  const [dashboardCollapse, setDashboardCollapse] = useState(false);
  const [ordersCollapse, setOrdersCollapse] = useState(false);

  if (!showSidebar) return null;

  return (
    <aside
      className="bg-light border-end p-3"
      style={{
        width: "280px",
        position: "fixed",
        top: 0,
        bottom: 0,
        left: 0,
        zIndex: 1000,
        overflowY: "auto",
      }}
    >
      <Link
        to="/"
        className="d-flex align-items-center mb-3 mb-md-0 me-md-auto text-dark text-decoration-none"
      >
        <svg className="bi me-2" width="30" height="24">
          <use xlinkHref="#bootstrap" />
        </svg>
        <span className="fs-5 fw-bold">Collapsible</span>
      </Link>

      <hr />

      <ul className="nav nav-pills flex-column mb-auto">

        {/* DASHBOARD SECTION */}
        <li className="nav-item mb-2">
          <button
            className="btn btn-toggle w-100 text-start"
            onClick={() => setDashboardCollapse(!dashboardCollapse)}
          >
            Companies
          </button>
          {dashboardCollapse && (
            <ul className="nav flex-column ms-3">
              <li><Link to="#" className="nav-link text-dark">Companies' products</Link></li>
              <li><Link to="#" className="nav-link text-dark">Companies' top products</Link></li>
              <li><Link to="#" className="nav-link text-dark">Company - Product insights</Link></li>
            </ul>
          )}
        </li>

        {/* ORDERS SECTION */}
        <li className="nav-item mb-2">
          <button
            className="btn btn-toggle w-100 text-start"
            onClick={() => setOrdersCollapse(!ordersCollapse)}
          >
            Products
          </button>
          {ordersCollapse && (
            <ul className="nav flex-column ms-3">
              <li><Link to="#" className="nav-link text-dark">Product insights</Link></li>
            </ul>
          )}
        </li>

          {/* ORDERS SECTION */}
          <li className="nav-item mb-2">
            <button
              className="btn btn-toggle w-100 text-start"
              onClick={() => setOrdersCollapse(!ordersCollapse)}
            >
            Global
          </button>
          {ordersCollapse && (
            <ul className="nav flex-column ms-3">
              <li><Link to="/analytics/global/summary" className="nav-link text-dark">Summary</Link></li>
              <li><Link to="#" className="nav-link text-dark">Products' tally</Link></li>
              <li><Link to="#" className="nav-link text-dark">Companies' tally</Link></li>
              <li><Link to="#" className="nav-link text-dark">Quick trends</Link></li>
              <li><Link to="#" className="nav-link text-dark">Compare periods</Link></li>
            </ul>
          )}
        </li>

        <hr />
        {/* ACCOUNT SECTION
        <li className="nav-item mb-2">
          <button
            className="btn btn-toggle w-100 text-start"
            onClick={() => setAccountCollapse(!accountCollapse)}
          >
            Account
          </button>
          {accountCollapse && (
            <ul className="nav flex-column ms-3">
              <li><Link to="#" className="nav-link text-dark">New...</Link></li>
              <li><Link to="#" className="nav-link text-dark">Profile</Link></li>
              <li><Link to="#" className="nav-link text-dark">Settings</Link></li>
              <li><Link to="#" className="nav-link text-dark">Sign out</Link></li>
            </ul>
          )}
        </li> */}
      </ul>
    </aside>
  );
}

export default Sidebar;



  