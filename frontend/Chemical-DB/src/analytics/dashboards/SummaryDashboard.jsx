import { useState } from "react";
import buildQueryString from "../../shared/queryParamBuilder";
import SummaryRecap from "./SummaryRecap";
import InputForm from "../InputForm"
import { FaSpinner } from "react-icons/fa";
import { apiFetch } from "../../shared/apiFetch";

function SummaryDashboard() {
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);
    const [isError, setIsError] = useState(false);
    const [errorMessage, setErrorMessage] = useState("");
  

    const handleSubmit = async (formData) => {
        setLoading(true);
        setIsError(false);
        setResults(null);

        try {
        const queryString = buildQueryString(formData)
        const data = await apiFetch(`/analytics/global/summary${queryString}`, 'GET');
        setResults(data);
        }   catch (error) {
            const msg = error instanceof Error ? error.message : error;
            setErrorMessage(msg);
            setIsError(true);
        }   finally {
            setLoading(false);
        }
        };
  
        return (
            <div className="container my-4">
              {/* === Form Section === */}
              <h2 className="mb-3">Search Criteria</h2>
              <InputForm
                fields={{
                  productId: { present: true, mandatory: false },
                  companyId: { present: true, mandatory: false },
                  start: { present: true, mandatory: false },
                  end: { present: true, mandatory: false },
                  limit: { present: false, mandatory: false },
                  start2: { present: false, mandatory: false },
                  end2: { present: false, mandatory: false },
                }}
                onSubmit={handleSubmit}
              />
          
              <hr className="my-5" />
          
              {/* === Analytics Section === */}
              <h2 className="mb-4">Analytics Results</h2>
          
              {loading && (
                <div className="d-flex justify-content-center align-items-center flex-column mt-5">
                  <FaSpinner className="spinner-border text-primary" size={50} />
                  <p className="mt-3 text-primary fs-4">Loading analytics...</p>
                </div>
              )}
          
              {isError && (
                <div className="alert alert-danger mt-4" role="alert">
                  {errorMessage}
                </div>
              )}
          
              {!loading && results && !isError && (
                <>
                  {results?.empty === "true" ? (
                    <p className="text-muted mt-4">{results.message}</p>
                  ) : (
                    <SummaryRecap data={results} />
                  )}
                </>
              )}
            </div>
          );
          
}

export default SummaryDashboard;
