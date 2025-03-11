#%%
# Setup

import os
import sys
import replicate
from dotenv import load_dotenv
import time
import markdown2
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

def query_llm(prompt_name, context_names=None, prompts_folder="./prompts", input_extension=".txt", model_name="anthropic/claude-3.7-sonnet"):
    """Query the Claude model via Replicate API.
    
    Args:
        prompt_name: Name of the prompt file (without extension)
        context_names: List of context file names (without extension), or None for no context
        prompts_folder: Directory containing prompt files
        input_extension: File extension for prompt and context files
        model_name: Claude model version to use (e.g., "claude-3.7-sonnet", "claude-3.5-sonnet", etc.)
    """
    # Check if API token is available
    if "REPLICATE_API_TOKEN" not in os.environ:
        print("Error: REPLICATE_API_TOKEN environment variable not set.")
        print("Please set your Replicate API token in the .env file or environment variables.")
        sys.exit(1)
    
    try:
        # Read the prompt file
        input_path = os.path.join(prompts_folder, prompt_name + input_extension)
        prompt = read_prompt_file(input_path)
        print(f"Reading prompt from {input_path}...")
        
        # Read the contexts if specified
        combined_context = ""
        if context_names:
            # Handle both string and list inputs for backward compatibility
            if isinstance(context_names, str) and context_names != "none":
                context_names = [context_names]
            elif isinstance(context_names, str) and context_names == "none":
                context_names = []
                
            for context_name in context_names:
                context_path = os.path.join(prompts_folder, context_name + input_extension)
                if os.path.exists(context_path):
                    print(f"Reading context from {context_path}...")
                    context_content = read_prompt_file(context_path)
                    combined_context += f"--- BEGIN CONTEXT: {context_name} ---\n{context_content}\n--- END CONTEXT: {context_name} ---\n\n"

        # Read the system prompt if it exists
        system_prompt_path = os.path.join(prompts_folder, "claude-system-2025-02.txt")
        system_prompt = None
        if os.path.exists(system_prompt_path):
            print(f"Reading system prompt from {system_prompt_path}...")
            system_prompt = read_prompt_file(system_prompt_path)
        
        # The model identifier for Claude on Replicate
        model = model_name
        print(f"Using model: {model}")
        
        # Prepare the full prompt with context if provided
        full_prompt = prompt
        if combined_context:
            full_prompt = f"Here is some context:\n\n{combined_context}\n\n{prompt}"
        
        # Prepare input parameters
        input_params = {
            "prompt": full_prompt,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        # Add system prompt if provided
        if system_prompt:
            input_params["system"] = system_prompt
        
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
        
        return result, prompt_name
    
    except Exception as e:
        print(f"Error querying the model: {e}")
        # Instead of sys.exit(1), return empty values or re-raise the exception
        # Option 1: Return empty values
        return "", prompt_name
        # Option 2: Re-raise the exception (uncomment this and comment the line above)
        # raise

def save_response(response, prompt_name, use_timestamp=False, output_dir="./responses", file_ext=".md"):
    """Save the model's response to a file.
    
    Args:
        response: The text response from Claude
        prompt_name: Name of the prompt used (for filename)
        use_timestamp: Whether to add a timestamp to the filename
        output_dir: Directory to save the response
        file_ext: File extension for the output file
    """
    try:
        # Create the base output file path
        output_file = f"{output_dir}/{prompt_name}{file_ext}"
        
        # Apply timestamp to filename if requested
        if use_timestamp:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            file_base, file_ext = os.path.splitext(output_file)
            output_file = f"{file_base}_{timestamp}{file_ext}"
            
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
            
            # Convert markdown to HTML using markdown2 with table support
            with open(output_file, 'r', encoding='utf-8') as md_file:
                md_content = md_file.read()
            
            # Use markdown2 with extras for table support
            html_content = markdown2.markdown(md_content, extras=["tables", "fenced-code-blocks"])
            
            # Add basic styling with improved table styling
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
                    # Add options for better table rendering
                    options = {
                        'encoding': 'UTF-8',
                        'enable-local-file-access': None,
                        'margin-top': '20mm',
                        'margin-right': '20mm',
                        'margin-bottom': '20mm',
                        'margin-left': '20mm',
                    }
                    pdfkit.from_file(temp_html, pdf_file, configuration=config, options=options)
                else:
                    # Try with default configuration and options
                    options = {
                        'encoding': 'UTF-8',
                        'enable-local-file-access': None,
                        'margin-top': '20mm',
                        'margin-right': '20mm',
                        'margin-bottom': '20mm',
                        'margin-left': '20mm',
                    }
                    pdfkit.from_file(temp_html, pdf_file, options=options)
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
            print("pip install markdown2 pdfkit")
            print("You also need wkhtmltopdf installed: https://wkhtmltopdf.org/downloads.html")
        except Exception as e:
            print(f"Error converting to PDF: {e}")

    except Exception as e:
        print(f"Error saving response: {e}")

#%%
#  Globals

# for model list see https://replicate.com/explore

use_timestamp = False # if True, output has timestamp
model_name = "anthropic/claude-3.7-sonnet" # for actual
# model_name = "anthropic/claude-3.5-haiku" # for testing
# model_name = "meta/meta-llama-3.1-405b-instruct" # man this is not great
prompts_folder = "./prompts"
input_extension = ".txt"
max_tokens = 4000  # Adjust as needed
temperature = 0.5  # Lower for more deterministic output
        
#%%
# run main

prompt_name = "1-main-analysis"
context_names = None # use None for no context

print(f"Querying {model_name} with prompt '{prompt_name}'...\n")

# Query the model
response, used_prompt_name = query_llm(prompt_name, context_names, prompts_folder, input_extension, model_name)

# Save
save_response(response, used_prompt_name, use_timestamp)


#%% 
# run efficient markets considerations

prompt_name = "2-efficient-markets"
context_names = ["1-main-analysis"] # List of context files

print(f"Querying {model_name} with prompt '{prompt_name}'...\n")

# Query the model
response, used_prompt_name = query_llm(prompt_name, context_names, prompts_folder, input_extension, model_name)

# Save
save_response(response, used_prompt_name, use_timestamp)

#%%
# run 3-extensions

prompt_name = "3-extensions"
context_names = ["1-main-analysis", "2-efficient-markets"] # List of context files

print(f"Querying {model_name} with prompt '{prompt_name}'...\n")

# Query the model
response, used_prompt_name = query_llm(prompt_name, context_names, prompts_folder, input_extension, model_name)

# Save
save_response(response, used_prompt_name, use_timestamp)

#%%
# look for related lit

bib_files = [f for f in os.listdir("./prompts") if f.startswith("bib-") and f.endswith(".txt")]
bib_files = [f.replace('.txt', '') for f in bib_files] # Remove .txt 


prompt_name = "4-related-lit"
context_names = ["1-main-analysis"] + bib_files # List of context files

print(f"Querying {model_name} with prompt '{prompt_name}'...\n")

# Query the model
response, used_prompt_name = query_llm(prompt_name, context_names, prompts_folder, input_extension, model_name)

# Save
save_response(response, used_prompt_name, use_timestamp)

#%%
# write introduction

prompt_name = "5-introduction"
context_names = ["1-main-analysis", "2-efficient-markets", "3-extensions", "4-related-lit"] # List of context files

print(f"Querying {model_name} with prompt '{prompt_name}'...\n")

# Query the model
response, used_prompt_name = query_llm(prompt_name, context_names, prompts_folder, input_extension, model_name)

# Save
save_response(response, used_prompt_name, use_timestamp)

#%%
# write abstract

prompt_name = "6-abstract"
context_names = ["5-introduction"]

print(f"Querying {model_name} with prompt '{prompt_name}'...\n")

# Query the model
response, used_prompt_name = query_llm(prompt_name, context_names, prompts_folder, input_extension, model_name)

# Save
save_response(response, used_prompt_name, use_timestamp)

#%%
# write conclusion

prompt_name = "7-conclusion"
context_names = ["1-main-analysis", "2-efficient-markets", "3-extensions", "4-related-lit", "5-introduction", "6-abstract"]

print(f"Querying {model_name} with prompt '{prompt_name}'...\n")

# Query the model
response, used_prompt_name = query_llm(prompt_name, context_names, prompts_folder, input_extension, model_name)

# Save
save_response(response, used_prompt_name, use_timestamp)

