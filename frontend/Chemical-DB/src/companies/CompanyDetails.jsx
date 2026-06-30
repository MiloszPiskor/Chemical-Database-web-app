import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiFetch } from '../shared/apiFetch';
import { FaBuilding, FaMapMarkerAlt, FaUserAlt, FaPhone } from 'react-icons/fa';

function CompanyDetails() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [company, setCompany] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [deleteStatus, setDeleteStatus] = useState({
    loading: false,
    success: false,
    error: null,
    message: null
  });

  useEffect(() => {
    const fetchCompany = async () => {
      try {
        const data = await apiFetch(`/companies/${id}`);
        setCompany(data.company);
      } catch (err) {
        setError(err.message || 'Failed to load company :(');
      } finally {
        setIsLoading(false);
      }
    };
    fetchCompany();
  }, [id]);

  useEffect(() => {
    if (deleteStatus.success) {
      const timeout = setTimeout(() => {
        navigate('/companies');
      }, 2000);
      return () => clearTimeout(timeout);
    }
  }, [deleteStatus.success, navigate]);

  async function deleteCompany() {
    try {
      setDeleteStatus({ loading: true, success: false, error: null, message: null });
      const data = await apiFetch(`/companies/${id}`, 'DELETE');
      setDeleteStatus({ loading: false, success: true, error: null, message: data.success });
    } catch (err) {
      setDeleteStatus({ loading: false, success: false, error: err.message || 'Error', message: null });
    }
  }

  if (isLoading) return <p>Loading...</p>;
  if (error) return <p>{error}</p>;
  if (!company) return <p>No company found</p>;

  if (deleteStatus.success) {
    return (
      <div className="container py-5 text-center">
        <div className="alert alert-success display-5 fw-bold">
          🎉 {deleteStatus.message}
        </div>
      </div>
    );
  }

  return (
    <div className="container py-5">
    <div className="row justify-content-center">
    <div className="col-lg-10 col-xl-8">
      <div className="row align-items-start">
        {/* Image or Placeholder */}
        <div className="col-md-6 mb-4 text-center">
          <div className="bg-light d-inline-flex justify-content-center align-items-center rounded-circle shadow" style={{ width: '150px', height: '150px' }}>
            <FaBuilding size={80} className="text-primary" />
          </div>
        </div>

        {/* Company Info */}
        <div className="col-md-6">
          <h2 className="mb-3">{company.name}</h2>
          <ul className="list-group list-group-flush mb-3">
            <li className="list-group-item">
              <FaMapMarkerAlt className="me-2 text-muted" />
              <strong>Address:</strong> {company.address}
            </li>
            <li className="list-group-item">
              <FaUserAlt className="me-2 text-muted" />
              <strong>Contact Person:</strong> {company.contact_person || 'N/A'}
            </li>
            <li className="list-group-item">
              <FaPhone className="me-2 text-muted" />
              <strong>Contact Number:</strong> {company.contact_number}
            </li>
            <li className="list-group-item">
              <strong>Company ID:</strong> {company.id}
            </li>
            <li className="list-group-item">
              <strong>User ID:</strong> {company.user_id}
            </li>
          </ul>

          <div className="d-flex gap-3">
            <button onClick={() => navigate(`/companies/${company.id}/edit`)} className="btn btn-outline-primary">Edit Company</button>
            <button onClick={deleteCompany} className="btn btn-outline-danger">{deleteStatus.loading ? 'Deleting...' : 'Delete'}</button>
            {deleteStatus.error && <div className="alert alert-danger mt-2">{deleteStatus.error}</div>}
          </div>
        </div>
      </div>
      </div>
      </div>
    </div>
  );
}

export default CompanyDetails;
