#!/usr/bin/env python3
"""
Analyze visa_request_form.pdf to extract form fields, text positions, and field names
for mapping passport data to Japanese form fields.
"""

import sys
import os
from pathlib import Path
import pdfrw
import pdfplumber
import json
from collections import defaultdict
import argparse


def analyze_pdf_fields(pdf_path):
    """Analyze PDF form fields and their properties."""
    print(f"Analyzing PDF form fields from: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    # Load PDF with pdfrw for form fields
    pdf = pdfrw.PdfReader(pdf_path)
    
    form_fields = []
    
    def get_float_value(pdf_obj, default=0.0):
        """Safely extract float value from PDF object."""
        if pdf_obj is None:
            return default
        try:
            if hasattr(pdf_obj, '__float__'):
                return float(pdf_obj)
            else:
                return float(str(pdf_obj))
        except (ValueError, TypeError):
            return default
    
    def extract_fields_from_page(page, page_num):
        """Extract form fields from a single page."""
        annotations = page.Annots
        if not annotations:
            return []
        
        page_fields = []
        
        for annotation in annotations:
            if str(annotation.Subtype) == '/Widget':
                try:
                    rect = annotation.Rect
                    x = get_float_value(rect[0]) if rect else 0.0
                    y = get_float_value(rect[1]) if rect else 0.0
                    width = get_float_value(rect[2]) - x if rect and len(rect) >= 3 else 0.0
                    height = get_float_value(rect[3]) - y if rect and len(rect) >= 4 else 0.0
                    
                    field_info = {
                        'page': page_num + 1,
                        'field_name': str(annotation.T) if annotation.T else 'Unnamed',
                        'field_type': str(annotation.FT) if annotation.FT else 'Unknown',
                        'rect': str(rect) if rect else 'None',
                        'x': x,
                        'y': y,
                        'width': width,
                        'height': height,
                        'flags': str(annotation.F) if hasattr(annotation, 'F') else 'None',
                        'value': str(annotation.V) if hasattr(annotation, 'V') else None,
                        'options': []
                    }
                
                    # Clean up field name
                    field_name = str(annotation.T) if annotation.T else 'Unnamed'
                    if hasattr(field_name, 'decode'):
                        try:
                            field_name = field_name.decode('utf-8')
                        except:
                            field_name = str(field_name)
                    
                    # Handle field type
                    field_type = str(annotation.FT) if annotation.FT else 'Unknown'
                    field_type_name = str(field_type)
                    
                    if '/Tx' in field_type:
                        field_type_name = 'Text Field'
                    elif '/Btn' in field_type:
                        field_type_name = 'Button/Checkbox'
                    elif '/Ch' in field_type:
                        field_type_name = 'Choice/Dropdown'
                    
                    field_info['field_name'] = field_name
                    field_info['field_type_name'] = field_type_name
                    
                    # Extract choice options if available
                    if '/Ch' in field_type and hasattr(annotation, 'Opt'):
                        try:
                            options = []
                            for opt in annotation.Opt:
                                if isinstance(opt, (list, tuple)) and len(opt) >= 2:
                                    option_text = str(opt[1]) if hasattr(opt[1], '__str__') else str(opt[1])
                                    options.append(option_text)
                                else:
                                    option_text = str(opt) if hasattr(opt, '__str__') else str(opt)
                                    options.append(option_text)
                            field_info['options'] = options
                        except Exception as e:
                            field_info['options'] = [f"Error: {e}"]
                    
                    page_fields.append(field_info)
                    
                except Exception as e:
                    print(f"Error processing annotation: {e}")
                    continue
        
        return page_fields
    
    # Extract fields from all pages
    for page_num, page in enumerate(pdf.pages):
        fields = extract_fields_from_page(page, page_num)
        form_fields.extend(fields)
    
    return form_fields


def analyze_pdf_fields_pypdf2(pdf_path):
    """Alternative method to analyze PDF form fields using PyPDF2."""
    print(f"Analyzing PDF form fields with PyPDF2 from: {pdf_path}")
    
    try:
        import PyPDF2
    except ImportError:
        print("PyPDF2 not available. Installing...")
        os.system("pip install PyPDF2")
        import PyPDF2
    
    form_fields = []
    
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        
        # Get form fields from the reader
        if reader.get_form_text_fields():  # Method for older PyPDF2 versions
            form_text_fields = reader.get_form_text_fields()
        else:
            try:
                form_text_fields = reader.get_form_text_fields()  # Newer method
            except:
                form_text_fields = {}
        
        for page_num, page in enumerate(reader.pages):
            # Check if form fields exist on this page
            if '/Annots' in page:
                annotations = page['/Annots']
                
                for annotation_ref in annotations:
                    annotation = annotation_ref.get_object()
                    
                    # Get field properties
                    field_name = str(annotation.get('/T', 'Unnamed'))
                    field_type = str(annotation.get('/FT', 'Unknown'))
                    
                    # Get rectangle
                    rect = annotation.get('/Rect', [0, 0, 0, 0])
                    if isinstance(rect, list) and len(rect) >= 4:
                        x, y, x2, y2 = [float(v) if v is not None else 0.0 for v in rect]
                        width = max(0, x2 - x)
                        height = max(0, y2 - y)
                    else:
                        x = y = width = height = 0.0
                    
                    # Determine field type name
                    field_type_name = 'Unknown'
                    if field_type:
                        if '/Tx' in field_type:
                            field_type_name = 'Text Field'
                        elif '/Btn' in field_type:
                            field_type_name = 'Button/Checkbox'
                        elif '/Ch' in field_type:
                            field_type_name = 'Choice/Dropdown'
                    
                    field_info = {
                        'page': page_num + 1,
                        'field_name': field_name,
                        'field_type': field_type,
                        'field_type_name': field_type_name,
                        'rect': str(rect),
                        'x': x,
                        'y': y,
                        'width': width,
                        'height': height,
                        'flags': str(annotation.get('/F', 'None')),
                        'value': str(annotation.get('/V', '')),
                        'options': []
                    }
                    
                    # Handle choice options if available
                    if '/Opt' in annotation:
                        try:
                            options = []
                            for opt in annotation['/Opt']:
                                if isinstance(opt, (list, tuple)) and len(opt) >= 2:
                                    options.append(str(opt[1]))
                                else:
                                    options.append(str(opt))
                            field_info['options'] = options
                        except Exception as e:
                            field_info['options'] = []
                    
                    form_fields.append(field_info)
    
    return form_fields


def analyze_text_positions(pdf_path):
    """Analyze text content and positions using pdfplumber."""
    print(f"Analyzing text positions from: {pdf_path}")
    
    text_elements = []
    
    def safe_float(value, default=0.0):
        """Safely convert value to float."""
        try:
            return float(value) if value is not None else default
        except (ValueError, TypeError):
            return default
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Extract text with positions
                try:
                    words = page.extract_words()
                except Exception as e:
                    print(f"Warning: Failed to extract words from page {page_num+1}: {e}")
                    words = []
                
                for word in words:
                    try:
                        x0 = safe_float(word.get('x0', 0))
                        y0 = safe_float(word.get('y0', 0))
                        x1 = safe_float(word.get('x1', 0))
                        y1 = safe_float(word.get('top', 0))
                        bottom = safe_float(word.get('bottom', 0))
                        
                        text_element = {
                            'page': page_num + 1,
                            'text': str(word.get('text', '')).strip(),
                            'x': x0,
                            'y': y0,
                            'width': max(0, x1 - x0),
                            'height': max(0, bottom - y0),
                            'x1': x1,
                            'y1': bottom
                        }
                        
                        if text_element['text']:  # Only add non-empty text
                            text_elements.append(text_element)
                            
                    except Exception as e:
                        print(f"Warning: Failed to process word {word}: {e}")
                        continue
                        
    except Exception as e:
        print(f"Error analyzing text positions with pdfplumber: {e}")
        print("Skipping text position analysis, will use form fields only")
    
    return text_elements


def generate_mapping_guide(form_fields, text_elements):
    """Generate a mapping guide for passport data to Japanese form fields."""
    
    # Common passport data fields to map
    passport_fields = [
        'first_name', 'last_name', 'middle_name',
        'date_of_birth', 'passport_number', 'issue_date',
        'expiry_date', 'issuing_country', 'nationality',
        'gender', 'place_of_birth', 'full_name'
    ]
    
    mapping_guide = {
        'passport_fields': passport_fields,
        'form_field_mapping': {}
    }
    
    # Create mapping suggestions based on field names and positions
    field_groups = defaultdict(list)
    
    for field in form_fields:
        field_name = field['field_name']
        field_groups[field['page']].append(field)
    
    for page, fields in field_groups.items():
        # Sort fields by y-position (top to bottom), then by x-position (left to right)
        fields.sort(key=lambda f: (-f['y'], f['x']))
        
        for field in fields:
            mapping_suggestion = {
                'field_name': field['field_name'],
                'field_type': field['field_type_name'],
                'position': {
                    'page': field['page'],
                    'x': field['x'],
                    'y': field['y'],
                    'width': field['width'],
                    'height': field['height']
                },
                'suggested_mapping': None,
                'nearby_text': []
            }
            
            # Find nearby text labels
            for text in text_elements:
                if text['page'] == field['page']:
                    distance = abs(text['x'] - field['x']) + abs(text['y'] - field['y'])
                    if distance < 50:  # text within 50 units of the field
                        mapping_suggestion['nearby_text'].append({
                            'text': text['text'],
                            'distance': distance,
                            'position': [text['x'], text['y']]
                        })
            
            # Sort nearby text by distance
            mapping_suggestion['nearby_text'].sort(key=lambda x: x['distance'])
            
            # Simple mapping suggestions based on keywords
            field_name_upper = str(field['field_name']).upper()
            nearby_text_upper = " ".join([t['text'] for t in mapping_suggestion['nearby_text'][:3]]).upper()
            
            # Keyword matching
            if any(keyword in field_name_upper + nearby_text_upper for keyword in ['NAME', '氏名']):
                if 'LAST' in field_name_upper or 'FAMILY' in field_name_upper or '姓' in nearby_text_upper:
                    mapping_suggestion['suggested_mapping'] = 'last_name'
                elif 'FIRST' in field_name_upper or '名' in nearby_text_upper:
                    mapping_suggestion['suggested_mapping'] = 'first_name'
                else:
                    mapping_suggestion['suggested_mapping'] = 'full_name'
            
            elif any(keyword in field_name_upper + nearby_text_upper for keyword in ['PASSPORT', '旅券']):
                mapping_suggestion['suggested_mapping'] = 'passport_number'
            
            elif any(keyword in field_name_upper + nearby_text_upper for keyword in ['BIRTH', '生年月日']):
                mapping_suggestion['suggested_mapping'] = 'date_of_birth'
            
            elif any(keyword in field_name_upper + nearby_text_upper for keyword in ['ISSUE', '発給日']):
                mapping_suggestion['suggested_mapping'] = 'issue_date'
            
            elif any(keyword in field_name_upper + nearby_text_upper for keyword in ['EXPIRY', '満了日']):
                mapping_suggestion['suggested_mapping'] = 'expiry_date'
            
            elif any(keyword in field_name_upper + nearby_text_upper for keyword in ['COUNTRY', '国籍']):
                mapping_suggestion['suggested_mapping'] = 'issuing_country'
            
            elif any(keyword in field_name_upper + nearby_text_upper for keyword in ['NATIONALITY', '国籍']):
                mapping_suggestion['suggested_mapping'] = 'nationality'
            
            elif any(keyword in field_name_upper + nearby_text_upper for keyword in ['GENDER', '性別']):
                mapping_suggestion['suggested_mapping'] = 'gender'
            
            elif any(keyword in field_name_upper + nearby_text_upper for keyword in ['PLACE', '出生地']):
                mapping_suggestion['suggested_mapping'] = 'place_of_birth'
            
            mapping_guide['form_field_mapping'][field['field_name']] = mapping_suggestion
    
    return mapping_guide


def main():
    parser = argparse.ArgumentParser(description='Analyze PDF form structure')
    parser.add_argument('--pdf', default='template_file/visa_request_form.pdf', 
                        help='Path to the PDF file to analyze')
    parser.add_argument('--output', default='visa_form_analysis.json',
                        help='Output JSON file for analysis results')
    args = parser.parse_args()
    
    pdf_path = Path(args.pdf)
    output_path = Path(args.output)
    
    try:
        # Check if required packages are installed
        try:
            import pdfrw
            import pdfplumber
        except ImportError as e:
            print(f"Missing required packages: {e}")
            print("Please install: pip install pdfrw pdfplumber")
            sys.exit(1)
        
        # Analyze form fields
        print("=== Analyzing PDF Structure ===\n")
        
        # Try pdfrw first
        try:
            form_fields = analyze_pdf_fields(str(pdf_path))
        except Exception as e:
            print(f"pdfrw failed: {e}, trying PyPDF2 fallback...")
            form_fields = analyze_pdf_fields_pypdf2(str(pdf_path))
        
        # Analyze text positions
        text_elements = analyze_text_positions(str(pdf_path))
        print(f"Found {len(text_elements)} text elements")
        
        # Generate mapping guide
        mapping_guide = generate_mapping_guide(form_fields, text_elements)
        print("Generated mapping guide")
        
        # Generate timestamp
        from datetime import datetime
        timestamp = datetime.now().isoformat()
        
        # Prepare analysis results
        analysis_results = {
            'pdf_path': str(pdf_path),
            'timestamp': timestamp,
            'form_fields': form_fields,
            'text_elements': text_elements,
            'mapping_guide': mapping_guide,
            'summary': {
                'total_form_fields': len(form_fields),
                'total_text_elements': len(text_elements),
                'field_types': list(set(f['field_type_name'] for f in form_fields)) if form_fields else [],
                'pages_with_fields': list(set(f['page'] for f in form_fields)) if form_fields else []
            }
        }
        
        # Save results
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print("\n=== ANALYSIS SUMMARY ===")
        print(f"PDF: {pdf_path}")
        print(f"Found {len(form_fields)} form fields:")
        
        field_counts = defaultdict(int)
        for field in form_fields:
            field_counts[field['field_type_name']] += 1
        
        for field_type, count in field_counts.items():
            print(f"  {field_type}: {count}")
        
        print(f"\nAnalysis saved to: {output_path}")
        
        # Print sample mappings
        print("\n=== SAMPLE FIELD MAPPINGS ===")
        for field_name, mapping in list(mapping_guide['form_field_mapping'].items())[:10]:
            print(f"Field: {field_name}")
            print(f"  Type: {mapping['field_type']}")
            print(f"  Suggested mapping: {mapping['suggested_mapping']}")
            if mapping['nearby_text']:
                nearby = mapping['nearby_text'][:2]
                texts = [t['text'] for t in nearby]
                print(f"  Nearby text: {', '.join(texts)}")
            print()
        
        if len(mapping_guide['form_field_mapping']) > 10:
            print(f"... and {len(mapping_guide['form_field_mapping']) - 10} more fields")
        
    except Exception as e:
        print(f"Error analyzing PDF: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())