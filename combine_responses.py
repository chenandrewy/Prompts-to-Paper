#%%
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import markdown2
import pdfkit
from datetime import datetime

def natural_sort_key(s):
    """
    Sort strings that contain numbers in a natural way.
    For example: ["1-main", "2-efficient", "10-conclusion"] instead of ["1-main", "10-conclusion", "2-efficient"]
    """
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def combine_markdown_files(responses_dir="./responses", output_file="combined_paper.md", file_order=None):
    """
    Reads markdown files in the responses directory and combines them in the order specified by file_order
    """
    # Get all markdown files
    md_files = [f for f in os.listdir(responses_dir) if f.endswith('.md')]
    
    # Filter out any temporary files or other non-response files
    response_files = [f for f in md_files if re.match(r'^\d+-', f)]
    
    print(f"Found {len(response_files)} markdown files in total:")
    for file in response_files:
        print(f"  - {file}")
    
    # Create ordered list of files based on file_order patterns
    ordered_files = []
    
    if file_order:
        # For each pattern in file_order, find matching files
        for pattern in file_order:
            matching_files = [f for f in response_files if f.startswith(pattern)]
            if matching_files:
                # Sort matching files naturally if there are multiple matches
                matching_files.sort(key=natural_sort_key)
                ordered_files.extend(matching_files)
                print(f"Found {len(matching_files)} files matching pattern '{pattern}'")
    else:
        # If no file_order provided, sort all files naturally
        ordered_files = sorted(response_files, key=natural_sort_key)
    
    # Check if any files were not included in the ordered list
    unordered_files = [f for f in response_files if f not in ordered_files]
    if unordered_files:
        print(f"\nWarning: {len(unordered_files)} files were not included in the ordered list:")
        for file in unordered_files:
            print(f"  - {file}")
    
    print(f"\nFiles will be combined in this order:")
    for file in ordered_files:
        print(f"  - {file}")
    
    # Start with the title
    combined_content = "# Hedging the Singularity\n\n"
    
    # Read and append each file in the specified order
    for file in ordered_files:
        file_path = os.path.join(responses_dir, file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                combined_content += f"\n\n{content}"
                print(f"Added content from {file}")
        except Exception as e:
            print(f"Error reading {file}: {e}")
    
    # Write the combined content to a new file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(combined_content)
    
    print(f"\nCombined content saved to {output_file}")
    return output_file

def convert_to_pdf(md_file, pdf_file=None):
    """
    Converts a markdown file to PDF using the same approach as in main.py
    """
    if pdf_file is None:
        pdf_file = os.path.splitext(md_file)[0] + ".pdf"
    
    try:
        # Read the markdown content
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Convert markdown to HTML with extras for table support
        html_content = markdown2.markdown(md_content, extras=["tables", "fenced-code-blocks"])
        
        # Add styling
        styled_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Hedging the Singularity</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                h1, h2, h3 {{ color: #333; }}
                h1 {{ text-align: center; font-size: 24pt; margin-bottom: 40px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                code {{ background-color: #f5f5f5; padding: 2px 4px; border-radius: 4px; }}
                pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto; }}
                
                /* Additional table styling for better rendering */
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
        temp_html = f"{os.path.splitext(pdf_file)[0]}_temp.html"
        with open(temp_html, 'w', encoding='utf-8') as html_file:
            html_file.write(styled_html)
        
        # Check if wkhtmltopdf is installed and configure pdfkit
        try:
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
            
            # PDF options
            options = {
                'encoding': 'UTF-8',
                'enable-local-file-access': None,
                'margin-top': '20mm',
                'margin-right': '20mm',
                'margin-bottom': '20mm',
                'margin-left': '20mm',
                'page-size': 'Letter',
            }
            
            if wkhtmltopdf_path:
                config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
                pdfkit.from_file(temp_html, pdf_file, configuration=config, options=options)
            else:
                # Try with default configuration
                pdfkit.from_file(temp_html, pdf_file, options=options)
                
            print(f"PDF version saved to {pdf_file}")
            
        except Exception as pdf_error:
            print(f"PDF conversion error: {pdf_error}")
            print("\nTo fix this issue:")
            print("1. Install wkhtmltopdf from https://wkhtmltopdf.org/downloads.html")
            print("2. Make sure wkhtmltopdf is added to your PATH")
            print("   or specify its location in the script")
            print("\nSkipping PDF generation. Markdown file was saved successfully.")
        
        # Remove temporary HTML file if it exists
        if os.path.exists(temp_html):
            os.remove(temp_html)
            
    except ImportError:
        print("PDF conversion requires additional packages. Install with:")
        print("pip install markdown2 pdfkit")
        print("You also need wkhtmltopdf installed: https://wkhtmltopdf.org/downloads.html")
    except Exception as e:
        print(f"Error converting to PDF: {e}")

def main():
    """Main function to combine markdown files and convert to PDF"""
    output_md = "hedging_the_singularity.md"
    output_pdf = "hedging_the_singularity.pdf"

    # file order
    file_order = ["6-abstract", "5-introduction", "1-main-analysis", "2-efficient-markets", "3-extensions", "7-conclusion", "4-related-lit"]

    # Combine markdown files
    combined_md = combine_markdown_files(output_file=output_md, file_order=file_order)
    
    # Convert to PDF
    convert_to_pdf(combined_md, output_pdf)
    
    print("\nProcess completed!")

if __name__ == "__main__":
    main() 