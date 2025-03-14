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
from utils import clean_latex_aux_files, print_wrapped  # Import utility functions

# Load environment variables (API key)
load_dotenv()

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

# Gather all bibliography inputs
bib_files = glob.glob("prompts/bib*.txt")

bib_context = ""
for file_path in bib_files:
    with open(file_path, "r", encoding="utf-8") as f:
        file_content = f.read()
        file_name = os.path.basename(file_path)
        bib_context += f"\n\n## {file_name}\n{file_content}\n\n"

# Grab latex template
with open("input-other/latex-template.txt", "r", encoding="utf-8") as f:
    latex_template = f.read()

instructions = """
Write a short, roughly 10 page academic paper titled "Hedging the AI Singularity" based on the following planning and bibliography documents. 

At the end of the abstract write "Unlike previous work, all text in this paper is generated by an LLM."

Make sure all citations match actual papers in the bibliography documents. Output as a latex document with complete bibliography. Output only the latex code, no other text. The latex code is intended for compiling, assuming that bib-99-bibtex.bib is in the relative path ../input-other/.

Use 1 in margins, 12 pt font, 1.5 line spacing. Omit the date.
"""

# Construct the message with better formatting for human readability
message = f"""
<BEGIN_PLANNING_DOCUMENTS>
# PLANNING DOCUMENTS
{context}
<END_PLANNING_DOCUMENTS>

<BEGIN_BIBLIOGRAPHY_DOCUMENTS>
# BIBLIOGRAPHY DOCUMENTS
{bib_context}
<END_BIBLIOGRAPHY_DOCUMENTS>

<BEGIN_LATEX_TEMPLATE>
# LATEX TEMPLATE
{latex_template}
<END_LATEX_TEMPLATE>

# INSTRUCTIONS
{instructions}
"""

# save to temp folder
with open('temp/message.md', "w", encoding="utf-8") as f:
    f.write(message)

#%%
# submit

print("Sending request to Claude...")

# start timer
start_time = time.time()

# Query with streaming
with client.messages.stream(
    model="claude-3-7-sonnet-20250219",
    max_tokens=500*20,
    temperature=0.5,
    messages=[
        {"role": "user", "content": message}
    ]
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
with open("./latex/full_paper.tex", "w", encoding="utf-8") as f:
    f.write(final_message.content[0].text)

#%% 
# clean the latex code

# remove everything before \documentclass and everything after \end{document}
with open("./latex/full_paper.tex", "r", encoding="utf-8") as f:
    lines = f.readlines()
    start_index = next((i for i, line in enumerate(lines) if r'\documentclass' in line.strip()), None)
    if start_index is not None:
        lines = lines[start_index:]
    end_index = next((i for i, line in enumerate(lines) if r'\end{document}' in line.strip()), None)
    if end_index is not None:
        lines = lines[:end_index+1]
    
# save the cleaned latex code
with open("./latex/full_paper_cleaned.tex", "w", encoding="utf-8") as f:
    f.writelines(lines)



#%%
# compile latex

# clean aux files
clean_latex_aux_files("full_paper_cleaned")

# Compile with bibliography support
compile_command = f"pdflatex -interaction=nonstopmode -halt-on-error -output-directory=./latex ./latex/full_paper_cleaned.tex"
print(f"Running first LaTeX pass: {compile_command}")
os.system(compile_command)

# Run Biber without changing directory
biber_command = f"biber ./latex/full_paper_cleaned"
print(f"Running Biber: {biber_command}")
os.system(biber_command)

# Run LaTeX again (twice) to resolve references
print("Running second LaTeX pass...")
os.system(compile_command)

print("Running final LaTeX pass...")
result = os.system(compile_command)

# copy pdf to responses folder
shutil.copy("./latex/full_paper_cleaned.pdf", "./responses/full_paper_cleaned.pdf")