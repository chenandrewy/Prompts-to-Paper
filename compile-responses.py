#%%
import os
import glob
import subprocess
from pathlib import Path

def main():
    # 1. Find all planning*.tex files in ./responses/
    planning_files = sorted(glob.glob('./responses/planning*.tex'))
    
    if not planning_files:
        print("No planning*.tex files found in ./responses/ directory")
        return
    
    print(f"Found {len(planning_files)} planning files")
    
    # 2. Read in the template file
    template_path = './latex/template-prompt.tex'
    try:
        with open(template_path, 'r') as f:
            template_content = f.read()
    except FileNotFoundError:
        print(f"Template file not found: {template_path}")
        return
    
    # 3. Modify the template to input all planning files
    input_commands = []
    for file_path in planning_files:
        # Convert to relative path from the latex directory
        relative_path = os.path.relpath(file_path, './latex')
        # Replace backslashes with forward slashes for LaTeX compatibility
        relative_path = relative_path.replace('\\', '/')
        input_commands.append(f'\\input{{{relative_path}}}')
    
    # Join all input commands with newlines
    input_block = '\n'.join(input_commands)
    
    # Replace a placeholder in the template or append to the end
    if '%PLANNING_INPUTS%' in template_content:
        modified_content = template_content.replace('%PLANNING_INPUTS%', input_block)
    else:
        # If no placeholder exists, add before \end{document} if it exists
        if '\\end{document}' in template_content:
            modified_content = template_content.replace('\\end{document}', f'{input_block}\n\n\\end{{document}}')
        else:
            # Otherwise just append to the end
            modified_content = f"{template_content}\n\n{input_block}"
    
    # 4. Save the new tex file
    output_path = './latex/compiled-planning.tex'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(modified_content)
    
    print(f"Created {output_path}")
    
    # 5. Compile the tex file to PDF
    compile_latex(output_path)

def compile_latex(tex_file):
    """Compile a LaTeX file to PDF using pdflatex."""
    latex_dir = os.path.dirname(tex_file)
    tex_filename = os.path.basename(tex_file)
    
    # Change to the latex directory
    original_dir = os.getcwd()
    os.chdir(latex_dir)
    
    try:
        # Run pdflatex twice to resolve references
        for _ in range(2):
            result = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', tex_filename],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print("LaTeX compilation failed:")
                print(result.stderr)
                break
        
        pdf_filename = tex_filename.replace('.tex', '.pdf')
        if os.path.exists(pdf_filename):
            print(f"Successfully compiled {pdf_filename}")
        else:
            print(f"Failed to generate PDF file")
    
    finally:
        # Return to the original directory
        os.chdir(original_dir)

if __name__ == "__main__":
    main()
