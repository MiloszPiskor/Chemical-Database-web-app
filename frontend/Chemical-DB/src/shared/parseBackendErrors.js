export default async function parseBackendError(response, data) {
    // Check if the response is not OK
    if (!response.ok) {
        console.error("Backend Error Data:", data);  // Log the detailed error
        // Extract the error message from the response and throw an error
        const msg = data.error || data.message || "Something went wrong.";
        throw new Error(msg);
    }
}







// export default async function parseBackendError(response) {
//     const data = await response.json();

//     if (!response.ok) {
//         const msg = data.error || data.message || "Something went wrong.";
//         console.error("Backend Error Data:", data);  // Adetailed error logging
//         throw new Error(msg);
//     }
//     return data; // If response is OK, return the parsed data
// }
