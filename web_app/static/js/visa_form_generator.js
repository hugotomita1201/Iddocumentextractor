/**
 * Japanese Visa Form Generator Client
 * Handles passport uploads and form generation with dynamic family member support
 */

class VisaFormGenerator {
    constructor() {
        this.members = {
            primary: { files: [], data: null }
        };
        // Initialize with empty accompanying members
        for (let i = 1; i <= 7; i++) {
            this.members[`accompanying${i}`] = { files: [], data: null };
        }
        
        this.currentMemberCount = 0;
        this.isProcessing = false;
        this.emailContent = null;
        
        this.init();
    }

    init() {
        this.setupMemberCountListener();
        // Setup primary applicant file input
        this.setupFileInput('primary');
        // Note: Generate button is set up separately at the bottom of the file
    }

    setupMemberCountListener() {
        const memberCountSelect = document.getElementById('family_member_count');
        if (memberCountSelect) {
            memberCountSelect.addEventListener('change', (e) => {
                this.currentMemberCount = parseInt(e.target.value);
                this.updateFamilyMemberSections();
                this.updateGenerateButtonState();
            });
        }
    }

    updateFamilyMemberSections() {
        const container = document.getElementById('family-members-container');
        if (!container) return;

        // Clear existing sections
        container.innerHTML = '';

        // Create sections for each family member
        for (let i = 1; i <= this.currentMemberCount; i++) {
            const memberSection = this.createFamilyMemberSection(i);
            container.appendChild(memberSection);
            
            // Setup file input for this member
            this.setupFileInput(`accompanying${i}`);
        }
    }

    createFamilyMemberSection(memberNumber) {
        const section = document.createElement('div');
        section.className = 'member-upload';
        section.id = `member${memberNumber}-section`;
        
        const japaneseNumber = this.getJapaneseNumber(memberNumber);
        
        section.innerHTML = `
            <h3>Accompanying Family Member ${memberNumber} (同行家族${japaneseNumber})</h3>
            <div class="upload-area">
                <label for="member${memberNumber}-passport">Upload FM${memberNumber} Passport:</label>
                <input type="file" id="member${memberNumber}-passport" class="member-file" accept="image/png, image/jpeg, image/jpg" multiple>
                <div class="preview-zone" id="member${memberNumber}-preview">
                    <p>No passport uploaded yet</p>
                </div>
                <div class="extracted-data" id="member${memberNumber}-data" style="display: none;">
                    <h4>Extracted Information:</h4>
                    <div class="data-display"></div>
                </div>
            </div>
        `;
        
        return section;
    }

    getJapaneseNumber(num) {
        const japaneseNumbers = ['一', '二', '三', '四', '五', '六', '七'];
        return japaneseNumbers[num - 1] || num.toString();
    }

    setupFileInput(memberType) {
        // Determine the input ID based on member type
        let inputId;
        if (memberType === 'primary') {
            inputId = 'primary-passport';
        } else {
            const memberNum = memberType.replace('accompanying', '');
            inputId = `member${memberNum}-passport`;
        }

        // Use setTimeout to ensure DOM is ready
        setTimeout(() => {
            const fileInput = document.getElementById(inputId);
            if (fileInput) {
                // Remove any existing listeners
                const newInput = fileInput.cloneNode(true);
                fileInput.parentNode.replaceChild(newInput, fileInput);
                
                // Add new listener
                newInput.addEventListener('change', (e) => {
                    console.log(`File upload detected for ${memberType}:`, e.target.files);
                    this.handleFileUpload(memberType, e.target.files);
                });
            } else {
                console.error(`File input not found: ${inputId}`);
            }
        }, 100);
    }

    getMemberTypeFromId(inputId) {
        if (inputId.includes('primary')) return 'primary';
        
        // Extract member number from ID like "member3-passport"
        const match = inputId.match(/member(\d+)-passport/);
        if (match) {
            return `accompanying${match[1]}`;
        }
        
        return 'primary';
    }

    getPreviewId(memberType) {
        if (memberType === 'primary') return 'primary';
        
        // Extract number from accompanying1, accompanying2, etc.
        const match = memberType.match(/accompanying(\d+)/);
        if (match) {
            return `member${match[1]}`;
        }
        
        return 'primary';
    }

    handleFileUpload(memberType, files) {
        console.log(`handleFileUpload called for ${memberType}`, files);
        if (!files || files.length === 0) {
            console.log('No files provided');
            return;
        }
        
        this.members[memberType].files = Array.from(files);
        console.log(`Files stored for ${memberType}:`, this.members[memberType].files);
        this.displayPreviews(memberType);
        this.extractPassportData(memberType);
    }

    displayPreviews(memberType) {
        const previewId = this.getPreviewId(memberType);
        const previewElement = document.getElementById(`${previewId}-preview`);
        const files = this.members[memberType].files;
        
        if (!previewElement) return;

        if (files.length > 0) {
            previewElement.innerHTML = `<div class="visa-images">${files.map((f, index) => `
                <div class="visa-image">
                    <img src="${URL.createObjectURL(f)}" alt="${f.name}" onclick="window.open(this.src)">
                    <span class="file-name">${f.name}</span>
                    <button class="remove-image" onclick="visaForm.removeImage('${memberType}', ${index})">×</button>
                </div>
            `).join('')}</div>`;
            previewElement.className = 'preview-zone has-images';
        } else {
            previewElement.innerHTML = '<p>No passport uploaded yet</p>';
            previewElement.className = 'preview-zone';
        }
    }

    async extractPassportData(memberType) {
        console.log(`extractPassportData called for ${memberType}`);
        const files = this.members[memberType].files;
        if (!files.length) {
            console.log('No files to extract');
            return;
        }

        const previewId = this.getPreviewId(memberType);
        const dataElement = document.getElementById(`${previewId}-data`);
        if (!dataElement) {
            console.error(`Data element not found for ${previewId}-data`);
            return;
        }

        dataElement.style.display = 'block';
        
        // Show loading message
        const displayElement = dataElement.querySelector('.data-display');
        if (displayElement) {
            displayElement.innerHTML = '<div class="loading">Extracting passport data...</div>';
        }
        
        try {
            const formData = new FormData();
            formData.append('doc_type', 'US Passport');
            files.forEach(file => formData.append('file', file));

            console.log(`Sending extraction request for ${memberType}`);
            const response = await fetch('/extract', {
                method: 'POST',
                body: formData
            });
            
            console.log(`Response received for ${memberType}:`, response.status);
            const result = await response.json();
            console.log(`Extraction result for ${memberType}:`, result);
            
            if (result.length > 0 && !result[0].error) {
                this.members[memberType].data = result[0];
                this.displayExtractedData(memberType, result[0]);
            } else {
                throw new Error(result[0]?.error || 'Failed to extract data');
            }
        } catch (error) {
            console.error(`Extraction error for ${memberType}:`, error);
            if (displayElement) {
                displayElement.innerHTML = `
                    <div class="error-message">Error: ${error.message}</div>
                `;
            }
        }
    }

    displayExtractedData(memberType, data) {
        const previewId = this.getPreviewId(memberType);
        const dataElement = document.getElementById(`${previewId}-data`);
        const displayElement = dataElement.querySelector('.data-display');
        
        displayElement.innerHTML = '';
        
        const fields = [
            { key: 'surname', label: 'Surname' },
            { key: 'given_names', label: 'Given Names' },
            { key: 'passport_number', label: 'Passport Number' },
            { key: 'date_of_birth', label: 'Date of Birth' },
            { key: 'nationality', label: 'Nationality' },
            { key: 'date_of_expiration', label: 'Expiration Date' },
            { key: 'issuing_authority', label: 'Issuing Authority' }
        ];

        fields.forEach(field => {
            const div = document.createElement('div');
            div.className = 'data-item';
            div.innerHTML = `
                <strong>${field.label}:</strong>
                <span>${data[field.key] || 'N/A'}</span>
            `;
            displayElement.appendChild(div);
        });

        this.updateGenerateButtonState();
    }

    removeImage(memberType, index) {
        this.members[memberType].files.splice(index, 1);
        this.displayPreviews(memberType);
        
        if (this.members[memberType].files.length === 0) {
            const previewId = this.getPreviewId(memberType);
            const dataElement = document.getElementById(`${previewId}-data`);
            if (dataElement) dataElement.style.display = 'none';
            this.members[memberType].data = null;
        }
        
        this.updateGenerateButtonState();
    }

    updateGenerateButtonState() {
        const generateBtn = document.getElementById('generate-forms');
        if (!generateBtn) return;

        // Always require primary applicant
        const hasPrimaryData = this.members.primary.data !== null;
        
        // Check if all visible family members have data
        let allFamilyMembersReady = true;
        for (let i = 1; i <= this.currentMemberCount; i++) {
            if (!this.members[`accompanying${i}`].data) {
                allFamilyMembersReady = false;
                break;
            }
        }

        const isReady = hasPrimaryData && allFamilyMembersReady;
        generateBtn.disabled = !isReady;
        
        if (!hasPrimaryData) {
            generateBtn.textContent = 'Upload primary applicant passport first';
        } else if (!allFamilyMembersReady && this.currentMemberCount > 0) {
            generateBtn.textContent = 'Upload all family member passports';
        } else {
            generateBtn.textContent = 'Generate Visa Application Forms';
        }
    }

    async generateForms() {
        if (this.isProcessing) return;

        const generateBtn = document.getElementById('generate-forms');
        const loadingContainer = document.getElementById('loading-container');
        const resultsContainer = document.getElementById('results-container');

        try {
            this.isProcessing = true;
            
            if (generateBtn) generateBtn.disabled = true;
            if (loadingContainer) {
                loadingContainer.style.display = 'block';
                resultsContainer.style.display = 'none';
            }

            // Prepare member data
            const memberData = {};
            
            // Always include primary
            if (this.members.primary.data) {
                memberData.primary = this.members.primary.data;
            }
            
            // Include family members based on current count
            for (let i = 1; i <= this.currentMemberCount; i++) {
                const memberKey = `accompanying${i}`;
                if (this.members[memberKey].data) {
                    memberData[memberKey] = this.members[memberKey].data;
                }
            }

            // Call backend to generate forms
            const response = await fetch('/api/generate-japanese-forms', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    members: memberData,
                    form_type: 'japanese_visa_family',
                    member_count: this.currentMemberCount + 1 // +1 for primary
                })
            });

            const result = await response.json();

            if (result.success) {
                // Store email content
                this.emailContent = {
                    subject: result.email_subject,
                    body: result.email_body
                };
                this.displayResults(result);
            } else {
                throw new Error(result.error || 'Failed to generate forms');
            }

        } catch (error) {
            console.error('Generation error:', error);
            this.showError(error.message);
        } finally {
            this.isProcessing = false;
            if (loadingContainer) loadingContainer.style.display = 'none';
            this.updateGenerateButtonState();
        }
    }

    displayResults(result) {
        const resultsContainer = document.getElementById('results-container');
        const pdfDownload = document.getElementById('pdf-download');
        const wordDownload = document.getElementById('word-download');

        if (!resultsContainer) return;

        if (pdfDownload) pdfDownload.href = result.pdf_path;
        if (wordDownload) wordDownload.href = result.word_path;

        resultsContainer.style.display = 'block';
    }

    showError(message) {
        const resultsContainer = document.getElementById('results-container');
        if (resultsContainer) {
            resultsContainer.style.display = 'block';
            resultsContainer.innerHTML = `
                <div class="error-message">
                    <h3>Error</h3>
                    <p>${message}</p>
                </div>
            `;
        }
    }

    createEmailDraft() {
        if (!this.emailContent) {
            console.error('No email content available');
            alert('Please generate the forms first before creating an email draft.');
            return;
        }

        console.log('Creating email draft with content:', this.emailContent);

        try {
            // Encode subject and body for mailto link
            const subject = encodeURIComponent(this.emailContent.subject);
            const body = encodeURIComponent(this.emailContent.body);
            
            // Create mailto link
            const mailtoLink = `mailto:?subject=${subject}&body=${body}`;
            
            console.log('Mailto link length:', mailtoLink.length);
            
            // Check if the mailto link is too long (some browsers have limits)
            if (mailtoLink.length > 2000) {
                console.warn('Email content might be too long for some email clients');
            }
            
            // Try to open in a new window first (better for some browsers)
            const mailWindow = window.open(mailtoLink, '_blank');
            
            // If that fails, try changing location
            if (!mailWindow) {
                window.location.href = mailtoLink;
            }
            
            // Show instructions
            const instructionsElement = document.getElementById('email-instructions');
            if (instructionsElement) {
                instructionsElement.style.display = 'block';
                instructionsElement.innerHTML = `
                    <p><strong>Email draft created!</strong></p>
                    <p>If your email client didn't open automatically:</p>
                    <ol>
                        <li>Check if you have a default email client set up</li>
                        <li>Copy the information from the generated Word document</li>
                        <li>Create a new email manually in Outlook</li>
                    </ol>
                    <p>Remember to attach the passport images before sending.</p>
                `;
                
                // Hide instructions after 15 seconds
                setTimeout(() => {
                    instructionsElement.style.display = 'none';
                }, 15000);
            }
            
            // Also provide a fallback - copy to clipboard option
            this.addCopyToClipboardOption();
            
        } catch (error) {
            console.error('Error creating email draft:', error);
            alert('Failed to create email draft. Please check the console for details.');
        }
    }
    
    addCopyToClipboardOption() {
        const instructionsElement = document.getElementById('email-instructions');
        if (!instructionsElement || !this.emailContent) return;
        
        // Add a copy button
        const copyButton = document.createElement('button');
        copyButton.className = 'btn-primary';
        copyButton.style.marginTop = '10px';
        copyButton.style.padding = '0.5rem 1rem';
        copyButton.textContent = 'Copy Email Content to Clipboard';
        
        copyButton.onclick = async () => {
            const emailText = `Subject: ${this.emailContent.subject}\n\n${this.emailContent.body}`;
            
            try {
                await navigator.clipboard.writeText(emailText);
                copyButton.textContent = 'Copied!';
                setTimeout(() => {
                    copyButton.textContent = 'Copy Email Content to Clipboard';
                }, 2000);
            } catch (err) {
                console.error('Failed to copy text:', err);
                alert('Failed to copy to clipboard. Please use the Word document instead.');
            }
        };
        
        instructionsElement.appendChild(copyButton);
    }
}

// Initialize the form generator when DOM loads
document.addEventListener('DOMContentLoaded', function() {
    window.visaForm = new VisaFormGenerator();
    
    // Setup generate button listener
    const generateBtn = document.getElementById('generate-forms');
    if (generateBtn) {
        generateBtn.addEventListener('click', () => {
            window.visaForm.generateForms();
        });
    }
    
    // Setup email draft button listener
    const emailBtn = document.getElementById('email-draft');
    if (emailBtn) {
        emailBtn.addEventListener('click', () => {
            window.visaForm.createEmailDraft();
        });
    }
});