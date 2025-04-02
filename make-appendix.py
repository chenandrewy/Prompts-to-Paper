import yaml
import os
from utils import MODEL_CONFIG

def format_prompt_for_latex(prompt):
    """Format a single prompt for LaTeX output."""
    # Escape special LaTeX characters
    def escape_latex(text):
        special_chars = ['&', '%', '$', '#', '_', '{', '}', '~', '^', '\\']
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        return text

    # Get full model name from MODEL_CONFIG
    model_name = prompt['model_name']
    full_model_name = MODEL_CONFIG[model_name]['full_name'] if model_name in MODEL_CONFIG else model_name

    # Format the prompt
    formatted = []
    if prompt['name'] == 'System Prompt':
        formatted.append(f"\\subsection*{{System Prompt (model: {escape_latex(full_model_name)})}}")
    else:
        formatted.append(f"\\subsection*{{Instruction: {escape_latex(prompt['name'])}  (model: {escape_latex(full_model_name)})}}")
    formatted.append("\\vspace{-1ex}")
    
    # Format instructions as code listing
    formatted.append("\\begin{lstlisting}[language=text,breaklines=true,frame=single]")
    formatted.append(escape_latex(prompt['instructions']))
    formatted.append("\\end{lstlisting}")
    formatted.append("\\vspace{-3ex}")
    
    return '\n'.join(formatted)

def create_appendix():
    # User
    plan_file = "plan5-streamlined.yaml"
    output_file = "lit-context/appendix-promptlisting.tex"

    # Read the YAML file
    with open(plan_file, "r") as f:
        data = yaml.safe_load(f)
    
    # Create the LaTeX appendix
    appendix = []
    appendix.append("\\section{Prompts Used to Generate This Paper}")
    appendix.append("""
    Each prompt consists of context and instructions. The context consists of the responses to the previous prompts, and may include literature reviews (all AI generated). For writing tasks (using Claude 3.7 Sonnet), a system prompt is also included.
    
    For further details, see \\url{{https://github.com/chenandrewy/Prompts-to-Paper/}}.
    
    The system prompt and instructions are listed below.
    """)
    appendix.append("\\vspace{-2ex}")
    
    # Add system prompt first
    if 'config' in data and 'system_prompt' in data['config']:
        system_prompt = {
            'name': 'System Prompt',
            'model_name': 'sonnet',
            'instructions': data['config']['system_prompt']
        }
        appendix.append(format_prompt_for_latex(system_prompt))
    
    # Add each regular prompt
    for prompt in data['prompts']:
        appendix.append(format_prompt_for_latex(prompt))
        
    # Write to file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write('\n'.join(appendix))
    
    print(f"Appendix has been created in {output_file}")

if __name__ == "__main__":
    create_appendix() 