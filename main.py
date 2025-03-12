#%%
# Setup

import os
import sys
import replicate
from dotenv import load_dotenv
import time
import markdown2
import pdfkit
from datetime import datetime
import shutil  
import pandas as pd

# Load environment variables from .env file (if it exists)
load_dotenv()

def read_prompt_file(filename):
    """Read the content from the specified file."""
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

def query_llm(prompt_name, context_names=None, prompts_folder="./prompts", input_extension=".txt", model_name="anthropic/claude-3.7-sonnet"):
    """Query the Claude model via Replicate API.
    
    Args:
        prompt_name: Name of the prompt file (without extension)
        context_names: List of context file names (without extension), or None for no context
        prompts_folder: Directory containing prompt files
        input_extension: File extension for prompt and context files
        model_name: Claude model version to use (e.g., "claude-3.7-sonnet", "claude-3.5-sonnet", etc.)
    """
    # Check if API token is available
    if "REPLICATE_API_TOKEN" not in os.environ:
        print("Error: REPLICATE_API_TOKEN environment variable not set.")
        print("Please set your Replicate API token in the .env file or environment variables.")
        sys.exit(1)
    
    # Read the prompt file
    input_path = os.path.join(prompts_folder, prompt_name + input_extension)
    prompt = read_prompt_file(input_path)
    print(f"Reading prompt from {input_path}...")
    
    # Read the contexts if specified
    combined_context = ""
    if context_names:
        # Handle both string and list inputs for backward compatibility
        if isinstance(context_names, str) and context_names != "none":
            context_names = [context_names]
        elif isinstance(context_names, str) and context_names == "none":
            context_names = []
            
        for context_name in context_names:
            context_path = os.path.join(prompts_folder, context_name + input_extension)
            if os.path.exists(context_path):
                print(f"Reading context from {context_path}...")
                context_content = read_prompt_file(context_path)
                combined_context += f"--- BEGIN CONTEXT: {context_name} ---\n{context_content}\n--- END CONTEXT: {context_name} ---\n\n"

    # Read the system prompt if it exists
    system_prompt_path = os.path.join(prompts_folder, "claude-system-2025-02.txt")
    system_prompt = None
    if os.path.exists(system_prompt_path):
        print(f"Reading system prompt from {system_prompt_path}...")
        system_prompt = read_prompt_file(system_prompt_path)
    
    # Select model
    model = model_name
    print(f"Using model: {model}")
    
    # Prepare the full prompt with context if provided
    full_prompt = prompt
    if combined_context:
        full_prompt = f"Here is some context:\n\n{combined_context}\n\n{prompt}"
    
    # Prepare input parameters
    input_params = {
        "prompt": full_prompt,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    
    # Add system prompt if provided
    if system_prompt:
        input_params["system"] = system_prompt
    
    # Run the model
    output = replicate.run(
        model,
        input=input_params
    )
    
    # Collect the output
    result = ""
    for item in output:
        result += item
        print(item, end="", flush=True)  # Stream the output
    
    return result, prompt_name

def save_response(response, prompt_name, use_timestamp=False, output_dir="./responses", file_ext=".md"):
    """Save the model's response to a file.
    
    Args:
        response: The text response from Claude
        prompt_name: Name of the prompt used (for filename)
        use_timestamp: Whether to add a timestamp to the filename
        output_dir: Directory to save the response
        file_ext: File extension for the output file
    """

    # Create the base output file path
    output_file = f"{output_dir}/{prompt_name}{file_ext}"
    
    # Apply timestamp to filename if requested
    if use_timestamp:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        file_base, file_ext = os.path.splitext(output_file)
        output_file = f"{file_base}_{timestamp}{file_ext}"
        
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(response)
    print(f"\n\nResponse saved to {output_file}")      

    # -- output latex 
    print(f"Outputting latex for {prompt_name}...")
    
    # read in latex template
    with open("./latex/template-prompt.tex", "r") as file:
        latex_template = file.read()

    # replace [prompt-name] with prompt_name
    latex_template = latex_template.replace("[prompt-name]", prompt_name)

    # save latex template
    with open(f"./latex/{prompt_name}.tex", "w") as file:
        file.write(latex_template)
    
    # compile latex with non-interactive mode and halt on errors
    os.system(f"pdflatex -interaction=nonstopmode -halt-on-error -output-directory=./latex ./latex/{prompt_name}.tex")
    
    # Check if PDF was created before trying to copy it
    pdf_path = f"./latex/{prompt_name}.pdf"
    if os.path.exists(pdf_path):
        shutil.copy(pdf_path, f"{output_dir}/{prompt_name}.pdf")
        print(f"PDF saved to {output_dir}/{prompt_name}.pdf")
    else:
        print(f"Warning: LaTeX compilation failed for {prompt_name}")

#%%
# Set up plan_df: a dataframe of the planning prompts

# Get list of plan prompts
plan_prompts = [f for f in os.listdir(prompts_folder) if f.startswith("plan") and f.endswith(input_extension)]

# create a dataframe of the planning prompts
plan_df = pd.DataFrame(plan_prompts, columns=["filename"])

# extract name and index
plan_df["name"] = plan_df["filename"].str.replace(input_extension, "")
plan_df["index"] = plan_df["name"].str.extract(r"(\d+)")

# read in prompts
for filename in plan_df["filename"]:
    prompt = read_prompt_file(os.path.join(prompts_folder, filename))
    plan_df.loc[plan_df["filename"] == filename, "prompt"] = prompt


#%%
# Main

#  Globals
# for model list see https://replicate.com/explore

use_timestamp = False # if True, output has timestamp
model_name = "anthropic/claude-3.7-sonnet" # for actual
# model_name = "anthropic/claude-3.5-haiku" # for testing
# model_name = "meta/meta-llama-3.1-405b-instruct" # man this is not great
prompts_folder = "./prompts"
input_extension = ".txt"
max_tokens = 4000  # Adjust as needed
temperature = 0.5  # Lower for more deterministic output


# User selection of plan prompt range
plan_start = "01"
plan_end = "02"

# loop over plan prompts
index_start = plan_df[plan_df["index"] == plan_start].index[0]
index_end = plan_df[plan_df["index"] == plan_end].index[0]

for index in range(index_start, index_end+1):
    

    print(f"Processing prompt index {index}...")

    # Set context
    if index == plan_df.index[0]:
        context_names = "none"
    else:
        # Strip extension from previous prompt for context
        context_names = plan_df["name"][index-1]

    # set prompt
    prompt = plan_df["name"][index]

    # Feedback
    print(f"Prompt: {prompt}")
    print(f"Context: {context_names}")

    # Query the model
    response, used_prompt_name = query_llm(prompt, context_names, prompts_folder, input_extension, model_name)

    # Save
    save_response(response, used_prompt_name, use_timestamp)


