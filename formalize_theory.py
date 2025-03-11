#%%
#!/usr/bin/env python3
"""
formalize_theory.py - A script to convert the analysis from a markdown file 
to a more formal mathematical theory using the DeepSeek R1 model via Replicate API.

This script:
1. Reads the content from responses/1-main-analysis.md
2. Sends the content to DeepSeek R1 via Replicate API for formalization
3. Saves the formalized theory to responses/1-main-analysis-formalized_{timestamp}.md

Usage:
    python formalize_theory.py

Requirements:
    - Replicate API token in .env file (REPLICATE_API_TOKEN)
    - Python packages: replicate, python-dotenv
"""

import os
import replicate
from dotenv import load_dotenv
import datetime

# Load environment variables (for API key)
load_dotenv()

def read_markdown_file(file_path):
    """Read the content from a markdown file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def query_deepseek_r1_via_replicate(content):
    """
    Query the DeepSeek R1 model via Replicate API to formalize the content into mathematical theory.
    """
    # Construct the prompt for mathematical formalization
    prompt = """You are an expert in mathematical formalism. 
Convert the following analysis into a rigorous mathematical theory with formal definitions, 
theorems, and proofs where applicable:

{}""".format(content)
    
    try:
        # Run the model inference using DeepSeek R1
        output = replicate.run(
            "deepseek-ai/deepseek-r1",  # Correct model identifier for DeepSeek R1
            input={
                "prompt": prompt,
                "temperature": 0.2,  # Lower temperature for more formal/deterministic output
                "max_tokens": 8192
            }
        )
        
        # Replicate typically returns an iterator for streaming responses
        # Collect all parts of the response
        response_text = ""
        for item in output:
            response_text += item
            
        return response_text
    
    except Exception as e:
        print(f"Error during Replicate API request: {e}")
        return None

def save_formalized_theory(formalized_content, output_file):
    """Save the formalized theory to a markdown file."""
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(formalized_content)
    print(f"Formalized theory saved to {output_file}")

def main():
    # File paths
    input_file = "responses/1-main-analysis.md"
    
    # Add timestamp to output filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"responses/1-main-analysis-formalized_{timestamp}.md"
    
    # The Replicate API token is automatically used from environment variables via the replicate package
    if not os.getenv("REPLICATE_API_TOKEN"):
        print("Error: REPLICATE_API_TOKEN environment variable not found.")
        print("Please ensure it's set in your .env file.")
        return
    
    # Read the content from the input file
    print(f"Reading content from {input_file}...")
    content = read_markdown_file(input_file)
    
    # Query the DeepSeek R1 model via Replicate
    print("Querying DeepSeek R1 via Replicate API for formalization...")
    formalized_content = query_deepseek_r1_via_replicate(content)
    
    if formalized_content:
        # Save the formalized theory
        save_formalized_theory(formalized_content, output_file)
        print(f"Success! Formalized theory saved to {output_file}")
    else:
        print("Failed to generate formalized theory.")

if __name__ == "__main__":
    main() 