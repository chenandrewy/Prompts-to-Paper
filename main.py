#%%
# Runs everything.

import subprocess
import time
import numpy as np
import os
import shutil

num_papers = 10

for paper_i in range(1,num_papers+1):

    # Feedback
    start_time = time.time()
    print("----------------------------------------")
    print(f"Running paper {paper_i} of {num_papers}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Delete all files in ./responses/ and ./latex/
    try:
        for file in os.listdir("./responses"):
            os.remove(os.path.join("./responses", file))
        for file in os.listdir("./latex"):
            os.remove(os.path.join("./latex", file))
    except Exception as e:
        print("Warning: Could not clean up ./responses/ and ./latex/")
        print("Waiting 20 seconds before trying again...")
        
        # wait 20 seconds
        time.sleep(20)

        # try again
        try:
            for file in os.listdir("./responses"):
                os.remove(os.path.join("./responses", file))
            for file in os.listdir("./latex"):
                os.remove(os.path.join("./latex", file))
        except Exception as e:
            print("Warning: Could not clean up ./responses/ and ./latex/")
            print(f"Encountered error: {e}")

    # Run plan-paper.py first
    print("Running plan-paper.py...")
    out_plan_paper = subprocess.run(["python", "plan-paper.py"], capture_output=True, text=True)

    # Print the output
    print("STDOUT:")
    print(out_plan_paper.stdout)
    
    print("STDERR:")
    print(out_plan_paper.stderr)
    
    print(f"Return code: {out_plan_paper.returncode}")

    if out_plan_paper.returncode !=0:
        print(f"Plan paper failed, saving out_plan_paper.stderr to ./2-many-papers/paper-{paper_i:03}-plan-paper-stderr.txt")
        with open(f"./2-many-papers/paper-{paper_i:03}-plan-paper-stderr.txt", "w") as f:
            f.write(out_plan_paper.stderr)
        with open(f"./2-many-papers/paper-{paper_i:03}-plan-paper-stdout.txt", "w") as f:
            f.write(out_plan_paper.stdout)
        continue

    # Then run make-paper.py
    print("Running make-paper.py...")
    out_make_paper = subprocess.run([
        "python", "make-paper.py", 
        # "--model", "claude-3-5-haiku-20241022",
        "--model", "claude-3-7-sonnet-20250219",
        "--temperature", "1.0", 
        "--max-tokens", "20000"
    ], capture_output=True, text=True)

    # Print the output
    print("STDOUT:")
    print(out_make_paper.stdout)
    
    print("STDERR:")
    print(out_make_paper.stderr)
    
    print(f"Return code: {out_make_paper.returncode}")

    if out_make_paper.returncode != 0:
        print(f"Paper {paper_i} failed, saving out_make_paper.stderr to ./2-many-papers/paper-{paper_i:03}-make-paper-stderr.txt")
        with open(f"./2-many-papers/paper-{paper_i:03}-make-paper-stderr.txt", "w") as f:
            f.write(out_make_paper.stderr)
        continue

    # Copy the responses folder to 1-many-responses subfolder
    shutil.copytree("./responses", f"./1-many-responses/responses-{paper_i:03}", dirs_exist_ok=True)

    # Copy full_paper_cleaned.pdf and full_paper_cleaned.tex to 2-many-papers subfolder
    shutil.copy("./responses/full_paper_cleaned.tex", f"./2-many-papers/paper-{paper_i:03}.tex")

    if os.path.exists("./responses/full_paper_cleaned.pdf"):
        shutil.copy("./responses/full_paper_cleaned.pdf", f"./2-many-papers/paper-{paper_i:03}.pdf")
    else:
        shutil.copy("./responses/full_paper_cleaned.log", f"./2-many-papers/paper-{paper_i:03}.log")
        print(f"PDF failed, copying log file instead to ./2-many-papers/paper-{paper_i:03}.log")

    # Feedback
    end_time = time.time()
    print("----------------------------------------")
    print(f"Paper {paper_i} of {num_papers} complete")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")    
    print(f"Time for paper {paper_i}: {round((end_time - start_time) / 60, 2)} minutes")    

# %%
