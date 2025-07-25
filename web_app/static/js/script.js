document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('upload-form');
    const resultsContainer = document.getElementById('results-container');
    const downloadExcelButton = document.getElementById('download-excel');
    const downloadCsvButton = document.getElementById('download-csv');
    const imagePreviewContainer = document.getElementById('image-preview-container');
    const imagePreview = document.getElementById('image-preview');
    const fileInput = document.getElementById('file');
    let extractedData = null;

    fileInput.addEventListener('change', function() {
        const file = this.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                imagePreview.src = e.target.result;
                imagePreviewContainer.style.display = 'block';
            }
            reader.readAsDataURL(file);
        } else {
            imagePreview.src = '#';
            imagePreviewContainer.style.display = 'none';
        }
    });

    uploadForm.addEventListener('submit', function(event) {
        event.preventDefault();

        const formData = new FormData(uploadForm);
        const file = fileInput.files[0];

        if (!file) {
            alert('Please select a file to upload.');
            return;
        }

        resultsContainer.innerHTML = '<p>Extracting data... Please wait.</p>';

        fetch('/extract', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                resultsContainer.innerHTML = `<p style="color: red;">Error: ${data.error}</p>`;
                downloadExcelButton.style.display = 'none';
                downloadCsvButton.style.display = 'none';
            } else {
                extractedData = data;
                displayResults(data);
                downloadExcelButton.style.display = 'inline-block';
                downloadCsvButton.style.display = 'inline-block';
            }
        })
        .catch(error => {
            resultsContainer.innerHTML = `<p style="color: red;">An unexpected error occurred: ${error}</p>`;
            downloadExcelButton.style.display = 'none';
            downloadCsvButton.style.display = 'none';
        });
    });

    function displayResults(data) {
        let html = '<ul>';
        for (const key in data) {
            html += `<li><strong>${key}:</strong> ${data[key]}</li>`;
        }
        html += '</ul>';
        resultsContainer.innerHTML = html;
    }

    downloadExcelButton.addEventListener('click', function() {
        if (extractedData) {
            downloadFile([extractedData], 'excel');
        }
    });

    downloadCsvButton.addEventListener('click', function() {
        if (extractedData) {
            downloadFile([extractedData], 'csv');
        }
    });

    function downloadFile(data, format) {
        const a = document.createElement('a');
        const blob = new Blob([convertToFormat(data, format)], {type: format === 'excel' ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' : 'text/csv'});
        const url = URL.createObjectURL(blob);
        a.href = url;
        a.download = `extracted_data.${format === 'excel' ? 'xlsx' : 'csv'}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    function convertToFormat(data, format) {
        if (format === 'csv') {
            const headers = Object.keys(data[0]);
            let csv = headers.join(',') + '\n';
            data.forEach(row => {
                const values = headers.map(header => row[header]);
                csv += values.join(',') + '\n';
            });
            return csv;
        } else if (format === 'excel') {
            // This is a simplified representation. For a real Excel file, 
            // you would need a library like SheetJS on the client-side or generate it on the server.
            // For this example, we'll just generate a CSV with an .xlsx extension.
            const headers = Object.keys(data[0]);
            let csv = headers.join(',') + '\n';
            data.forEach(row => {
                const values = headers.map(header => row[header]);
                csv += values.join(',') + '\n';
            });
            return csv;
        }
    }
});