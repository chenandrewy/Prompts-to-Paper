#%%
# SETUP
import os
import sys
import yaml
import argparse
from utils import create_readme_appendix, create_appendix, tex_to_pdf
import shutil

# Set default plan
plan_name = "plan0403-streamlined"

#%%
# Set up output folder
temp_num, temp_name = plan_name.split("plan")[1].split("-") 
output_folder = f"./output{temp_num}-{temp_name}/"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

#%%
# Generate appendices
print("==== FEEDBACK ====")
print("Generating appendix with README...")
create_readme_appendix()

print("Generating appendix with prompt listing...")
create_appendix(plan_name + ".yaml")

#%%
# Load plan to get last prompt name
with open(f"{plan_name}.yaml", "r") as f:
    temp = yaml.safe_load(f)
prompts = temp["prompts"]
last_prompt_name = prompts[-1]['name']

#%%
# Compile full paper LaTeX
print("==== FEEDBACK ====")
print(f"Compiling full paper LaTeX")

# read in the full paper md response
with open(f"{output_folder}{last_prompt_name}-response.md", "r", encoding="utf-8") as f:
    full_paper_md = f.read()

# remove everything between \documentclass and \end{document}
i_start = full_paper_md.find("\\documentclass")
i_end = full_paper_md.find("\\end{document}") + len("\\end{document}")
full_paper_md = full_paper_md[i_start:i_end]

# save the full paper md
with open(f"{output_folder}{last_prompt_name}-cleaned.tex", "w", encoding="utf-8") as f:
    f.write(full_paper_md)

# compile the full paper
compile_result = tex_to_pdf(f"{last_prompt_name}-cleaned", output_folder)
# %%
