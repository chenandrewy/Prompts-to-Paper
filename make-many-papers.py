#%% Import required libraries
import os
import shutil
import subprocess
from datetime import datetime

# User input
plan_name = 'plan0403-streamlined'
# plan_name = 'plan0000-test'
run_start = 1
run_end = 5

# Extract plan number and name
temp_num, temp_name = plan_name.split("plan")[1].split("-")
print(f"Processing plan {temp_num} with name {temp_name}")

# Create output directories
detail_folder = f"manyout{temp_num}-detail"
pdf_folder = f"manyout{temp_num}-pdf"
os.makedirs(detail_folder, exist_ok=True)
os.makedirs(pdf_folder, exist_ok=True)

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
    
    # Copy the output folder to the new location
    # might need to quit dropbox?
    import time
    time.sleep(2)
    if os.path.exists(run_detail_folder):
        shutil.rmtree(run_detail_folder)
    shutil.copytree(f"output{temp_num}-{temp_name}/", run_detail_folder)
    
    if result.returncode != 0:
        raise RuntimeError(f"make-paper.py failed with return code {result.returncode}")
    
    print(f"Completed run {run_id:02d}. Output saved to {run_detail_folder}")

    # Copy PDFs to pdf folder
    for root, _, files in os.walk(run_detail_folder):
        for file in files:
            if file.endswith('.pdf'):
                # Get the base name without extension
                base_name = os.path.splitext(file)[0]
                # Create new filename with run-id suffix (padded with zeros)
                new_filename = f"{base_name}-run{run_id:02d}.pdf"
                # Copy the file to the PDFs folder
                shutil.copy2(
                    os.path.join(root, file),
                    os.path.join(pdf_folder, new_filename)
                )

print("\nAll runs completed!")
print(f"All PDFs have been copied to {pdf_folder}")
print(f"All detailed outputs are in {detail_folder}")
