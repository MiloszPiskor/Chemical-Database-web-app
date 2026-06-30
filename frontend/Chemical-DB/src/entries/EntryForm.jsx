import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiFetch } from '../shared/apiFetch.js';

function EntryForm() {
  const navigate = useNavigate();

  const [date, setDate] = useState('');
  const [documentNr, setDocumentNr] = useState('');
  const [transactionType, setTransactionType] = useState('Purchase');
  const [company, setCompany] = useState('');
  const [lineItems, setLineItems] = useState([{ product: '', quantity: '', price_per_unit: '' }]);

  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [isError, setIsError] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
    // For dropdown menues
  const [products, setProducts] = useState([])
  const [companies, setCompanies] = useState([])

  const handleLineItemChange = (index, field, value) => {
    const newItems = [...lineItems];
    newItems[index][field] = value;
    setLineItems(newItems);
  };

  const addLineItem = () => {
    setLineItems([...lineItems, { product: '', quantity: '', price_per_unit: '' }]);
  };

  const handleSubmit = async (e) => {

    if (!company) {
        alert("Please select a company.");
        return;
        }

    const hasEmptyProduct = lineItems.some(item => !item.product);
    if (hasEmptyProduct) {
        alert("Please select a product for each line item.");
        return;
    }

  if (!/^WZ\s\d{1,4}\/\d{1,2}\/\d{4}$/.test(documentNr)) {
    alert("Document number format invalid. Use: WZ 123/02/2025.");
    return;
  }
  if (lineItems.length === 0) {
    alert("You must add at least one line item.");
    return;
  }
    e.preventDefault();
    setIsLoading(true);
    setIsError(false);

    try {
      const data = {
        date: date,
        document_nr: documentNr,
        transaction_type: transactionType,
        company: company,
        line_items: lineItems.map(item => ({
          ...item,
          quantity: Number(item.quantity),
          price_per_unit: Number(item.price_per_unit),
          product: item.product
        })),
      };

      await apiFetch('/entries', 'POST', data);

      setIsSuccess(true);
      setTimeout(() => setIsSuccess(false), 3000);

      // Reset form
      setDate('');
      setDocumentNr('');
      setTransactionType('Supply');
      setCompany('');
      setLineItems([{ product: '', quantity: '', price_per_unit: '' }]);

    } catch (error) {
      const msg = error instanceof Error ? error.message : error;
      setErrorMessage(msg);
      setIsError(true);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isSuccess) {
      const timeout = setTimeout(() => navigate('/entries'), 2000);
      return () => clearTimeout(timeout);
    }
  }, [isSuccess, navigate]);

  // Fetch Products for a dropdown menu
  useEffect(() => {
          const fetchData = async () => {
              try {
                  const data = await apiFetch('/products')
                  
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
   }, []);

  // Fetch Companies for a dropdown menu
  useEffect(() => {
    const fetchData = async () => {
        try {
            const data = await apiFetch('/companies')
            
            console.log('Companies added:', data);
            setCompanies(data); // This only runs if response was OK

        } catch (error) {
            // Check if error is a string or an Error object and handle accordingly
            const errorMessage = error instanceof Error ? error.message : error;
            console.error("Fetching companies failed:", errorMessage);
            setErrorMessage(errorMessage); // This gets the message from parseBackendError
            setIsError(true);
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
        {isSuccess && <p className="alert alert-success">Entry submitted successfully!</p>}
        {isError && <div className="alert alert-danger">{errorMessage || 'Something went wrong'}</div>}
  
        <form onSubmit={handleSubmit}>
          {/* Date Input */}
          <div className="form-group">
            <label>Date</label>
            <input 
              type="date" 
              className="form-control" 
              value={date} 
              onChange={e => setDate(e.target.value)} 
            />
          </div>
  
          {/* Document Number */}
          <div className="form-group">
            <label>Document Number</label>
            <input 
              type="text" 
              className="form-control" 
              placeholder="WZ 123/02/2025" 
              pattern="^WZ\s\d{1,4}/\d{1,2}/\d{4}$" 
              title="Format: WZ 123/02/2025" 
              value={documentNr} 
              onChange={e => setDocumentNr(e.target.value)} 
            />
          </div>
  
          {/* Transaction Type */}
          <div className="form-group">
            <label>Transaction Type</label>
            <select 
              className="form-control" 
              value={transactionType} 
              onChange={e => setTransactionType(e.target.value)}
            >
              <option value="Supply">Supply</option>
              <option value="Purchase">Purchase</option>
            </select>
          </div>
  
          {/* Select Company */}
          <div className="form-group">
            <label htmlFor="company-select">Select company</label>
            <select 
              id="company-select" 
              className="form-control" 
              value={company} 
              onChange={e => setCompany(e.target.value)}
            >
              <option value="" disabled>-- Select Company --</option>
              {companies.map(company => (
                <option key={company.name} value={company.name}>{company.name}</option>
              ))}
            </select>
          </div>
  
          {/* Line Items */}
          <h5 className="mt-4">Line Items</h5>
          {lineItems.map((item, index) => (
            <div className="form-row mb-3" key={index}>
              <div className="col-12 mb-2">
                <label htmlFor={`product-${index}`}>Product</label>
                <select 
                  id={`product-${index}`} 
                  className="form-control" 
                  value={item.product} 
                  onChange={e => handleLineItemChange(index, 'product', e.target.value)}
                >
                  <option value="" disabled>-- Select Product --</option>
                  {products.map(product => (
                    <option key={product.name} value={product.name}>{product.name}</option>
                  ))}
                </select>
              </div>
              <div className="col-12 mb-2">
                <label>Quantity</label>
                <input 
                  type="number" 
                  min="0.01" 
                  step="0.01" 
                  className="form-control" 
                  placeholder="Qty" 
                  value={item.quantity} 
                  onChange={e => handleLineItemChange(index, 'quantity', e.target.value)} 
                />
              </div>
              <div className="col-12 mb-2">
                <label>Price per unit</label>
                <input 
                  type="number" 
                  min="0.01" 
                  step="0.01" 
                  className="form-control" 
                  placeholder="Price" 
                  value={item.price_per_unit} 
                  onChange={e => handleLineItemChange(index, 'price_per_unit', e.target.value)} 
                />
              </div>
            </div>
          ))}
  
          {/* Add Line Item and Submit */}
          <div className="d-flex justify-content-between mt-3 mb-4">
            <button 
              type="button" 
              className="btn btn-outline-secondary" 
              onClick={addLineItem}
            >
              ➕ Add Line Item
            </button>
            <button 
              type="submit" 
              className="btn btn-primary"
            >
              {isLoading ? 'Submitting...' : '✅ Submit Entry'}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>

  );
}

export default EntryForm;
