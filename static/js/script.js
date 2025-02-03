document.addEventListener("DOMContentLoaded", function() {
    // Handle Product form submission via AJAX
    document.getElementById("addProductForm").addEventListener("submit", function(event) {
        event.preventDefault(); // Prevent the form from submitting normally

        const productName = document.getElementById("product_name").value;

        // AJAX request to the Flask backend
        fetch('/add_product', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name: productName }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Add the new product to the form select
                const productSelect = document.querySelector("select[name='product_name']");
                const newOption = document.createElement("option");
                newOption.value = data.product_id;
                newOption.textContent = productName;
                productSelect.appendChild(newOption);

                // Close the modal and reset the form
                $('#productModal').modal('hide');
                document.getElementById("addProductForm").reset();
            } else {
                alert('Error adding product');
            }
        });
    });

    // Handle Company form submission via AJAX
    document.getElementById("addCompanyForm").addEventListener("submit", function(event) {
        event.preventDefault(); // Prevent the form from submitting normally

        const companyName = document.getElementById("company_name").value;

        // AJAX request to the Flask backend
        fetch('/add_company', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name: companyName }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Add the new company to the form select
                const companySelect = document.querySelector("select[name='company_name']");
                const newOption = document.createElement("option");
                newOption.value = data.company_id;
                newOption.textContent = companyName;
                companySelect.appendChild(newOption);

                // Close the modal and reset the form
                $('#companyModal').modal('hide');
                document.getElementById("addCompanyForm").reset();
            } else {
                alert('Error adding company');
            }
        });
    });
});