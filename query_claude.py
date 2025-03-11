#%%
import os
import sys
import replicate
from dotenv import load_dotenv
import time
from markdown import markdown
import pdfkit
from datetime import datetime


# Load environment variables from .env file (if it exists)
load_dotenv()

def read_prompt_file(filename):
    """Read the content from the specified file."""
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

def query_claude(prompt, system_prompt=None):
    """Query the Claude 3.7 Sonnet model via Replicate API."""
    # Check if API token is available
    if "REPLICATE_API_TOKEN" not in os.environ:
        print("Error: REPLICATE_API_TOKEN environment variable not set.")
        print("Please set your Replicate API token in the .env file or environment variables.")
        sys.exit(1)
    
    try:
        # The model identifier for Claude 3.7 Sonnet on Replicate
        model = "anthropic/claude-3.7-sonnet"
        
        # Prepare input parameters
        input_params = {
            "prompt": prompt,
            "max_tokens": 4000,  # Adjust as needed
            "temperature": 0.5   # Lower for more deterministic output
        }
        
        # Add system prompt if provided
        if system_prompt:
            input_params["system"] = system_prompt
            print("Using system prompt...")
        
        # Run the model
        output = replicate.run(
            model,
            input=input_params
        )
        
        # Collect the output
        result = ""
        for item in output:
            result += item
            print(item, end="", flush=True)  # Stream the output
        
        return result
    
    except Exception as e:
        print(f"Error querying the model: {e}")
        sys.exit(1)

def save_response(response, output_file="claude_response.txt"):
    """Save the model's response to a file."""
    try:
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(response)
        print(f"\n\nResponse saved to {output_file}")


        # also output a pdf
        # Convert markdown to PDF
        try:            
            # Get the base name of the output file without extension
            pdf_base = os.path.splitext(output_file)[0]
            pdf_file = f"{pdf_base}.pdf"
            
            # Convert markdown to HTML
            with open(output_file, 'r', encoding='utf-8') as md_file:
                md_content = md_file.read()
            
            html_content = markdown(md_content)
            
            # Add basic styling
            styled_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Claude Response</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                    h1, h2, h3 {{ color: #333; }}
                    table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    code {{ background-color: #f5f5f5; padding: 2px 4px; border-radius: 4px; }}
                    pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto; }}
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
            temp_html = f"{pdf_base}_temp.html"
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
                
                if wkhtmltopdf_path:
                    config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
                    pdfkit.from_file(temp_html, pdf_file, configuration=config)
                else:
                    # Try with default configuration
                    pdfkit.from_file(temp_html, pdf_file)
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
            
            if os.path.exists(pdf_file):
                print(f"PDF version saved to {pdf_file}")
            
        except ImportError:
            print("PDF conversion requires additional packages. Install with:")
            print("pip install markdown pdfkit")
            print("You also need wkhtmltopdf installed: https://wkhtmltopdf.org/downloads.html")
        except Exception as e:
            print(f"Error converting to PDF: {e}")

    except Exception as e:
        print(f"Error saving response: {e}")

def main():
    # Read the prompt from prompts directory
    input_folder = "./prompts"
    input_name = "main-analysis"
    input_extension = ".txt"
    input_path = os.path.join(input_folder, input_name + input_extension)
    prompt = read_prompt_file(input_path)
    
    # Read the system prompt if it exists
    system_prompt_path = os.path.join(input_folder, "claude-system-2025-02.txt")
    system_prompt = None
    if os.path.exists(system_prompt_path):
        print(f"Reading system prompt from {system_prompt_path}...")
        system_prompt = read_prompt_file(system_prompt_path)
    
    print(f"Querying Claude 3.7 Sonnet with content from {input_path}...\n")
    
    # Query the model with the system prompt
    response = query_claude(prompt, system_prompt)
    
    # Generate timestamp for the filename
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_file = f"./responses/{input_name}_{timestamp}.md"
    
    # Save the response as markdown
    save_response(response, output_file)

    

#%%
# main
if __name__ == "__main__":
    main() 
# %%
