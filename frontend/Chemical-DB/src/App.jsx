import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './Dashboard';
import Header from './shared/Header';
import Footer from './shared/Footer';
import { UserProvider } from "./shared/UserContext";
import 'bootstrap/dist/css/bootstrap.min.css';
import OktaSecurity from './shared/OktaSecurity';
import { LoginCallback } from '@okta/okta-react';
import FetchProducts from './products/Products';
import ProductForm from './products/ProductForm';
import ProductDetails from './products/ProductDetails';
import EditForm from './products/ProductEditForm';
import FetchCompanies from './companies/Companies';
import CompanyForm from './companies/CompanyForm';
import CompanyDetails from './companies/CompanyDetails';
import CompanyEditForm from './companies/CompanyEditForm';
import EntryList from './entries/Entries';
import EntryForm from './entries/EntryForm';
import AnalyticsLayout from './analytics/AnalyticsLayout';
import AnalyticsHome from './analytics/AnalyticsHome';
import SummaryDashboard from './analytics/dashboards/SummaryDashboard';

function App() {
  return (
    <Router>
      <OktaSecurity>
        <UserProvider>
          <Header />
          <div className="app-content" style={{ paddingTop: '70px', paddingBottom: '70px' }}>

            {/* Analytics routes render full-width with sidebar */}
            <Routes>
              {/* Render the Analytics Layout (sidebar) */}
              <Route path="/analytics/*" element={<AnalyticsLayout />}>
                <Route path="home" element={<AnalyticsHome />} />
                <Route path="global/summary" element={<SummaryDashboard />} />
                {/*
                <Route path="global/products-tally" element={<PurchaseDashboard />} />
                <Route path="global/companies-tally" element={<SupplyDashboard />} />
                <Route path="global/quick-trends" element={<SupplyDashboard />} />
                <Route path="global/compare-periods" element={<SupplyDashboard />} />
                <Route path="products/:id/top-partners" element={<SupplyDashboard />} />
                <Route path="companies/:id/products" element={<SupplyDashboard />} />
                <Route path="companies/:id/top-products" element={<SupplyDashboard />} />
                <Route path="companies/:company_id/products/:product_id" element={<SupplyDashboard />} /> */}
              </Route>

              {/* All other routes use centered layout */}
              <Route
                path="*"
                element={
                  <div className="container my-5">
                    <div className="row justify-content-center">
                      <div className="col-12 col-md-10">
                        <Routes>
                          <Route path="/" element={<Dashboard />} />
                          <Route path="/login/callback" element={<LoginCallback />} />
                          {/* Product Related */}
                          <Route path="/products" element={<FetchProducts />} />
                          <Route path="/products/new" element={<ProductForm />} />
                          <Route path="/products/:id" element={<ProductDetails />} />
                          <Route path="/products/:id/edit" element={<EditForm />} />
                          {/* Company Related */}
                          <Route path="/companies" element={<FetchCompanies />} />
                          <Route path="/companies/new" element={<CompanyForm />} />
                          <Route path="/companies/:id" element={<CompanyDetails />} />
                          <Route path="/companies/:id/edit" element={<CompanyEditForm />} />
                          {/* Entries Related */}
                          <Route path="/entries" element={<EntryList />} />
                          <Route path="/entries/new" element={<EntryForm />} />
                        </Routes>
                      </div>
                    </div>
                  </div>
                }
              />
            </Routes>
          </div>
          <Footer />
        </UserProvider>
      </OktaSecurity>
    </Router>
  );
}

  // return (
  //   <Router>
  //     <OktaSecurity>
  //       <UserProvider>
  //       <Header />
  //       <div className="app-content" style={{ paddingTop: '70px', paddingBottom: '70px' }}>
  //       <div className="container my-5">
  //       <div className="row justify-content-center">
  //       <div className="col-12 col-md-10">
  //         <Routes>
  //           {/* Product Related */}
  //           <Route path="/" element={<Dashboard />} />
  //           <Route path="/login/callback" element={<LoginCallback />} />
  //           <Route path="/products" element={<FetchProducts />} />
  //           <Route path="/products/new" element={<ProductForm />} />
  //           <Route path="/products/:id" element={<ProductDetails />} />
  //           <Route path="/products/:id/edit" element={<EditForm />} />
  //           {/* Company Related */}
  //           <Route path="/companies" element={<FetchCompanies />} />
  //           <Route path="/companies/new" element={<CompanyForm />} />
  //           <Route path="/companies/:id" element={<CompanyDetails />} />
  //           <Route path="/companies/:id/edit" element={<CompanyEditForm/>} />
  //           {/* Entries Related */}
  //           <Route path="/entries" element={<EntryList />} />
  //           <Route path="/entries/new" element={<EntryForm />} />
  //           {/* Analytics Related */}
  //           <Route path="/analytics/*" element={<AnalyticsLayout />} >
  //             <Route path="report" element={<div>Analytics Report</div>}/>
  //           </ Route>
  //         </Routes>
  //       </div>
  //       </div>
  //       </div>
  //       </div>
  //       <Footer />
  //       </UserProvider>
  //     </OktaSecurity>
  //   </Router>
  // );


export default App;
