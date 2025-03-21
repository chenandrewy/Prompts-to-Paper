"""
Utility functions for the Prompts-to-Paper project.
"""

import os
import textwrap
import pandas as pd

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

def calculate_costs(response, model_name, max_tokens, thinking_budget):
    """Calculate token usage and costs for Anthropic API calls.
    
    Args:
        response: The response object from Anthropic API
        model_name: Name of the model used (e.g., "claude-3-7-sonnet-20250219")
        max_tokens: Maximum tokens allowed for the response
        thinking_budget: Budget tokens for thinking mode
        
    Returns:
        tuple: A tuple containing (cost_dict, cost_summary) where:
            - cost_dict: Dictionary containing token usage and cost information
            - cost_summary: String containing formatted token usage and cost information
    """
    # Model pricing information
    MODEL_PRICES = {
        "sonnet": {
            "input":   3.0*10**-6,  # $3 per M tokens
            "output": 15.0*10**-6,  # $15 per M tokens
        },
        "haiku": {
            "input": 0.8*10**-6,   
            "output": 4.0*10**-6,  
        }
    }

    # Find matching model based on substring
    matching_model = None
    for model_key in MODEL_PRICES:
        if model_key in model_name.lower():
            matching_model = model_key
            break
    
    if matching_model is None:
        raise ValueError(f"No matching model found for {model_name}")

    # Get token counts from response
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    total_tokens = input_tokens + output_tokens
    
    # Calculate costs
    input_cost = input_tokens * MODEL_PRICES[matching_model]["input"]
    output_cost = output_tokens * MODEL_PRICES[matching_model]["output"]
    total_cost = input_cost + output_cost        

    # Create dictionary format
    cost_dict = {
        "model": {
            "name": model_name,
            "type": matching_model
        },
        "token_usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "max_tokens": max_tokens,
            "thinking_budget": thinking_budget,
            "total_tokens": total_tokens
        },
        "costs": {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost
        }
    }

    # Format cost summary string
    cost_summary = f"""
    %% MODEL INFO
    % Model name: {model_name}
    % Model type: {matching_model}
    %% TOKEN USAGE
    % Input tokens: {input_tokens}
    % Output tokens: {output_tokens}
    % max_tokens: {max_tokens}
    % thinking_budget: {thinking_budget}
    %% COSTS        
    % Total tokens: {total_tokens}
    % Input cost: ${input_cost:.2f}
    % Output cost: ${output_cost:.2f}
    % Total cost: ${total_cost:.2f}
    """

    return cost_dict, cost_summary

def save_cost_table(cost_df, output_path='./responses/cost_tracking.md'):
    """Format and save a DataFrame as a nicely spaced markdown table.
    
    Args:
        cost_df (pd.DataFrame): DataFrame containing cost tracking information
        output_path (str): Path where to save the markdown table
    """

    # round all values to 3 decimal places
    cost_df = cost_df.round(3)

    # clean up
    cost_df = cost_df.drop(columns=["timestamp", "model_type"])

    # convert to long format
    cost_df = cost_df.melt(id_vars=["prompt_name"], var_name="name", value_name="value").sort_values(by=["prompt_name"])    
    
    def format_table_row(row, col_widths):
        return '| ' + ' | '.join(f"{str(val):{width}}" for val, width in zip(row, col_widths)) + ' |'

    # Calculate column widths based on maximum content length
    col_widths = {}
    for col in cost_df.columns:
        # Get max length of column name and values
        max_val_length = max(
            len(str(val)) for val in cost_df[col].astype(str)
        )
        col_widths[col] = max(len(col), max_val_length)

    # Create markdown table content
    md_content = []
    # Header
    headers = list(cost_df.columns)
    md_content.append(format_table_row(headers, [col_widths[col] for col in headers]))
    # Separator
    md_content.append('|' + '|'.join('-' * (col_widths[col] + 2) for col in headers) + '|')
    # Data rows
    for _, row in cost_df.iterrows():
        md_content.append(format_table_row(row, [col_widths[col] for col in headers]))

    # Save markdown table
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write('\n'.join(md_content))
