import React, { useState, useEffect } from 'react';
import { apiFetch } from '../shared/apiFetch.js';
import { useParams, useNavigate } from 'react-router-dom';

function CompanyEditForm() {
    const { id } = useParams();
    const navigate = useNavigate();

    const [name, setName] = useState(null);
    const [address, setAddress] = useState(null)
    const [contactPerson, setContactPerson] = useState(null)
    const [contactNumber, setContactNumber] = useState(null)

    const [isError, setIsError] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [isSuccess, setIsSuccess] = useState(false);
    const [errorMessage, setErrorMessage] = useState('');

    function handleName (event) {
        setName(event.target.value)
    }
    function handlePerson (event) {
        setContactPerson(event.target.value)
    }
    function handleNumber (event) {
        setContactNumber(event.target.value)
    }
    function handleAddress (event) {
        setAddress(event.target.value)
    }

    const handleSubmit = async (event) => {
        event.preventDefault();
        setIsLoading(true);
        setIsError(false);

        try {
            const updatedCompany = {
                name: name.trim(),
                "address": address,
                "contact_person": contactPerson,
                "contact_number" : `${contactNumber}`
            };

            const responseData = await apiFetch(`/companies/${id}`, 'PATCH', updatedCompany);
            console.log("PATCH response:", responseData);

            setIsSuccess(true);
            setTimeout(() => setIsSuccess(false), 3000);
        } catch (error) {
            const message = error instanceof Error ? error.message : error;
            console.error("Error updating company:", message);
            setErrorMessage(message);
            setIsError(true);
        } finally {
            setIsLoading(false);
        }
    };

    // Fetch company data and autofill respective form fields
    useEffect(() => {
        async function fetchCompany() {
            setIsLoading(true);
            try {
                const data = await apiFetch(`/companies/${id}`, 'GET');
                setName(data.company.name);
                setAddress(data.company.address);
                setContactPerson(data.company.contact_person);
                setContactNumber(data.company.contact_number);
            } catch (err) {
                setErrorMessage(err.message || 'Failed to load company data.');
                setIsError(true);
            } finally {
                setIsLoading(false);
            }
        }

        fetchCompany();
    }, [id]);

    // Redirect to /companies after successful edit 
    useEffect(() => {
        if (isSuccess) {
            const timeout = setTimeout(() => {
                navigate(`/companies/${id}`);
            }, 2000);
            return () => clearTimeout(timeout);
        }
    }, [isSuccess, navigate, id]);

    return (
        <>
            {isSuccess && <p className="alert alert-success">Company updated successfully!</p>}

            {isError && (
                <div className="alert alert-danger" role="alert">
                    {errorMessage || "Something went wrong... Please try again."}
                </div>
            )}

            {isLoading ? (
                <p>Loading...</p>
            ) : (
                <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label htmlFor="name">Company Name</label>
                    <input value={name} onChange={handleName} type="text" className="form-control" id="companytName" placeholder="Enter company name" />
                </div>

                <div className="form-group">
                    <label htmlFor="address">Company's Address</label>
                    <input value={address} onChange={handleAddress} type="text" className="form-control" id="companyAddress" placeholder="Enter company's address" />
                </div>

                <div className="form-group">
                    <label htmlFor="contactPerson">Contact Person</label>
                    <input value={contactPerson} onChange={handlePerson} type="text" className="form-control" id="contactPerson" placeholder="Enter a contact person" />
                </div>

                <div className="form-group">
                    <label htmlFor="contactNumber">Contact Number</label>
                    <input value={contactNumber} onChange={handleNumber} type="tel" className="form-control" id="contactNumber" placeholder="Enter the contact number" />
                </div>

                <button type="submit" className="btn btn-primary">{isLoading ? 'Submitting...' : 'Submit'}</button>
            </form>
            )}
        </>
    );
}

export default CompanyEditForm;
