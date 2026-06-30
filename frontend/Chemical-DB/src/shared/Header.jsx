import { useOktaAuth } from "@okta/okta-react";
import { useNavigate } from "react-router-dom";

function Header () {

    const navigate = useNavigate();

    const { oktaAuth } = useOktaAuth();

    const login = async () => {
        console.log("Redirecting to Okta login...");
        console.log("oktaAuth:", oktaAuth);
        await oktaAuth.signInWithRedirect({
            originalUri: '/',
            extraParams: {
              prompt: 'login'  // <- forces user to always re-authenticate
            }
        });
    };

    const logout = async () => {
        await oktaAuth.signOut();
      };

    return (
      <>
        <div className="container-fluid">
        <header className="d-flex flex-wrap justify-content-center py-3 mb-4 border-bottom fixed-top bg-white shadow-sm">
          <a href="/" className="d-flex align-items-center mb-3 mb-md-0 me-md-auto link-body-emphasis text-decoration-none">
            <svg className="bi me-2" width="40" height="32" aria-hidden="true"><use xlinkHref="#bootstrap" /></svg>
            <span className="fs-4">Prexpol's Database</span>
          </a>
  
          <ul className="nav nav-pills">
            <li className="nav-item"><a href="#" className="nav-link active" aria-current="page">Home</a></li>
            <li className="nav-item"><button onClick={() => navigate('/analytics/home')} className="nav-link btn btn-link">Analytics</button></li>
            <li className="nav-item"><button onClick={() => navigate('/products')} className="nav-link btn btn-link">Products</button></li>
            <li className="nav-item"><button onClick={() => logout()} className="nav-link btn btn-link">Logout</button></li>
            <li className="nav-item"><button onClick={() => login()} className="nav-link btn btn-link">Login</button></li>
          </ul>
        </header>
        </div>
      </>
    );

}

export default Header;