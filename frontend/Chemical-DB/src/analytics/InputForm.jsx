import React, { useState, useEffect } from 'react';
import { apiFetch } from '../shared/apiFetch.js';

function InputForm({ onSubmit, fields }) {

  const [formData, setFormData] = useState({
    productId: "",
    companyId: "",
    start: "",
    end: "",
    start2: "",
    end2: "",
    limit: ""
  });

  const [products, setProducts] = useState([])
  const [companies, setCompanies] = useState([])

  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [isError, setIsError] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setIsError(false);

    for (const field in fields) {
        if (!formData[field] && fields[field].mandatory) {
            alert("Please fill out all mandatory fields.");
            setIsLoading(false);
            return;
        }
    }

    try {
        await onSubmit(formData);  // // <-- pass the form data to the parent

        setIsSuccess(true);
        setTimeout(() => setIsSuccess(false), 3000);

        // // Reset form DESIREABLE???????
        // setFormData({
        //     productId: "",
        //     companyId: "",
        //     start: "",
        //     end: "",
        //     start2: "",
        //     end2: "",
        //     limit: ""
        // });
      } catch (error) {
        setIsError(true);
        setErrorMessage(error.message || "Submission failed.");
      } finally {
        setIsLoading(false);
      }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value
    }));
  };

    // Fetch Products for a dropdown menu
    useEffect(() => {
            const fetchData = async () => {
                try {
                    const data = await apiFetch('/products')
                    setProducts(data);
                } catch (error) {
                    const errorMessage = error instanceof Error ? error.message : error;
                    console.error("Fetching products failed:", errorMessage);
                    setErrorMessage(errorMessage);
                    setIsError(true);
                } finally {
                    setIsLoading(false);
                }
            };
            fetchData();
     }, []);
  
    // Fetch Companies for a dropdown menu
    useEffect(() => {
      const fetchData = async () => {
          try {
              const data = await apiFetch('/companies')
              setCompanies(data);
          } catch (error) {
              const errorMessage = error instanceof Error ? error.message : error;
              console.error("Fetching companies failed:", errorMessage);
              setErrorMessage(errorMessage); 
          } finally {
              setIsLoading(false);
          }
      };
      fetchData();
    }, []);

  return (
    <div className="container my-5">
    <div className="row justify-content-center">
      <div className="col-12">
        {isSuccess && <p className="alert alert-success">Analysis loaded successfully!</p>}
        {isError && <div className="alert alert-danger">{errorMessage || 'Something went wrong'}</div>}
  
        <form onSubmit={handleSubmit}>

            {/* Product Id */}
            {fields.productId?.present && (
              <div className="form-group">
                <label>Product {fields.productId.mandatory ? '(Mandatory)' : ''}</label>
                <select
                  name="productId"
                  className="form-control"
                  value={formData.productId}
                  onChange={handleChange}
                >
                  <option value="" disabled>-- Select Product --</option>
                  {products.map(product => (
                    <option key={product.id} value={product.id}>{product.name}</option>
                  ))}
                </select>
              </div>
            )}
  
            {/* Company Id */}
            {fields.companyId?.present && (
              <div className="form-group">
                <label>Company {fields.companyId.mandatory ? '(Mandatory)' : ''}</label>
                <select
                  name="companyId"
                  className="form-control"
                  value={formData.companyId}
                  onChange={handleChange}
                >
                  <option value="" disabled>-- Select Company --</option>
                  {companies.map(company => (
                    <option key={company.id} value={company.id}>{company.name}</option>
                  ))}
                </select>
              </div>
            )}
  
          {/* Start Date */}
          {fields.start?.present && (
              <div className="form-group">
                <label>Start {fields.start.mandatory ? '(Mandatory)' : ''}</label>
                <input
                  type="date"
                  name="start"
                  className="form-control"
                  value={formData.start}
                  onChange={handleChange}
                />
              </div>
            )}
  
          {/* End Date */}
          {fields.end?.present && (
              <div className="form-group">
                <label>End {fields.end.mandatory ? '(Mandatory)' : ''}</label>
                <input
                  type="date"
                  name="end"
                  className="form-control"
                  value={formData.end}
                  onChange={handleChange}
                />
              </div>
            )}
  
          {/* Start Date 2*/}
          {fields.start2?.present && (
              <div className="form-group">
                <label>Start 2 {fields.start2.mandatory ? '(Mandatory)' : ''}</label>
                <input
                  type="date"
                  name="start2"
                  className="form-control"
                  value={formData.start2}
                  onChange={handleChange}
                />
              </div>
            )}
  
          {/* End Date 2*/}
          {fields.end2?.present && (
              <div className="form-group">
                <label>End 2 {fields.end2.mandatory ? '(Mandatory)' : ''}</label>
                <input
                  type="date"
                  name="end2"
                  className="form-control"
                  value={formData.end2}
                  onChange={handleChange}
                />
              </div>
            )}

          {/* Limit*/}
          {fields.limit?.present && (
              <div className="form-group">
                <label>Limit {fields.limit.mandatory ? '(Mandatory)' : ''}</label>
                <input
                  type="number"
                  name="limit"
                  className="form-control"
                  value={formData.limit}
                  onChange={handleChange}
                />
              </div>
            )}
            <div className="form-group my-2">
              <button type="submit" className="btn btn-primary">
              {isLoading ? 'Submitting...' : '✅ Sumbit for analysis'}
            </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
export default InputForm;
