#%% Import required libraries

import os
import shutil
import subprocess
from datetime import datetime
import time
import yaml
import sys

# User input
plan_name = 'plan0408-piecewise'
# plan_name = 'plan0407-piecewise'
# plan_name = 'plan0403-streamlined'
# plan_name = 'plan0000-test'
run_start = 1
run_end = 3

# Extract plan number and name
temp_num, temp_name = plan_name.split("plan")[1].split("-")
print(f"Processing plan {temp_num} with name {temp_name}")


# Create output directories
detail_folder = f"manyout{temp_num}-detail"
pdf_folder = f"manyout{temp_num}-pdf"
os.makedirs(detail_folder, exist_ok=True)
os.makedirs(pdf_folder, exist_ok=True)

#%%
# Check with user before running

# Read run range from YAML file for display purposes
yaml_file = f"{plan_name}.yaml"
with open(yaml_file, 'r') as file:
    plan_config = yaml.safe_load(file)
print(f"\nMany Runs Setting:")
print(f"run_start: {run_start}")
print(f"run_end: {run_end}")

print(f"\nPlan Details:")
print(f"  Plan Name: {plan_name}")
print(f"  Plan Start: {plan_config['config']['run_range']['start']}")
print(f"  Plan End: {plan_config['config']['run_range']['end']}")
print(f"\nOutput will be saved to:")
print(f"  Detail folder: {detail_folder}")
print(f"  PDF folder: {pdf_folder}")

user_input = input("\nPress Enter to continue or 'q' to quit: ")
if user_input.lower() == 'q':
    print("Operation cancelled by user.")
    sys.exit(0)

print("\nProceeding with paper generation...")

#%% Run the paper generation multiple times
for run_id in range(run_start, run_end + 1):
    print(f"\n=== Starting Run {run_id:02d} of {run_end} ===")
    
    # Run make-paper.py and capture output
    result = subprocess.run(["python", "-u", "make-paper.py", "--plan_name", plan_name], 
                          capture_output=True, 
                          text=True,
                          encoding='utf-8')

    # Print the components of result
    print("\nProcess Results:")
    print(f"Return Code: {result.returncode}")
    print(f"Command Run: {result.args}")
    
    # Create new output folder name with run ID (padded with zeros)
    run_detail_folder = os.path.join(detail_folder, f"run{run_id:02d}")

    # pause to allow dropbox sync
    time.sleep(30)    

    if os.path.exists(run_detail_folder):
        shutil.rmtree(run_detail_folder)
    shutil.copytree(f"output{temp_num}-{temp_name}/", run_detail_folder)
    
    if result.returncode != 0:
        raise RuntimeError(f"make-paper.py failed with return code {result.returncode}")
    
    print(f"Completed run {run_id:02d}. Output saved to {run_detail_folder}")

#%% Copy PDFs to output folder
# Copy PDFs from all runs to the pdf folder
for run_id in range(run_start, run_end + 1):
    run_detail_folder = os.path.join(detail_folder, f"run{run_id:02d}")
    for root, _, files in os.walk(run_detail_folder):
        for file in files:
            if 'full-paper-cleaned' in file and file.endswith('.pdf'):
                # Copy over with short name and run-id suffix (padded with zeros)
                new_filename = f"paper-run{run_id:02d}.pdf"
                # Copy the file to the PDFs folder
                shutil.copy2(
                    os.path.join(root, file),
                    os.path.join(pdf_folder, new_filename)
                )

print("\nAll runs completed!")
print(f"All PDFs have been copied to {pdf_folder}")
print(f"All detailed outputs are in {detail_folder}")
