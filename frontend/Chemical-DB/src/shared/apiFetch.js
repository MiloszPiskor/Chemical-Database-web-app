import { oktaAuth } from './oktaConfig'; // or pass it in as a param if needed
// import OpenAI from 'openai';

// const openai = new OpenAI({
//     apiKey: import.meta.env.VITE_OPENAI_API_KEY, // or use process.env if server-side
//     dangerouslyAllowBrowser: true 
//   });

export async function apiFetch(endpoint, method = 'GET', body = null) {
    const token = await oktaAuth.tokenManager.get('accessToken');
    if (!token) throw new Error('No token available');
    
    const headers = {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token.accessToken}`,
    };

    const options = {
        method,
        headers,
    };

    if (body) options.body = JSON.stringify(body);

    const response = await fetch(`${import.meta.env.VITE_DATABASE_URL}${endpoint}`, options);
    const data = await response.json();
    console.log(data)

    if (!response.ok) {
        const msg = data.error || data.message || 'Something went wrong';
        console.error('API Error:', data);
        throw new Error(msg);
    }

    return data;
}

// export async function apiFetchProductInfo(product) {

//     if (!product || !product.name) {
//         return "Invalid product data. Cannot generate summary.";
//     }

//     try{

//     const response = await openai.responses.create({

//         model:"gpt-3.5-turbo",
//         input: [
//             {
//                 role: "system",
//                 content: "You are a helpful assistant providing short summaries of industrial chemical products.",
//               },
//             {
//                 role: "user",
//                 content: `Summarize the industrial chemical product: ${product.name} in 2-3 sentences for a product info section.
//                 Focus on use cases and safety. You may greet website users first, as their assistant providing information
//                 about this product.`
//             }
//         ],
//         temperature: 0.7, // For a bit more creative answers
//     });

//     return response.choices[0]?.message?.content ?? "No summary returned.";

//     } catch (error) {
//         console.error("Failed to fetch GPT summary:", error);
//         return "Sorry, no product summary is available at the moment.";
//     }
// }


