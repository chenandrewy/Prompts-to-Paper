#!/usr/bin/env python
# update-many-appendices.py
# Script to update appendices and recompile all full paper tex files in a given manyoutput*-detail folder,
# then update all the PDFs in the corresponding manyoutput*-pdf folder

#%%
# SETUP
import os
import sys
import yaml
import argparse
import glob
import re
from utils import create_readme_appendix, create_appendix, tex_to_pdf
import shutil

plan_name = "plan0403-streamlined"

#%%
# Update appendices once for all output folders
print("\n==== Updating Appendices ====")
print("Generating appendix with README...")
create_readme_appendix()

print("Generating appendix with prompt listing...")
create_appendix(plan_name + ".yaml")
print("Appendices updated successfully.")

#%%
# Prepare for loop

# Find all manyoutput*-detail folders

temp_num, temp_name = plan_name.split("plan")[1].split("-")
detail_folder = f"./manyout{temp_num}-detail/"
pdf_folder = f"./manyout{temp_num}-pdf/"

# Create PDF folder if it doesn't exist
if not os.path.exists(pdf_folder):
    os.makedirs(pdf_folder)

run_folders = glob.glob(detail_folder + "/run*/")

# Find the last prompt name from the plan
with open(f"{plan_name}.yaml", "r") as f:
    temp = yaml.safe_load(f)
prompts = temp["prompts"]
last_prompt_name = prompts[-1]['name']

#%%
# Process each run folder
for run_folder in run_folders:
    print(f"\n==== Processing folder: {run_folder} ====")
    
    # Extract run number from folder name
    run_match = re.search(r'run(\d+)', run_folder)
    if not run_match:
        print(f"Warning: Could not extract run number from {run_folder}. Skipping this folder.")
        continue
    
    run_number = run_match.group(1)
    
    # Check if the response file exists
    response_file = f"{run_folder}{last_prompt_name}-response.md"
    if not os.path.exists(response_file):
        print(f"Warning: Response file {response_file} not found. Skipping this folder.")
        continue
    
    # Compile full paper LaTeX
    print(f"Compiling full paper LaTeX")
    
    # Read in the full paper md response
    with open(response_file, "r", encoding="utf-8") as f:
        full_paper_md = f.read()
    
    # Extract LaTeX content
    i_start = full_paper_md.find("\\documentclass")
    i_end = full_paper_md.find("\\end{document}") + len("\\end{document}")
    if i_start == -1 or i_end == -1:
        print(f"Warning: Could not find LaTeX document markers in {response_file}. Skipping this folder.")
        continue
    
    full_paper_md = full_paper_md[i_start:i_end]
    
    # Save the full paper tex
    tex_file = f"{run_folder}{last_prompt_name}-cleaned.tex"
    with open(tex_file, "w", encoding="utf-8") as f:
        f.write(full_paper_md)
    
    # Create temp directory if it doesn't exist
    temp_dir = "./temp/"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    # Copy the tex file to temp directory
    temp_tex_file = f"{temp_dir}{last_prompt_name}-cleaned.tex"
    shutil.copy2(tex_file, temp_tex_file)
    
    # Compile the full paper in temp directory
    compile_result = tex_to_pdf(f"{last_prompt_name}-cleaned", temp_dir)
    
    if compile_result != 0:
        print(f"Warning: LaTeX compilation failed with error code {compile_result}")
        continue
    
    # Copy the PDF from temp to the PDF folder with run suffix
    source_pdf = f"{temp_dir}{last_prompt_name}-cleaned.pdf"
    dest_pdf = f"{pdf_folder}{last_prompt_name}-cleaned-run{run_number}.pdf"
    
    if os.path.exists(source_pdf):
        print(f"Copying {source_pdf} to {dest_pdf}")
        shutil.copy2(source_pdf, dest_pdf)
    else:
        print(f"Warning: PDF file {source_pdf} not found. Skipping copy.")

#%%
print("\n==== All processing complete ====") 
