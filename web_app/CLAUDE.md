# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Flask-based web application that extracts data from passport and identity documents using Google's Gemini AI and generates Japanese visa application forms. The app processes uploaded images, extracts structured data, and can generate filled PDF and Word documents for visa applications.

## Architecture

### Core Components

1. **Main Application (`app.py`)**
   - Flask server with CORS enabled
   - Gemini AI integration for document OCR
   - Routes: `/` (main page), `/extract` (document processing)
   - Environment-based configuration using python-dotenv

2. **API Endpoints (`modules/api_endpoints.py`)**
   - `/visa-form` - Visa form generator UI
   - `/api/generate-japanese-forms` - Generate filled visa forms from passport data
   - `/api/download/<format>/<job_id>` - Download generated PDFs/Word docs

3. **PDF Generation (`modules/pdf_generator.py`)**
   - `JapaneseFormGenerator` class handles form generation
   - Fills existing PDF templates using pikepdf
   - Generates Word documents as fallback
   - Creates email content for visa applications

4. **Frontend Components**
   - `static/js/visa_form_generator.js` - Handles UI for visa form generation
   - `static/js/drag-drop.js` - Drag-and-drop file upload functionality
   - `templates/visa_form.html` - Visa form generator page
   - `templates/index.html` - Main passport extraction page

### Data Flow

1. User uploads passport/ID images via drag-and-drop interface
2. Images are processed by Gemini AI to extract structured data
3. For visa forms: extracted data is mapped to Japanese form fields
4. PDF template is filled with mapped data using pikepdf
5. Alternative Word document and email content are generated
6. Files are saved to `generated_forms/` directory

## Common Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
echo "GEMINI_API_KEY=your_api_key_here" > .env

# Run development server
python app.py

# Run production server (Heroku/Render deployment)
gunicorn app:app

# Test document extraction
curl -X POST http://localhost:5000/extract \
  -F "file=@passport.jpg" \
  -F "doc_type=US Passport"

# Test visa form generation
curl -X POST http://localhost:5000/api/generate-japanese-forms \
  -H "Content-Type: application/json" \
  -d '{"members": {"primary": {...passport_data...}}}'
```

## Configuration

### Environment Variables
- `GEMINI_API_KEY` - Google Gemini API key (required)
- `PORT` - Server port (default: 5000)

### PDF Field Mapping
- `pdf_config/visa_form_mapping.json` - Maps passport fields to PDF form fields
- Supports primary applicant + up to 7 accompanying family members
- Each member has fields: `full_name_japanese_order`, `passport_number`, `date_of_birth`

### Supported Document Types
- US Passport
- Japanese Passport  
- US Driver's License
- US Permanent Resident Card

## File Structure

- `generated_forms/` - Output directory for generated visa forms
- `template_file/` - PDF templates for form filling
- `pdf_config/` - Configuration files for PDF field mappings
- `modules/` - Core business logic modules
- `utils/` - Utility scripts for analysis and mapping

## Important Notes

- The application requires a valid Gemini API key to function
- Generated forms are stored locally and should be cleaned up periodically
- PDF template must exist at `template_file/visa_request_form.pdf`
- All dates are converted to Japanese format (YYYY年MM月DD日)
- Names are formatted in Japanese order (surname first, uppercase)