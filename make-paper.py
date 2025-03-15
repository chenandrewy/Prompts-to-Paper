#%%
# setup

import os
import glob
import anthropic
import subprocess
from dotenv import load_dotenv
import textwrap
import time
import re
import shutil
import argparse  
# custom functions
from utils import clean_latex_aux_files, print_wrapped, validate_arguments 

# Load environment variables (API key)
load_dotenv()

#%%
# Argument Parsing and Error Handling

# Parse command line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(description='Generate an academic paper using Claude AI')
    parser.add_argument('--model_name', type=str, default="claude-3-7-sonnet-20250219",
                        help='Model to use for generation (default: claude-3-7-sonnet-20250219)')
    parser.add_argument('--temperature', type=float, default=0.5,
                        help='Temperature for generation (default: 0.5)')
    parser.add_argument('--max-tokens', type=int, default=10000,
                        help='Maximum tokens to generate (default: 10000)')
    return parser.parse_args()


# Check if running in Jupyter notebook or as a script
def is_jupyter():
    try:
        # This will only exist in Jupyter environments
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':  # Jupyter notebook or qtconsole
            return True
        elif shell == 'TerminalInteractiveShell':  # IPython terminal
            return False
        else:
            return False
    except NameError:  # Not in an IPython environment
        return False

# Set default arguments for Jupyter notebooks
if is_jupyter():
    class DefaultArgs:
        def __init__(self):
            self.model_name = "claude-3-7-sonnet-20250219"
            self.temperature = 0.5
            self.max_tokens = 10000
    
    args = DefaultArgs()
    print("Running in Jupyter notebook with default arguments")
else:
    # Get command line arguments when running as a script
    args = parse_arguments()
    print(f"Running as script with arguments: model_name={args.model_name}, temperature={args.temperature}, max_tokens={args.max_tokens}")

# validate arguments
print("Validating arguments...")
args = validate_arguments(args)

#%%
# Functions


# Initialize Anthropic client
client = anthropic.Anthropic()

def print_wrapped(text, width=70):
    """
    Prints the input text with word wrapping while preserving paragraph breaks.
    
    Args:
        text (str): The input text to print.
        width (int, optional): Maximum width for each line. Defaults to 70.
    """
    # Create a TextWrapper instance with the desired width
    wrapper = textwrap.TextWrapper(width=width)
    
    # Split the text into paragraphs using double newlines
    paragraphs = text.split("\n\n")
    
    # Wrap and print each paragraph separately
    for para in paragraphs:
        try:
            print(wrapper.fill(para))
        except UnicodeEncodeError:
            # Handle Unicode encoding errors by replacing problematic characters
            print(wrapper.fill(para.encode('ascii', 'replace').decode('ascii')))
        # Print a blank line to preserve paragraph separation
        print()

def clean_latex_aux_files(prompt_name):
    """Clean up auxiliary files created by LaTeX."""
    aux_files = [
        f"{prompt_name}.aux",
        f"{prompt_name}.bbl",
        f"{prompt_name}.blg",
        f"{prompt_name}.out"
    ]

    for file in aux_files:
        if os.path.exists(file):
            os.remove(file)

def clean_latex_code(file_path):
    """Clean the LaTeX code to remove problematic Unicode characters."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Replace emojis and other problematic Unicode characters
    # Replace winking emoji with LaTeX-friendly alternative
    content = content.replace("😉", "\\texttt{;)}")
    
    # Add more replacements as needed for other Unicode characters
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

#%%
# create prompt

# Gather all planning*.tex files from responses directory
planning_files = glob.glob("responses/planning*.tex")

# Read content from planning files
context = ""
for file_path in planning_files:
    with open(file_path, "r") as f:
        file_content = f.read()
        file_name = os.path.basename(file_path)
        context += f"\n\n## {file_name}\n{file_content}\n\n"

# Gather all literature inputs
lit_files = glob.glob("prompts/lit-*.txt")

lit_context = ""
for file_path in lit_files:
    with open(file_path, "r", encoding="utf-8") as f:
        file_content = f.read()
        file_name = os.path.basename(file_path)
        lit_context += f"\n\n# {file_name}\n{file_content}\n\n"

# Grab latex template
with open("input-other/latex-template.txt", "r", encoding="utf-8") as f:
    latex_template = f.read()

# Read writing prompt 01 (only one for now)
with open("prompts/writing-01.txt", "r", encoding="utf-8") as f:
    instructions = f.read()

# Construct the message with better formatting for human readability
message = f"""
<BEGIN_PLANNING_DOCUMENTS>
# PLANNING DOCUMENTS
{context}
<END_PLANNING_DOCUMENTS>

<BEGIN_LITERATURE_DOCUMENTS>
# LITERATURE DOCUMENTS
{lit_context}
<END_LITERATURE_DOCUMENTS>

<BEGIN_LATEX_TEMPLATE>
# LATEX TEMPLATE
{latex_template}
<END_LATEX_TEMPLATE>

# INSTRUCTIONS
{instructions}
"""

# save to full prompt
with open('responses/full-paper-full-prompt.md', "w", encoding="utf-8") as f:
    f.write(message)


#%%
# load system prompt

with open('prompts/system-prompt-full-paper.txt', "r", encoding="utf-8") as f:
    system_prompt = f.read()

#%%
# submit

print("Sending request to Claude...")

# start timer
start_time = time.time()

# Query with streaming
with client.messages.stream(
    model=args.model_name,
    max_tokens=args.max_tokens,
    temperature=args.temperature,
    system=system_prompt,
    messages=[{
        "role": "user", 
        "content": message
    }]
) as stream:
    # Process the response as it comes in
    for text in stream.text_stream:
        # Process or display each chunk of text as it arrives
        print(text, end="", flush=True)  # For example
    
    # If you need the final complete message
    final_message = stream.get_final_message()

# end timer
end_time = time.time()
print('end claude stream---------------------------\n\n')
print(f"Time taken: {round((end_time - start_time) / 60, 2)} minutes")

# save latex code
output_file = "./latex/full_paper.tex"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(final_message.content[0].text)

# Clean the LaTeX code to handle Unicode characters
clean_latex_code(output_file)

#%% 
# clean the latex code

# remove everything before \documentclass and everything after \end{document}
with open(output_file, "r", encoding="utf-8") as f:
    lines = f.readlines()
    start_index = next((i for i, line in enumerate(lines) if r'\documentclass' in line.strip()), None)
    if start_index is not None:
        lines = lines[start_index:]
    end_index = next((i for i, line in enumerate(lines) if r'\end{document}' in line.strip()), None)
    if end_index is not None:
        lines = lines[:end_index+1]
    
# save the cleaned latex code
cleaned_output_file = "./latex/full_paper_cleaned.tex"
with open(cleaned_output_file, "w", encoding="utf-8") as f:
    f.writelines(lines)

#%%
# compile latex
# clean aux files
clean_latex_aux_files("full_paper_cleaned")

# remove pdf for safety
if os.path.exists("./latex/full_paper_cleaned.pdf"):
    os.remove("./latex/full_paper_cleaned.pdf")

# Compile with literature support
compile_command = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "-output-directory=./latex", "./latex/full_paper_cleaned.tex"]
print(f"Running first LaTeX pass: {' '.join(compile_command)}")
result = subprocess.run(compile_command, capture_output=True)
if result.returncode != 0:
    print(f"LaTeX compilation failed with code {result.returncode}")
    print("Error output:")
    print(result.stderr.decode('utf-8', errors='replace'))

# Run Biber without changing directory
biber_command = ["biber", "./latex/full_paper_cleaned"]
print(f"Running Biber: {' '.join(biber_command)}")
biber_result = subprocess.run(biber_command, capture_output=True)
if biber_result.returncode != 0:
    print(f"Biber failed with code {biber_result.returncode}")
    print("Error output:")
    print(biber_result.stderr.decode('utf-8', errors='replace'))

# Run LaTeX again (twice) to resolve references
print("Running second LaTeX pass...")
result2 = subprocess.run(compile_command, capture_output=True)
if result2.returncode != 0:
    print(f"Second LaTeX pass failed with code {result2.returncode}")
    print("Error output:")
    print(result2.stderr.decode('utf-8', errors='replace'))

print("Running final LaTeX pass...")
result3 = subprocess.run(compile_command, capture_output=True)
if result3.returncode != 0:
    print(f"Final LaTeX pass failed with code {result3.returncode}")
    print("Error output:")
    print(result3.stderr.decode('utf-8', errors='replace'))

# Store the final result for later use
final_result = result3.returncode

#%%
# copy over output

# copy latex file to responses folder
shutil.copy("./latex/full_paper_cleaned.tex", "./responses/full_paper_cleaned.tex")

# copy pdf to responses folder
if os.path.exists("./latex/full_paper_cleaned.pdf"):
    shutil.copy("./latex/full_paper_cleaned.pdf", "./responses/full_paper_cleaned.pdf")
    print("PDF saved to ./responses/full_paper_cleaned.pdf")
else:
    # copy over the log file instead
    shutil.copy("./latex/full_paper_cleaned.log", "./responses/full_paper_cleaned.log")
    print("PDF failed, copying log file instead to ./responses/full_paper_cleaned.log")

