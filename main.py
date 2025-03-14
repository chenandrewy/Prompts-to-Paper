#%%
# Runs everything.

import subprocess
import time
import numpy as np
import os
import shutil

num_papers = 2

for paper_i in range(1,num_papers+1):

    # Feedback
    print("----------------------------------------")
    print(f"Running paper {paper_i} of {num_papers}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # start timer
    start_time = time.time()

    # Run plan-paper.py first
    print("Running plan-paper.py...")
    out_plan_paper = subprocess.run(["python", "plan-paper.py"], capture_output=True, text=True)

    # Print the output
    print("STDOUT:")
    print(out_plan_paper.stdout)
    
    print("STDERR:")
    print(out_plan_paper.stderr)
    
    print(f"Return code: {out_plan_paper.returncode}")

    # Then run make-paper.py
    print("Running make-paper.py...")
    out_make_paper = subprocess.run([
        "python", "make-paper.py", 
        "--model", "claude-3-5-haiku-20241022",
        "--temperature", "1.0", 
        "--max-tokens", "4000"
    ], capture_output=True, text=True)

    # Print the output
    print("STDOUT:")
    print(out_make_paper.stdout)
    
    print("STDERR:")
    print(out_make_paper.stderr)
    
    print(f"Return code: {out_make_paper.returncode}")

    # Copy the responses folder to 1-many-responses subfolder
    # os.makedirs(f"./1-many-responses/responses-{paper_i:03}", exist_ok=True)
    shutil.copytree("./responses", f"./1-many-responses/responses-{paper_i:03}", dirs_exist_ok=True)

    # Copy full_paper_cleaned.pdf to 2-many-papers subfolder
    shutil.copy("./responses/full_paper_cleaned.pdf", f"./2-many-papers/paper-{paper_i:03}.pdf")

    # Feedback
    end_time = time.time()
    print("----------------------------------------")
    print(f"Paper {paper_i} of {num_papers} complete")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")    
    print(f"Time for paper {paper_i}: {round((end_time - start_time) / 60, 2)} minutes")    

# %%
