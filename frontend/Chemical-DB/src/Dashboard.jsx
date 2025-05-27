import { useEffect, useState } from "react";
import { useUser } from "./shared/UserContext";
import { Row, Col, Card, Button } from "react-bootstrap";
import { FaBox, FaBuilding, FaClipboardList, FaSpinner } from "react-icons/fa";
import { useNavigate } from "react-router-dom";
import { oktaAuth } from "./shared/oktaConfig";

function Dashboard() {
  const [isAuth, setIsAuth] = useState(false);
  const { user } = useUser();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const checkAuth = async () => {
      setIsLoading(true); 
      const auth = await oktaAuth.isAuthenticated();
      setIsAuth(auth);
      setIsLoading(false);
    };
    checkAuth();
  }, []);
  


  if (isLoading) {
    return (
      <div className="d-flex justify-content-center align-items-center flex-column" style={{ height: '100vh' }}>
        <FaSpinner className="spinner-border text-primary" size={50} />
        <p className="mt-3 text-primary fs-4">Loading...</p>
      </div>
    );
  }

  if (!isAuth || !user) {
    // User not authenticated or user object missing
    return (
      <div className="text-center mt-5">
        <h1>Welcome to Chemical Database Web App!</h1>
        <p className="lead">Please log in to access your dashboard.</p>
        <Button variant="primary" onClick={() => oktaAuth.signInWithRedirect()}>
          Log In
        </Button>
      </div>
    );
  }

  // If authenticated
  return (
    <>
      <Row className="text-center mt-5">
        <Col md={4}>
          <Card onClick={() => navigate("/products")} className="shadow hover-scale">
            <Card.Body>
              <FaBox size={40} className="text-primary mb-3" />
              <Card.Title>Products</Card.Title>
              <Card.Text>Manage and browse all products</Card.Text>
            </Card.Body>
          </Card>
        </Col>
        <Col md={4}>
          <Card onClick={() => navigate("/companies")} className="shadow hover-scale">
            <Card.Body>
              <FaBuilding size={40} className="text-success mb-3" />
              <Card.Title>Companies</Card.Title>
              <Card.Text>View and update company info</Card.Text>
            </Card.Body>
          </Card>
        </Col>
        <Col md={4}>
          <Card onClick={() => navigate("/entries")} className="shadow hover-scale">
            <Card.Body>
              <FaClipboardList size={40} className="text-warning mb-3" />
              <Card.Title>Entries</Card.Title>
              <Card.Text>Transaction records and details</Card.Text>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </>
  );
}

export default Dashboard;
