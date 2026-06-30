import { useEffect, useState } from 'react';
import { ListGroup, Collapse, Button, Spinner } from 'react-bootstrap';
import { FaSpinner, FaExclamationTriangle } from 'react-icons/fa';
import { apiFetch } from '../shared/apiFetch.js';
import { useNavigate } from 'react-router-dom';

function EntryItem({ entry }) {
  const [open, setOpen] = useState(false);

  const totalAmount = entry.line_items.reduce(
    (sum, item) => sum + (Number(item.quantity) || 0) * (Number(item.price_per_unit) || 0),
    0
  );

  return (
    <ListGroup.Item className="mb-4">
      <div className="d-flex justify-content-between align-items-center">
        <div className="w-75">
          <strong>{entry.document_nr}</strong> | {entry.company} | {entry.transaction_type} | {entry.date} | <strong>Total:</strong> ${totalAmount.toFixed(2)}
        </div>
        <Button
          variant="outline-primary"
          size="sm"
          onClick={() => setOpen(!open)}
          aria-controls={`collapse-entry-${entry.document_nr}`}
          aria-expanded={open}
        >
          {open ? 'Hide Details' : 'Show Details'}
        </Button>
      </div>
      <Collapse in={open}>
        <div className="mt-3" id={`collapse-entry-${entry.document_nr}`}>
          <table className="table table-sm table-bordered w-100">
            <thead>
              <tr>
                <th>Product</th>
                <th>Quantity</th>
                <th>Unit Price</th>
                <th>Total</th>
              </tr>
            </thead>
            <tbody>
              {entry.line_items.map((item, index) => (
                <tr key={index}>
                  <td>{item.product}</td>
                  <td>{item.quantity}</td>
                  <td>${item.price_per_unit.toFixed(2)}</td>
                  <td>${(item.quantity * item.price_per_unit).toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Collapse>
    </ListGroup.Item>
  );
}

function EntryList() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    async function fetchEntries() {
      try {
        console.log("Fetching...")
        const data = await apiFetch('/entries');
        console.log(`Backend entried data: ${data}`)
        setEntries(data);
      } catch (err) {
        setError(true);
        console.error('Failed to fetch entries:', err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchEntries();
  }, []);

  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center flex-column" style={{ height: '100vh' }}>
        <FaSpinner className="spinner-border text-primary" size={50} />
        <p className="mt-3 text-primary fs-4">Loading entries...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center text-danger mt-5">
        <FaExclamationTriangle size={50} />
        <p>{error || "Something went wrong..."}</p>
      </div>
    );
  }

  if (entries.length === 0) {
    return (
      <div className="text-center mt-5">
        <p className="fs-4">No entries in the database yet</p>
        <button
          onClick={() => navigate('/entries/new')}
          type="button"
          className="btn btn-primary btn-lg mt-3"
        >
          Add new Entry!
        </button>
      </div>
    );
  }

  return (
    <div className="container mt-4">
      <h2>Entries</h2>
        <ListGroup className="w-100">
          {entries.map((entry) => (
            <EntryItem key={entry.document_nr} entry={entry} />
          ))}
        </ListGroup>
        <div className="d-flex justify-content-center mt-4">
            <Button variant="primary" size="lg" onClick={() => navigate('/entries/new')}>
            Add New Entry
            </Button>
        </div>
    </div>
  );
}

export default EntryList;
