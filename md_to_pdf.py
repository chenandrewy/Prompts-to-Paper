#!/usr/bin/env python3
"""
md_to_pdf.py - A script to convert Markdown files to PDF format.

This script:
1. Allows the user to select a Markdown file through command-line arguments or a file dialog
2. Converts the selected Markdown file to PDF using markdown2 and pdfkit
3. Saves the PDF in the same directory as the original file or a specified output location

Usage:
    python md_to_pdf.py [input_file] [output_file]
    
    If no input_file is provided, a file dialog will open to select one.
    If no output_file is provided, the PDF will be saved with the same name as the input file.

Requirements:
    - Python packages: markdown2, pdfkit, tkinter
    - wkhtmltopdf installed on your system
"""

import os
import sys
import argparse
from tkinter import Tk, filedialog
import markdown2
import pdfkit
from datetime import datetime

def select_file_dialog():
    """Open a file dialog to select a Markdown file."""
    root = Tk()
    root.withdraw()  # Hide the main window
    file_path = filedialog.askopenfilename(
        title="Select Markdown File",
        filetypes=[("Markdown Files", "*.md"), ("All Files", "*.*")]
    )
    root.destroy()
    return file_path

def get_default_output_path(input_path):
    """Generate default output path by replacing .md extension with .pdf"""
    base_path = os.path.splitext(input_path)[0]
    return f"{base_path}.pdf"

def convert_md_to_pdf(input_path, output_path=None):
    """Convert Markdown file to PDF using markdown2 and pdfkit."""
    if not output_path:
        output_path = get_default_output_path(input_path)
    
    # Get the base name of the output file without extension for temp files
    pdf_base = os.path.splitext(output_path)[0]
    temp_html = f"{pdf_base}_temp.html"
    
    try:
        print(f"Converting {input_path} to PDF...")
        
        # Read the markdown content
        with open(input_path, 'r', encoding='utf-8') as md_file:
            md_content = md_file.read()
        
        # Convert markdown to HTML using markdown2 with extras
        html_content = markdown2.markdown(md_content, extras=["tables", "fenced-code-blocks"])
        
        # Add styling for better appearance
        styled_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Markdown to PDF</title>
            <script type="text/javascript" id="MathJax-script" async
                src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js">
            </script>
            <script>
                window.MathJax = {{
                    tex: {{
                        inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
                        displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
                        processEscapes: true
                    }}
                }};
            </script>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                h1, h2, h3 {{ color: #333; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                code {{ background-color: #f5f5f5; padding: 2px 4px; border-radius: 4px; }}
                pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto; }}
                
                /* Table styling for better rendering */
                table {{ table-layout: fixed; }}
                td, th {{ word-wrap: break-word; }}
            </style>
        </head>
        <body>
            {html_content}
            <div style="margin-top: 30px; font-size: 0.8em; color: #666;">
                Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            </div>
        </body>
        </html>
        """
        
        # Create a temporary HTML file
        with open(temp_html, 'w', encoding='utf-8') as html_file:
            html_file.write(styled_html)
        
        # Try to find wkhtmltopdf in common installation locations
        wkhtmltopdf_path = None
        possible_paths = [
            r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe',
            r'C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe',
            # Add more potential paths if needed
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                wkhtmltopdf_path = path
                break
        
        # PDF conversion options
        options = {
            'encoding': 'UTF-8',
            'enable-local-file-access': None,
            'margin-top': '20mm',
            'margin-right': '20mm',
            'margin-bottom': '20mm',
            'margin-left': '20mm',
            'javascript-delay': 1000,  # Wait for MathJax to render (in milliseconds)
            'no-stop-slow-scripts': None,  # Don't stop slow running JavaScript
        }
        
        # Convert HTML to PDF
        if wkhtmltopdf_path:
            config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
            pdfkit.from_file(temp_html, output_path, configuration=config, options=options)
        else:
            # Try with default configuration
            pdfkit.from_file(temp_html, output_path, options=options)
        
        # Clean up temporary file
        if os.path.exists(temp_html):
            os.remove(temp_html)
        
        print(f"Conversion successful! PDF saved to: {output_path}")
        return True
    
    except Exception as e:
        print(f"Error during conversion: {e}")
        
        if "wkhtmltopdf" in str(e).lower():
            print("\nTo fix this issue:")
            print("1. Install wkhtmltopdf from https://wkhtmltopdf.org/downloads.html")
            print("2. Make sure wkhtmltopdf is added to your PATH")
            print("   or specify its location in the script")
        
        # Clean up temporary file if it exists
        if os.path.exists(temp_html):
            os.remove(temp_html)
        
        return False

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Convert Markdown files to PDF")
    parser.add_argument("input_file", nargs="?", help="Path to the input Markdown file")
    parser.add_argument("output_file", nargs="?", help="Path for the output PDF file")
    args = parser.parse_args()
    
    # Get input file path
    input_path = args.input_file
    if not input_path:
        print("No input file specified. Opening file selection dialog...")
        input_path = select_file_dialog()
        if not input_path:
            print("No file selected. Exiting.")
            return
    
    # Validate input file
    if not os.path.exists(input_path):
        print(f"Error: Input file '{input_path}' does not exist.")
        return
    
    if not input_path.lower().endswith('.md'):
        print(f"Warning: '{input_path}' does not have a .md extension. Continuing anyway.")
    
    # Get output file path
    output_path = args.output_file
    if not output_path:
        output_path = get_default_output_path(input_path)
    
    # Convert the file
    convert_md_to_pdf(input_path, output_path)

if __name__ == "__main__":
    main() 