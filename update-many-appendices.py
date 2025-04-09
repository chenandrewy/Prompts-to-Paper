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

plan_name = "plan0408-piecewise"

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

    print(f"Copying latex input files to {run_folder}")
    for tex_file in glob.glob("latex-input/*.tex"):
        shutil.copy(tex_file, run_folder)
    # shutil.copy("latex-input/econstyle.sty", run_folder)
    shutil.copy("lit-context/bibtex-all.bib", run_folder)

    # argh, econstyle.sty needs to be modified for its relative path
    # I should make this more consistent throughout the codebase someday
    with open("latex-input/econstyle.sty", "r", encoding="utf-8") as f:
        econstyle_content = f.read()
    econstyle_content = econstyle_content.replace("../lit-context/", "./")
    with open(f"{run_folder}econstyle.sty", "w", encoding="utf-8") as f:
        f.write(econstyle_content)    
    
    print(f"Cleaning up response file and making {last_prompt_name}-cleaned.tex file")
    with open(response_file, "r", encoding="utf-8") as f:
        full_paper_md = f.read()
    
    # Extract LaTeX content
    i_start = full_paper_md.find("\\documentclass")
    i_end = full_paper_md.find("\\end{document}") + len("\\end{document}")
    if i_start == -1 or i_end == -1:
        print(f"Warning: Could not find LaTeX document markers in {response_file}. Skipping this folder.")
        continue
    
    full_paper_md = full_paper_md[i_start:i_end]
    
    # Update "../latex-input/" to "./"
    full_paper_md = full_paper_md.replace("../latex-input/", "./")
    
    tex_file = f"{run_folder}{last_prompt_name}-cleaned.tex"
    with open(tex_file, "w", encoding="utf-8") as f:
        f.write(full_paper_md)
    
    print(f"Compiling full paper LaTeX for {run_folder}")
    run_folder_linux = run_folder.replace("\\", "/")
    compile_result = tex_to_pdf(f"{last_prompt_name}-cleaned", run_folder_linux)
    
    if compile_result != 0:
        print(f"Warning: LaTeX compilation failed with error code {compile_result}")
        continue
    
    # Copy the PDF from the run folder to the PDF folder with special suffix
    source_pdf = f"{run_folder}{last_prompt_name}-cleaned.pdf"
    dest_pdf = f"{pdf_folder}paper-appendix-update-run{run_number}.pdf"
    
    if os.path.exists(source_pdf):
        print(f"Copying {source_pdf} to {dest_pdf}")
        shutil.copy2(source_pdf, dest_pdf)
    else:
        print(f"Warning: PDF file {source_pdf} not found. Skipping copy.")

#%%
print("\n==== All processing complete ====") 
