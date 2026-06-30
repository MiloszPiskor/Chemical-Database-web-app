const buildQueryString = (formData) => {

    const conversionTable = {
        productId: "product_id",
        companyId: "company_id",
        start: "start",
        end: "end",
        start2: "start2",
        end2: "end2",
        limit: "limit",
    }

    const filteredEntries = Object.entries(formData)
    .filter(([_, v]) => v != "")
    .map(([k, v]) => [conversionTable[k], v]);

    const queryString = filteredEntries
    .map(([k , v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
    .join("&")
    
    const toQueryString = queryString ? `?${queryString}` : ""

    return toQueryString
}

export default buildQueryString;