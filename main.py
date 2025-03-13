# Runs everything.

import subprocess

# Run plan-paper.py first
print("Running plan-paper.py...")
subprocess.run(["python", "plan-paper.py"])

# Then run make-paper.py
print("Running make-paper.py...")
subprocess.run(["python", "make-paper.py"])
