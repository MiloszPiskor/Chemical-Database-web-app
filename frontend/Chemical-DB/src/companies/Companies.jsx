import React, { useEffect, useState } from 'react';
import { FaBuilding, FaUserAlt, FaPhone, FaMapMarkerAlt, FaSpinner, FaExclamationTriangle, FaPlus } from 'react-icons/fa';
import { apiFetch } from '../shared/apiFetch';
import { useNavigate } from 'react-router-dom';

function FetchCompanies() {

    const navigate = useNavigate();

    const [companies, setCompanies] = useState([]);
    const [errorMessage, setErrorMessage] = useState(null);
    const [isError, setIsError] = useState(false);
    const [isLoading, setIsLoading] = useState(true);


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

    if (isLoading) {
        return (
            <div className="d-flex justify-content-center align-items-center flex-column" style={{ height: '100vh' }}>
                <FaSpinner className="spinner-border text-primary" size={50} />
                <p className="mt-3 text-primary fs-4">Loading companies...</p>
            </div>
        );
    }
    if (isError) {
        return (
            <div className="text-center text-danger">
                <FaExclamationTriangle size={50} />
                <p>{errorMessage || "Something went wrong..."}</p>
            </div>
        );
    }
    if (companies.length === 0) {
        return (
            <div className="container py-5">
                 <div className="row justify-content-center">
                    <div className="col-md-8 text-center">

                        <button className="btn btn-primary mb-4" onClick={() => navigate('/companies/new')}>
                            Add New Company
                        </button>

                    <div className="alert alert-warning text-dark">
                        <h4 className="alert-heading">No Companies Available</h4>
                        <p className="mb-0">There are currently no companies in the database. Please add new companies to get started.</p>
                    </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <>
            {/* Add New Company Button */}
            <div className="container mb-4">
                <div className="d-flex justify-content-center">
                <button className="btn btn-primary" onClick={() => navigate('/companies/new')}>
                    <FaPlus className="me-2" /> Add New Company
                </button>
                </div>
            </div>

            {/* Companies Grid */}
            <div className="container-fluid">
                <div className="row">
                {companies.map(company => (
                    <div className="col-12 col-md-6 col-lg-6 mb-4" key={company.id}>
                    <div
                        className="card h-100 w-100 shadow-sm rounded-3 company-card hover-shadow"
                        style={{ cursor: 'pointer' }}
                        onClick={() => onViewDetails(company.id)}
                    >
                        <div className="row g-0 align-items-center">
                        {/* Icon */}
                        <div className="col-4 d-flex justify-content-center align-items-center p-3">
                            <div
                            className="bg-light rounded-circle d-flex justify-content-center align-items-center"
                            style={{ width: '60px', height: '60px' }}
                            >
                            <FaBuilding className="text-primary" size={30} />
                            </div>
                        </div>

                        {/* Info */}
                        <div className="col-8">
                            <div className="card-body">
                            <h5 className="card-title mb-1">{company.name}</h5>
                            <p className="card-text mb-1">
                                <FaMapMarkerAlt className="me-2 text-muted" />
                                {company.address}
                            </p>
                            <p className="card-text mb-1">
                                <FaUserAlt className="me-2 text-muted" />
                                {company.contact_person}
                            </p>
                            <p className="card-text">
                                <FaPhone className="me-2 text-muted" />
                                {company.contact_number}
                            </p>
                            <button
                                className="btn btn-outline-primary mt-3"
                                onClick={(e) => {
                                e.stopPropagation(); // Prevent card click from triggering
                                navigate(`/companies/${company.id}`);
                                }}
                            >View Details
                            </button>
                            </div>
                        </div>
                        </div>
                    </div>
                    </div>
                ))}
                </div>
            </div>
        </>
    );
}

export default FetchCompanies;