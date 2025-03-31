import os
import shutil
from pathlib import Path

def save_output(prefix):
    # Source and destination directories
    source_dir = Path("output-o1")
    dest_dir = Path("saved-output")
    
    # Create destination directory if it doesn't exist
    dest_dir.mkdir(exist_ok=True)
    
    # File extensions to copy
    extensions = ['.pdf', '.md', '.xml']
    
    # Counter for tracking number of files copied
    files_copied = 0
    
    # Iterate through all files in source directory
    for file_path in source_dir.glob('*'):
        if file_path.suffix.lower() in extensions:
            # Create new filename with prefix
            new_filename = f"{prefix}_{file_path.name}"
            dest_path = dest_dir / new_filename
            
            # Copy the file
            shutil.copy2(file_path, dest_path)
            files_copied += 1
            print(f"Copied: {file_path.name} -> {new_filename}")
    
    print(f"\nTotal files copied: {files_copied}")

if __name__ == "__main__":
    prefix = input("Enter prefix for saved files: ")
    save_output(prefix)
