"""
Enhanced API endpoints for Japanese visa form generation
Works with existing API key from app.py
"""

from flask import request, jsonify, send_file, render_template
import os
import uuid
from datetime import datetime, timedelta
import json

def register_routes(app):
    """Register new API routes"""
    
    # Ensure directories exist
    if not os.path.exists('generated_forms'):
        os.makedirs('generated_forms')
    
    @app.route('/visa-form')
    def visa_form_page():
        """Render the Japanese visa form generator"""
        return render_template('visa_form.html')

    @app.route('/api/generate-japanese-forms', methods=['POST'])
    def generate_japanese_forms():
        """
        Generate Japanese visa application forms from passport data
        
        Expected JSON:
        {
            "members": {
                "primary": {...},
                "accompanying1": {...},
                "accompanying2": {...},
                ... up to accompanying7
            },
            "form_type": "japanese_visa_family",
            "member_count": 3  // Total number including primary
        }
        """
        try:
            data = request.get_json()
            members_data = data.get('members', {})
            form_type = data.get('form_type', 'japanese_visa_family')
            
            if not members_data:
                return jsonify({"error": "No member data provided"}), 400

            # Filter out empty member data
            valid_members = {}
            for member_key, member_data in members_data.items():
                if member_data and isinstance(member_data, dict):
                    valid_members[member_key] = member_data
            
            if not valid_members:
                return jsonify({"error": "No valid member data provided"}), 400

            # Generate forms using shared model from app.py
            from modules.pdf_generator import generate_japanese_forms_from_passports
            result = generate_japanese_forms_from_passports(valid_members)
            
            # Create temporary download links
            job_id = str(uuid.uuid4())
            
            return jsonify({
                "success": True,
                "job_id": job_id,
                "pdf_path": f"/api/download/pdf/{job_id}",
                "word_path": f"/api/download/word/{job_id}",
                "email_subject": result.get("email_subject", ""),
                "email_body": result.get("email_body", ""),
                "members_processed": result["members_processed"]
            })

        except Exception as e:
            print(f"Error generating forms: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/download/<format>/<job_id>')
    def download_generated_form(format, job_id):
        """Download generated form in specified format"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            search_dir = 'generated_forms'
            files = []
            
            if os.path.exists(search_dir):
                for file in os.listdir(search_dir):
                    if format == 'pdf' and file.endswith('.pdf'):
                        files.append(file)
                    elif format == 'word' and file.endswith('.docx'):
                        files.append(file)
            
            if files:
                latest_file = sorted(files)[-1]
                file_path = os.path.join(search_dir, latest_file)
                
                if format == 'pdf':
                    mimetype = 'application/pdf'
                    filename = f'japanese_visa_application_{timestamp}.pdf'
                else:  # word/docx
                    mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                    filename = f'japanese_visa_application_{timestamp}.docx'
                
                if os.path.exists(file_path):
                    return send_file(file_path, 
                                   as_attachment=True, 
                                   download_name=filename,
                                   mimetype=mimetype)
                else:
                    return jsonify({"error": "Generated file not found"}), 404
            else:
                return jsonify({"error": "No generated files found"}), 404

        except Exception as e:
            return jsonify({"error": f"Download failed: {str(e)}"}), 500