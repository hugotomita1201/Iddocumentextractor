#!/usr/bin/env python3
"""
Generate a simple mapping guide from the analysis results
"""

import json
import os

def generate_field_mapping_guide():
    """Generate a user-friendly mapping guide"""
    
    with open('visa_form_analysis.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("=" * 60)
    print("JAPANESE VISA FORM FIELD MAPPING GUIDE")
    print("=" * 60)
    print(f"PDF analyzed: {data['pdf_path']}")
    print(f"Total form fields: {data['summary']['total_form_fields']}")
    print(f"Datatype: {', '.join(data['summary']['field_types'])}")
    print()
    
    print("FIELD POSITION MAPPING:")
    print("-" * 40)
    
    # Let's manually map based on typical Japanese visa form layout
    # and Japanese text labels found in the text elements
    
    field_mappings = []
    
    for field in data['form_fields']:
        field_info = {
            'field_id': field['field_name'],
            'type': field['field_type_name'],
            'x': field['x'],
            'y': field['y'],
            'width': field['width'],
            'height': field['height'],
            'passport_data_key': None,
            'description': None
        }
        
        # Manual mapping based on typical Japanese visa field positioning
        y = float(field['y'])
        
        # These mappings are based on typical Japanese visa form layouts
        # and the field positions in the analysis
        
        # Name fields (usually at the top)
        if 590 <= y <= 610:
            field_info['passport_data_key'] = 'primary_last_name'
            field_info['description'] = 'Primary applicant LAST name'
        elif 575 <= y <= 595:
            field_info['passport_data_key'] = 'primary_first_name'
            field_info['description'] = 'Primary applicant FIRST name'
        elif 560 <= y <= 580:
            field_info['passport_data_key'] = 'primary_middle_name'
            field_info['description'] = 'Primary applicant MIDDLE name'
        elif 505 <= y <= 525:
            field_info['passport_data_key'] = 'primary_passport_number'
            field_info['description'] = 'Primary applicant passport number'
        elif 490 <= y <= 510:
            field_info['passport_data_key'] = 'primary_date_of_birth'
            field_info['description'] = 'Primary applicant date of birth (YYYY-MM-DD)'
        elif 475 <= y <= 495:
            field_info['passport_data_key'] = 'primary_nationality'
            field_info['description'] = 'Primary applicant nationality'
    
    sorted_fields = sorted(field_mappings, key=lambda x: x['y'], reverse=True)
    
    print("FIELD MAPPINGS FOR PASSPORT DATA:")
    print()
    
    passport_data_template = {
        "primary_last_name": "",
        "primary_first_name": "",
        "primary_middle_name": "",
        "primary_passport_number": "",
        "primary_date_of_birth": "",
        "primary_nationality": "",
        "primary_issue_date": "",
        "primary_expiry_date": "",
        "primary_place_of_birth": "",
        "primary_issuing_country": ""
    }
    
    print("Suggested passport data structure:")
    for key, value in passport_data_template.items():
        print(f"  {key}: '{value}'")
    
    print()
    print("MAP THESE TO FORM FIELDS:")
    for field in data['form_fields']:
        print(f"  Field: {field['field_name']} (at x:{field['x']:.0f}, y:{field['y']:.0f})")
        print(f"    Position: ({field['x']:.0f}, {field['y']:.0f}) -> ({field['x']+field['width']:.0f}, {field['y']+field['height']:.0f})")
        print(f"    Type: {field['field_type_name']}")
        print()
    
    # Create usage template
    usage_template = """
# USAGE EXAMPLE FOR FORM FILLING:

import json

# Load your passport data
passport_data = {
    "primary_first_name": "JOHN",
    "primary_last_name": "SMITH",
    "primary_middle_name": "MICHAEL",
    "primary_passport_number": "A12345678",
    "primary_date_of_birth": "1990-05-15",
    "primary_nationality": "AMERICAN",
    "primary_issuing_country": "UNITED STATES"
}

# Map to form fields
field_mapping = {}
for field in data['form_fields']:
    field_name = field['field_name']
    # ... your mapping logic here ...
    """
    
    print("USAGE TEMPLATE:")
    print(usage_template)

if __name__ == "__main__":
    if os.path.exists('visa_form_analysis.json'):
        generate_field_mapping_guide()
    else:
        print("Run analyze_visa_form.py first to generate the analysis file")