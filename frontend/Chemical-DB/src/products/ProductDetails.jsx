import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { apiFetch } from '../shared/apiFetch';
import { useNavigate } from 'react-router-dom';

function ProductDetails() {

    const { id } = useParams();

    const navigate = useNavigate();

    const [product, setProduct] = useState(null);

    const [isRegenerating, setIsRegenerating] = useState(false);

    const [isLoading, setIsLoading] = useState(true);

    const [error, setError] = useState('');

    const [errors, setErrors] = useState({});

    const [summary, setSummary] = useState(null);

    const [summaryError, setSummaryError] = useState(null);

    const [deleteStatus, setDeleteStatus] = useState({
        loading: false,
        success: false,
        error: null,
        message: null
      });


    async function deleteProduct () {

        try {
            setDeleteStatus({ loading: true, success: false, error: null, message: null })

            const data = await apiFetch(`/products/${id}`, 'DELETE')

            setDeleteStatus({ loading: false, success: true, error: null, message: data.success })

        } catch (err) {
            setDeleteStatus({ loading: false, success: false, error: err.message || "Error", message: null })
        }
    }

    async function regenerateSummary () {

        try {
            setIsRegenerating(true);
            setSummaryError(null);

        const data = await apiFetch(`/products/${id}/regenerate-summary`, 'PATCH')

        setSummary(data.summary);
        
        } catch (err) {
        setSummaryError(err.message || "Something went wrong.");
        } finally {
            setIsRegenerating(false);
        } 

    }


    // 1. Fetching product
    useEffect(() => {

    const fetchProduct = async () => {
    try{
        const data = await apiFetch(`/products/${id}`); // method: 'GET' and body: null by default
        setProduct(data.product); // Due to json response object structure
        setSummary(data.product.summary);
        console.log(data.product, data.product.id)
        console.log(product)
    } catch (err) {
        setError( {error : err.message || 'Failed to load product :('});
    } finally {
        setIsLoading(false);
    }
    };

    fetchProduct();
}, [id]);

    // 2. Redirect after successful deletion
    useEffect(() => {

    if (deleteStatus.success) {
      const timeout = setTimeout(() => {
        navigate('/products');
      }, 2000);
  
      return () => clearTimeout(timeout);
    }
  }, [deleteStatus.success, navigate]);

    if (isLoading) return <p>Loading...</p>;
    if (error) return <p>{error}</p>;
    if (!product) return <p>No product found</p>;
    if (deleteStatus.success) {
        return (
          <div className="container py-5 text-center">
            <div className="alert alert-success display-5 fw-bold">
              🎉 {deleteStatus.message}
            </div>
          </div>
        );
      }

    return(
        <div className="container py-5">
      <div className="row align-items-start">
        {/* Image */}
        <div className="col-md-6 mb-4">
          <img
            src={product.img_url}
            alt={product.name}
            className="img-fluid rounded shadow-sm"
          />
        </div>

        {/* Info */}
        <div className="col-md-6">
          <h2 className="mb-3">{product.name}</h2>

          <h5 className="text-primary">Product Assistant Summary</h5>
          {summaryError && <div className="alert alert-danger">{summaryError}</div>}
          <p className="mb-3">{summary}</p>
          <button onClick={regenerateSummary} className="btn btn-outline-danger" disabled={isRegenerating}>
            {isRegenerating ? "Regenerating..." : "Regenerate Summary"}
          </button>

          <ul className="list-group list-group-flush mb-3">
            <li className="list-group-item">
              <strong>Customs Code:</strong> {product.customs_code}
            </li>
            <li className="list-group-item">
              <strong>Product ID:</strong> {product.id}
            </li>
            <li className="list-group-item">
              <strong>User ID:</strong> {product.user_id}
            </li>
            <li className="list-group-item">
              <strong>Stock:</strong>{' '}
              {product.stock > 0 ? (
                <span className="badge bg-success">In Stock ({product.stock})</span>
              ) : (
                <span className="badge bg-danger">Out of Stock</span>
              )}
            </li>
          </ul>

          <div className="d-flex gap-3">
          <button onClick={() => navigate(`/products/${product.id}/edit`)} className="btn btn-outline-primary">Edit Product</button>
          <button onClick={deleteProduct} className="btn btn-outline-danger">{deleteStatus.loading ? 'Deleting' : 'Delete'}</button>
            {deleteStatus.error && <div className="alert alert-danger">{deleteStatus.error}</div>}
          </div>
        </div>
      </div>
    </div>
  
    );
}

export default ProductDetails;