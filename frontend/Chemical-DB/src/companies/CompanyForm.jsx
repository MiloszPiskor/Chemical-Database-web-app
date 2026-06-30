import React, {useState, useEffect} from 'react'
import { apiFetch } from '../shared/apiFetch.js';
import { useNavigate } from 'react-router-dom';

function CompanyForm() {

    const navigate = useNavigate();

    const [name, setName] = useState(null);
    const [address, setAddress] = useState(null)
    const [contactPerson, setContactPerson] = useState(null)
    const [contactNumber, setContactNumber] = useState(null)
    const [isError, setIsError] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [isSuccess, setIsSuccess] = useState(false);
    const [errorMessage, setErrorMessage] = useState(null);

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

        event.preventDefault(); // Prevent page reload

        setIsLoading(true);

        setIsError(false);   // reset error

        try {
            const data = {
                "name": name.trim(),
                "address": address,
                "contact_person": contactPerson,
                "contact_number" : `${contactNumber}`
            };

            const responseData = await apiFetch('/companies', 'POST', data)

            console.log(`The response from the server after a post request: ${responseData}`)

            // reset form on success
            setName('');
            setAddress('');
            setContactPerson('');
            setContactNumber('');
            
            // To show success message
            setIsSuccess(true);
            setTimeout(() => setIsSuccess(false), 3000); // 3 sec flash


        } catch (error) {
            // Check if error is a string or an Error object and handle accordingly
            const errorMessage = error instanceof Error ? error.message : error;
            console.error("Fetching products failed:", errorMessage);
            setErrorMessage(errorMessage); // This gets the message from parseBackendError
            setIsError(true);
            } finally {
                console.log("Successfully posted a product!")
                setIsLoading(false);
            }

    };

        // 2. Redirect after successful deletion
    useEffect(() => {
    
        if (isSuccess) {
            const timeout = setTimeout(() => {
            navigate(`/companies`);
            }, 2000);
        
            return () => clearTimeout(timeout);
        }
        }, [isSuccess, navigate]);

    useEffect(() => {
        if (isError) {
            setIsError(false);
            setErrorMessage(null);
        }
    }, [name, address, contactPerson, contactNumber]);


    return (
        <>
            {isSuccess && <p className="alert alert-success">Company submitted successfully!</p>}

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

export default CompanyForm;