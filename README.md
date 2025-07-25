# ID Document Extractor

This project is a Flask web application designed to extract structured data from images of various identity documents using the Google Gemini API. It supports different document types, including US Passports, Japanese Passports, US Driver's Licenses, and US Permanent Resident Cards.

## Features

*   **Image Upload:** Users can upload images of supported identity documents.
*   **Gemini API Integration:** Leverages the Google Gemini 1.5 Flash model for advanced image analysis and data extraction.
*   **Structured Data Output:** Extracts key information into a clean JSON format.
*   **Multiple Document Types:** Pre-configured prompts for various document types to ensure accurate extraction.
*   **Responsive Web Interface:** A simple and intuitive web interface for document upload and data display.

## Technologies Used

*   **Backend:** Python 3.x, Flask
*   **AI/ML:** Google Gemini API (via `google-generativeai` library)
*   **Image Processing:** Pillow (PIL)
*   **Environment Management:** `python-dotenv`
*   **Web Server:** Gunicorn
*   **Frontend:** HTML, CSS, JavaScript

## Setup and Installation

Follow these steps to get the project up and running on your local machine.

### 1. Clone the Repository

```bash
git clone https://github.com/hugotomita1201/Iddocumentextractor.git
cd Iddocumentextractor
```

### 2. Set up a Python Virtual Environment

It's highly recommended to use a virtual environment to manage project dependencies.

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

### 3. Install Dependencies

Install the required Python packages using `pip`:

```bash
pip install -r requirements.txt
pip install -r web_app/requirements.txt
```

### 4. Configure Google Gemini API Key

You need a Google Gemini API key to use the application.

1.  Go to [Google AI Studio](https://aistudio.google.com/) and generate a new API key.
2.  Create a file named `.env` inside the `web_app/` directory (e.g., `Iddocumentextractor/web_app/.env`).
3.  Add your API key to this file in the following format:

    ```
    GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"
    ```
    Replace `YOUR_GEMINI_API_KEY_HERE` with the actual API key you obtained.

### 5. Run the Application

Navigate to the `web_app` directory and start the Flask application using Gunicorn:

```bash
cd web_app
gunicorn --bind 0.0.0.0:8000 app:app
```

The application will be accessible at `http://0.0.0.0:8000` or `http://localhost:8000` in your web browser.

## Usage

1.  Open your web browser and go to `http://localhost:8000`.
2.  Select the type of document you want to process from the dropdown menu.
3.  Click "Choose File" to upload an image of the document.
4.  Click "Extract Data" to send the image to the Gemini API for analysis.
5.  The extracted structured data will be displayed on the page.

## Contributing

Contributions are welcome! If you have suggestions for improvements or new features, please open an issue or submit a pull request.

## License

[Optional: Add your license information here, e.g., MIT License]
