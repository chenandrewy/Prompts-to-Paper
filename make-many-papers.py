#%% Import required libraries
import os
import shutil
import subprocess
from datetime import datetime

# User input
num_runs = 10
plan_name = 'plan0403-streamlined'

# Extract plan number and name
temp_num, temp_name = plan_name.split("plan")[1].split("-")
print(f"Processing plan {temp_num} with name {temp_name}")

#%% Run the paper generation multiple times
for run_id in range(1, num_runs + 1):
    print(f"\n=== Starting Run {run_id} of {num_runs} ===")
    
    # Run make-paper.py and capture output
    result = subprocess.run(["python", "-u", "make-paper.py", "--plan_name", plan_name], 
                          capture_output=True, 
                          text=True,
                          encoding='utf-8')

    # Print the components of result
    print("\nProcess Results:")
    print(f"Return Code: {result.returncode}")
    print(f"Command Run: {result.args}")
    
    # Create new output folder name with run ID
    new_output_folder = f"output{temp_num}-{temp_name}-run{run_id}/"
    
    # Copy the output folder to the new location
    # might need to quit dropbox?
    import time
    time.sleep(2)
    if os.path.exists(new_output_folder):
        shutil.rmtree(new_output_folder)
    shutil.copytree(f"output{temp_num}-{temp_name}/", new_output_folder)
    
    if result.returncode != 0:
        raise RuntimeError(f"make-paper.py failed with return code {result.returncode}")
    
    print(f"Completed run {run_id}. Output saved to {new_output_folder}")

print("\nAll runs completed!") 

#%%
# copy all of the final pdfs into one folder

# copy all of the final pdfs into one folder
pdfs_folder = f"output{temp_num}-{temp_name}-pdfs"
os.makedirs(pdfs_folder, exist_ok=True)

for run_id in range(1, num_runs + 1):
    run_folder = f"output{temp_num}-{temp_name}-run{run_id}/"
    # Find all PDF files in the run folder
    for root, _, files in os.walk(run_folder):
        for file in files:
            if file.endswith('.pdf'):
                # Get the base name without extension
                base_name = os.path.splitext(file)[0]
                # Create new filename with run-id suffix
                new_filename = f"{base_name}-run{run_id}.pdf"
                # Copy the file to the PDFs folder
                shutil.copy2(
                    os.path.join(root, file),
                    os.path.join(pdfs_folder, new_filename)
                )

print(f"\nAll PDFs have been copied to {pdfs_folder}")
