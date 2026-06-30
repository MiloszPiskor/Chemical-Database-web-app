import React, { useEffect, useState } from 'react';
import { useOktaAuth } from '@okta/okta-react'; // assuming you're using this
import { useNavigate } from 'react-router-dom';
import { Link } from 'react-router-dom';
import { apiFetch } from '../shared/apiFetch';
import { FaSpinner, FaExclamationTriangle } from 'react-icons/fa';


function FetchProducts() {

    const navigate = useNavigate();
    const { oktaAuth } = useOktaAuth();

    const [products, setProducts] = useState([]);
    const [isError, setIsError] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [errorMessage, setErrorMessage] = useState('');

    useEffect(() => {
        const fetchData = async () => {
            try {
                const data = await apiFetch('/products', 'GET')
                
                console.log('Product added:', data);
                setProducts(data); // This only runs if response was OK

            } catch (error) {
                // Check if error is a string or an Error object and handle accordingly
                const errorMessage = error instanceof Error ? error.message : error;
                console.error("Fetching products failed:", errorMessage);
                setErrorMessage(errorMessage); // This gets the message from parseBackendError
                setIsError(true);
            } finally {
                setIsLoading(false);
            }
        };

        fetchData();
    }, [oktaAuth]);

    if (isLoading) return (
        <div className="d-flex flex-column align-items-center justify-content-center my-5 text-primary">
          <FaSpinner className="fa-spin" size={40} />
          <p className="mt-3 fs-5">Loading...</p>
        </div>
      );
      if (isError) return (
        <div className="d-flex flex-column align-items-center justify-content-center my-5 text-danger">
          <FaExclamationTriangle size={40} />
          <p className="mt-3 fs-5">{errorMessage || "Something went wrong..."}</p>
        </div>
      );
      if (products.length === 0) return (
        <div className="text-center my-5">
          <p className="fs-4">No products in database yet</p>
          <button
            onClick={() => navigate('/products/new')}
            className="btn btn-primary btn-lg mt-3"
          >
            Add new Product!
          </button>
        </div>
      );

    return (
        <>
            <div className="container-fluid">
            <div className="row">
            {products.map(product => (
                <div className="col-12 col-md-6 col-lg-6 mb-4" key={product.id}>
                <div key={product.id} className="card h-100 w-100 shadow-sm rounded-3 product-card hover-shadow"
                    style={{ cursor: 'pointer' }}>
                    <img className="card-img-top" src={product.img_url} alt="Product" />
                    <div className="card-body">
                        <h5 className="card-title">{product.name}</h5>
                        <p className="card-text">Customs code: {product.customs_code}</p>
                        <Link to={`/products/${product.id}`} className="btn btn-primary">
                            Product's Details
                        </Link>
                    </div>
                </div>
                </div>
            ))}
            </div>
            </div>
            <div style={{ marginTop: '2rem' }}>
                <button onClick={() => navigate('/products/new')} type="button" className="btn btn-primary btn-lg btn-block">Add new Product!</button>
            </div>
        </>
    );
}

export default FetchProducts;