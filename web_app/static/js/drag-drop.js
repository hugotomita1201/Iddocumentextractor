// Enhanced drag and drop with folder support
class DragDropUploader {
    constructor() {
        this.files = [];
        this.totalSize = 0;
        this.uploadedSize = 0;
        this.initializeDropzone();
        this.setupEventListeners();
    }

    initializeDropzone() {
        // Configure Dropzone without auto-upload
        Dropzone.autoDiscover = false;

        // Set up Dropzone with minimal configuration
        this.dropzone = new Dropzone("#drag-drop-area", {
            url: '/extract',
            autoProcessQueue: false,
            uploadMultiple: true,
            parallelUploads: 10,
            maxFilesize: 50,
            acceptedFiles: 'image/*',
            addRemoveLinks: false,
            clickable: true,
            createImageThumbnails: false,
            previewTemplate: '<div style="display: none;"></div>'
        });
        
        // Instead of using Dropzone events, we'll use our custom drag-drop handlers
        
        // Set up Dropzone to accept files without processing them
        this.dropzone.on("addedfile", (file) => {
            console.log('Dropzone added file:', file.name);
            if (file && file.type && file.type.startsWith('image/')) {
                this.addFiles([file]);
                this.dropzone.removeFile(file);
            }
        });
    }


    setupEventListeners() {
        // Manual drop handlers for enhanced folder support
        const dropArea = document.getElementById('drag-drop-area');

        dropArea.addEventListener('dragenter', this.handleDragIn.bind(this));
        dropArea.addEventListener('dragover', this.handleDragOver.bind(this));
        dropArea.addEventListener('dragleave', this.handleDragOut.bind(this));
        dropArea.addEventListener('drop', this.handleDrop.bind(this));

        // Button click
        document.getElementById('extract-button').addEventListener('click', this.startExtraction.bind(this));
    }

    handleDragIn(e) {
        e.preventDefault();
        e.stopPropagation();
        document.getElementById('drag-drop-area').classList.add('dragover');
    }

    handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    handleDragOut(e) {
        e.preventDefault();
        e.stopPropagation();
        if (!e.currentTarget.contains(e.relatedTarget)) {
            document.getElementById('drag-drop-area').classList.remove('dragover');
        }
    }

    async handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();

        const dropArea = document.getElementById('drag-drop-area');
        dropArea.classList.remove('dragover');

        const items = e.dataTransfer.items;
        const newFiles = [];

        for (let i = 0; i < items.length; i++) {
            const item = items[i];

            if (item.kind === 'file') {
                const entry = item.webkitGetAsEntry();
                if (entry) {
                    await this.traverseFileTree(entry, newFiles);
                } else {
                    const file = item.getAsFile();
                    if (file && file.type.startsWith('image/')) {
                        newFiles.push(file);
                    }
                }
            }
        }

        this.addFiles(newFiles);
        console.log('handleDrop completed with newFiles:', newFiles);
    }

    async traverseFileTree(entry, files, path = "") {
        if (entry.isFile && entry.name.match(/\.(jpe?g|png)$/i)) {
            try {
                const file = await this.getFileFromEntry(entry);
                if (file) files.push(file);
            } catch (error) {
                console.warn('Could not read file:', entry.name, error);
            }
        } else if (entry.isDirectory) {
            const dirReader = entry.createReader();
            try {
                const entries = await new Promise((resolve, reject) => {
                    dirReader.readEntries(resolve, reject);
                });

                for (const subEntry of entries) {
                    await this.traverseFileTree(subEntry, files, path + entry.name + "/");
                }
            } catch (error) {
                console.warn('Could not read directory:', entry.name, error);
            }
        }
    }

    getFileFromEntry(entry) {
        return new Promise((resolve, reject) => {
            entry.file(resolve, reject);
        });
    }

    addFiles(newFiles) {
        console.log('Adding files:', newFiles);
        if (newFiles.length === 0) {
            alert('No image files found in the selected location.');
            return;
        }

        // Filter out duplicates
        const existingNames = this.files.map(f => f.name);
        const uniqueFiles = newFiles.filter(f => !existingNames.includes(f.name));

        this.files.push(...uniqueFiles);
        console.log('Final files:', this.files);
        this.fileListUpdated();
    }

    fileListUpdated() {
        console.log('fileListUpdated called with files:', this.files);
        this.renderFileList();
        this.updateExtractButton();
        // Removed clearDropFiles to prevent clearing our file list
    }

    renderFileList() {
        console.log('renderFileList called');
        const fileList = document.getElementById('file-list');
        const uploadedFiles = document.getElementById('uploaded-files');

        if (this.files.length === 0) {
            uploadedFiles.style.display = 'none';
            return;
        }

        uploadedFiles.style.display = 'block';
        fileList.innerHTML = '';

        this.files.forEach((file, index) => {
            const li = document.createElement('li');
            li.innerHTML = `
                <span>${file.name}</span>
                <span class="file-size">${this.formatFileSize(file.size)}</span>
                <button type="button" onclick="dragDropUploader.removeFile(${index})" style="background: none; border: none; color: #dc3545; cursor: pointer;">×</button>
            `;
            fileList.appendChild(li);
        });
    }

    removeFile(index) {
        this.files.splice(index, 1);
        this.fileListUpdated();
    }

    clearDropFiles() {
        if (this.dropzone) {
            this.dropzone.files.forEach(file => {
                this.dropzone.removeFile(file);
            });
        }
    }

    formatFileSize(bytes) {
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        if (bytes === 0) return '0 Bytes';
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return parseFloat((bytes / Math.pow(1024, i)).toFixed(2)) + ' ' + sizes[i];
    }

    updateExtractButton() {
        const button = document.getElementById('extract-button');
        if (button) {
            button.disabled = this.files.length === 0;
            console.log('Extract button updated: enabled =', !button.disabled);
        } else {
            console.error('Extract button not found');
        }
    }

    async startExtraction() {
        if (this.files.length === 0) return;

        const button = document.getElementById('extract-button');
        const progressContainer = document.getElementById('progress-container');
        const resultsContainer = document.getElementById('results-container');

        button.disabled = true;
        button.textContent = 'Extracting...';
        button.classList.add('generating');
        progressContainer.style.display = 'block';
        resultsContainer.innerHTML = '<p>Processing files... Please wait.</p>';

        const docType = document.getElementById('doc_type').value;
        const formData = new FormData();

        formData.append('doc_type', docType);
        this.files.forEach(file => {
            formData.append('file', file);
        });

        try {
            const response = await fetch('/extract', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Handle both single and array responses
            const results = Array.isArray(data) ? data : [data];

            this.displayDragDropResults(results);
            this.showDownloadButtons(results);

        } catch (error) {
            console.error('Error:', error);
            resultsContainer.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
        } finally {
            button.disabled = false;
            button.textContent = 'Extract Information';
            button.classList.remove('generating');
            progressContainer.style.display = 'none';

            // Clear files after extraction
            this.files = [];
            this.fileListUpdated();
        }
    }

    displayDragDropResults(data) {
        const resultsContainer = document.getElementById('results-container');

        if (!data || data.length === 0) {
            resultsContainer.innerHTML = '<p>No data extracted from files.</p>';
            return;
        }

        const validData = data.filter(item => !item.error && item);

        if (validData.length === 0) {
            resultsContainer.innerHTML = '<p>All files failed to process.</p>';
            return;
        }

        let html = `
            <div class="results-summary">
                <p>Successfully processed ${validData.length} of ${data.length} files</p>
            </div>
            <div class="results-list">
        `;

        data.forEach((item, index) => {
            const fileName = item.file_name || item.filename || `File ${index + 1}`;
            
            if (item.error) {
                html += `
                    <div class="error-card">
                        <h3>${fileName} - Error</h3>
                        <p><strong>Error:</strong> ${item.error}</p>
                    </div>
                `;
            } else {
                html += `
                    <div class="result-card">
                        <h3>${fileName}</h3>
                        <div class="result-details">
                `;
                
                // List each field vertically
                Object.entries(item).forEach(([key, value]) => {
                    if (value !== undefined && value !== null && value !== '') {
                        html += `
                            <div class="result-item">
                                <strong>${this.formatHeader(key)}:</strong>
                                <span>${value}</span>
                            </div>
                        `;
                    }
                });
                
                html += `
                        </div>
                    </div>
                `;
            }
        });

        html += `</div>`;
        resultsContainer.innerHTML = html;
    }

    formatHeader(key) {
        return key
            .replace(/_/g, ' ')
            .replace(/\b\w/g, l => l.toUpperCase())
            .replace(/\bId\b/g, 'ID')
            .replace(/\bApi\b/g, 'API');
    }

    showDownloadButtons(data) {
        const downloadExcel = document.getElementById('download-excel');
        const downloadCsv = document.getElementById('download-csv');

        if (data && data.length > 0) {
            downloadExcel.style.display = 'inline-block';
            downloadCsv.style.display = 'inline-block';

            downloadExcel.onclick = () => this.downloadFile(data, 'excel');
            downloadCsv.onclick = () => this.downloadFile(data, 'csv');
        }
    }

    downloadFile(data, format) {
        if (!Array.isArray(data)) data = [data];

        const headers = Object.keys(data[0] || {});
        let content = '';

        if (format === 'csv') {
            content = headers.join(',') + '\n';
            data.forEach(row => {
                const values = headers.map(header => {
                    const val = row[header] || '';
                    return typeof val === 'string' ? `"${val.replace(/"/g, '""')}"` : val;
                });
                content += values.join(',') + '\n';
            });
        } else {
            content = headers.join(',') + '\n';
            data.forEach(row => {
                const values = headers.map(header => row[header] || '');
                content += values.join(',') + '\n';
            });
        }

        const blob = new Blob([content], { type: format === 'csv' ? 'text/csv' : 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `extracted_data.${format === 'csv' ? 'csv' : 'txt'}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
}

// Global instance
let dragDropUploader;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    dragDropUploader = new DragDropUploader();
});