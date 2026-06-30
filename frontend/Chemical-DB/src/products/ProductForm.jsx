import React, {useState, useEffect} from 'react'
import { apiFetch } from '../shared/apiFetch.js';
import { useNavigate } from 'react-router-dom';

function ProductForm() {

    const [name, setName] = useState('');

    const navigate = useNavigate();
    
    const [code, setCode] = useState('');

    const [img, setImg] = useState('');

    const [isError, setIsError] = useState(false);

    const [isLoading, setIsLoading] = useState(false);

    const [isSuccess, setIsSuccess] = useState(false);

    const [errorMessage, setErrorMessage] = useState('');

    function handleName (event) {
        setName(event.target.value)
    }

    function handleCode (event) {
        setCode(event.target.value)
    }

    function handleUrl (event) {
        setImg(event.target.value)
    }

    const handleSubmit = async (event) => {

        event.preventDefault(); // Prevent page reload

        setIsLoading(true);

        setIsError(false);   // reset error

        try {
            const data = {
                "name": name.trim(),
                "customs_code": code,
                "img_url": img
            };

            const responseData = await apiFetch('/products', 'POST', data)

            console.log(`The response from the server after a post request: ${responseData}`)

            // reset form on success
            setName('');
            setCode('');
            setImg('');
            
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
            navigate(`/products`);
            }, 2000);
        
            return () => clearTimeout(timeout);
        }
        }, [isSuccess, navigate]);


    return (
        <>
            {isSuccess && <p className="alert alert-success">Product submitted successfully!</p>}

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
                        <label htmlFor="productName">Product Name</label>
                        <input value={name} onChange={handleName} type="text" className="form-control" id="productName" placeholder="Enter product name" />
                    </div>
    
                    <div className="form-group">
                        <label htmlFor="customsCode">Customs Code</label>
                        <input value={code} onChange={handleCode} type="number" className="form-control" id="customsCode" placeholder="Enter customs code" />
                    </div>
    
                    <div className="form-group">
                        <label htmlFor="imgUrl">Image Url</label>
                        <input value={img} onChange={handleUrl} type="url" className="form-control" id="imgUrl" placeholder="Enter image url" />
                    </div>
    
                    <button type="submit" className="btn btn-primary">{isLoading ? 'Submitting...' : 'Submit'}</button>
                </form>
            )}
        </>
    );
}

export default ProductForm;

