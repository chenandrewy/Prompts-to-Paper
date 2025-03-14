"""
Utility functions for the Prompts-to-Paper project.
"""

import os
import textwrap

def clean_latex_aux_files(prompt_name):
    """Clean up auxiliary files created by LaTeX.
    
    Args:
        prompt_name: Base name of the LaTeX file (without extension)
    """
    aux_files = [
        f"{prompt_name}.aux",
        f"{prompt_name}.bbl",
        f"{prompt_name}.blg",
        f"{prompt_name}.out"
    ]

    for file in aux_files:
        if os.path.exists(file):
            os.remove(file)

def print_wrapped(text, width=70):
    """
    Prints the input text with word wrapping while preserving paragraph breaks.
    
    Args:
        text (str): The input text to print.
        width (int, optional): Maximum width for each line. Defaults to 70.
    """
    # Create a TextWrapper instance with the desired width
    wrapper = textwrap.TextWrapper(width=width)
    
    # Split the text into paragraphs using double newlines
    paragraphs = text.split("\n\n")
    
    # Wrap and print each paragraph separately
    for para in paragraphs:
        try:
            print(wrapper.fill(para))
        except UnicodeEncodeError:
            # Handle Unicode encoding errors by replacing problematic characters
            print(wrapper.fill(para.encode('ascii', 'replace').decode('ascii')))
        # Print a blank line to preserve paragraph separation
        print() 

# Check if running in Jupyter notebook or as a script
def is_jupyter():
    try:
        # This will only exist in Jupyter environments
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':  # Jupyter notebook or qtconsole
            return True
        elif shell == 'TerminalInteractiveShell':  # IPython terminal
            return False
        else:
            return False
    except NameError:  # Not in an IPython environment
        return False

# validate arguments
def validate_arguments(args):
    if args.model_name == "claude-3-5-haiku-20241022":
        if args.max_tokens > 8192:
            print("WARNING: claude-3-5-haiku-20241022 has a context window of 8192 tokens. Setting max_tokens to 8192.")
            args.max_tokens = 8192
    
    return args
