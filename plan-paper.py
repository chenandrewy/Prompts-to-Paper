#%%
# Setup

import os
import subprocess
import sys
import replicate
from dotenv import load_dotenv
import time
import markdown2
import pdfkit
from datetime import datetime
import shutil  
import pandas as pd
import anthropic  # Add anthropic import
import textwrap

# Load environment variables from .env file (if it exists)
load_dotenv()

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
        print(wrapper.fill(para))
        # Print a blank line to preserve paragraph separation
        print()


def query_llm(prompt_name, context_names=None, prompts_folder="./prompts", input_extension=".txt", api_provider="replicate", model_name="anthropic/claude-3.7-sonnet", use_system_prompt=True, use_thinking=False):
    """Query an llm
    
    Args:
        prompt_name: Name of the prompt file (without extension)
        context_names: List of context file names (without extension), or None for no context
        prompts_folder: Directory containing prompt files
        input_extension: File extension for prompt and context files
        api_provider: API provider to use ('replicate' or 'anthropic')
        model_name: Model version to use (e.g., "claude-3.7-sonnet", "claude-3.5-sonnet", etc.)
        use_system_prompt: Whether to use the system prompt (default: True)
        use_thinking: Whether to use thinking mode (Anthropic only)
    """
    
    # Read the prompt file
    input_path = os.path.join(prompts_folder, prompt_name + input_extension)
    with open(input_path, 'r', encoding='utf-8') as file:
        prompt = file.read()
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
                with open(context_path, 'r', encoding='utf-8') as file:
                    context_content = file.read()
                combined_context += f"--- BEGIN CONTEXT: {context_name} ---\n{context_content}\n--- END CONTEXT: {context_name} ---\n\n"

    # Read the system prompt if it exists and is requested
    system_prompt_path = os.path.join(prompts_folder, "claude-system-2025-02.txt")
    system_prompt = None
    if use_system_prompt and os.path.exists(system_prompt_path):
        print(f"Reading system prompt from {system_prompt_path}...")
        with open(system_prompt_path, 'r', encoding='utf-8') as file:
            system_prompt = file.read()
    
    # Prepare the full prompt with context if provided
    full_prompt = prompt
    if combined_context:
        full_prompt = f"Here is some context:\n\n{combined_context}\n\n{prompt}"
    
    # Process based on API provider
    if api_provider.lower() == 'replicate':
        # Replicate API
        print(f"Using Replicate model: {model_name}")
        
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
            model_name,
            input=input_params
        )
        
        # Collect the output
        result = ""
        for item in output:
            result += item
            print(item, end="", flush=True)  # Stream the output
            
    elif api_provider.lower() == 'anthropic':
        # Anthropic API
        # Create Anthropic client
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        
        # Extract the model name from the full model string if needed
        anthropic_model = model_name
        if "/" in anthropic_model:
            anthropic_model = anthropic_model.split("/")[-1]
        
        print(f"Using Anthropic model: {anthropic_model}")
        print(f"Thinking mode: {'enabled' if use_thinking else 'disabled'}")
        
        # Prepare common parameters
        params = {
            "model": anthropic_model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": full_prompt
                        }
                    ]
                }
            ]
        }
        
        # Add system prompt if provided
        if system_prompt:
            params["system"] = system_prompt
        
        # Add thinking parameters if enabled
        if use_thinking:
            params["thinking"] = {
                "type": "enabled",
                "budget_tokens": 1600
            }
        
        # Call the API
        response = client.messages.create(**params)
        
        # Extract the response text based on whether thinking mode is enabled
        if use_thinking:
            # For thinking mode, the response is in content[1]
            result = response.content[1].text
        else:
            # For standard mode, the response is in content[0]
            result = response.content[0].text
    else:
        raise ValueError(f"Unsupported API provider: {api_provider}")
    
    return result, prompt_name

def save_response(response, prompt_name, output_dir="./responses", file_ext=".tex"):
    """Save the model's response to a file.
    
    Args:
        response: The text response from Claude
        prompt_name: Name of the prompt used (for filename)
        output_dir: Directory to save the response
        file_ext: File extension for the output file
    """

    # Create the base output file path
    output_file = f"{output_dir}/{prompt_name}{file_ext}"
    
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(response)
    print(f"\n\nResponse saved to {output_file}")      

    # -- output latex 
    print(f"Outputting latex for {prompt_name}...")
    
    # read in latex template from new location
    with open("./input-other/latex-template.txt", "r") as file:
        latex_template = file.read()

    # replace [prompt-name] with prompt_name
    latex_template = latex_template.replace("% [input-goes-here]", f"\\input{{./responses/{prompt_name}.tex}}")

    # save latex template
    with open(f"./latex/{prompt_name}.tex", "w") as file:
        file.write(latex_template)
    
    # Compile with bibliography support
    compile_command = f"pdflatex -interaction=nonstopmode -halt-on-error -output-directory=./latex ./latex/{prompt_name}.tex"
    print(f"Running first LaTeX pass: {compile_command}")
    os.system(compile_command)
    
    # Run Biber without changing directory
    biber_command = f"biber ./latex/{prompt_name}"
    print(f"Running Biber: {biber_command}")
    os.system(biber_command)
    
    # Run LaTeX again (twice) to resolve references
    print("Running second LaTeX pass...")
    os.system(compile_command)
    
    print("Running final LaTeX pass...")
    result = os.system(compile_command)
    
    # Check if PDF was created before trying to copy it
    pdf_path = f"./latex/{prompt_name}.pdf"
    if os.path.exists(pdf_path):
        shutil.copy(pdf_path, f"{output_dir}/{prompt_name}.pdf")
        print(f"PDF saved to {output_dir}/{prompt_name}.pdf")
    else:
        print(f"Warning: LaTeX compilation failed for {prompt_name}")


#%%
# Set up plan_df: a dataframe of the planning prompts

prompts_folder = "./prompts"
input_extension = ".txt"

# Get list of plan prompts
plan_prompts = [f for f in os.listdir(prompts_folder) if f.startswith("plan") and f.endswith(input_extension)]

# create a dataframe of the planning prompts
plan_df = pd.DataFrame(plan_prompts, columns=["filename"])

# extract name and prompt number
plan_df["name"] = plan_df["filename"].str.replace(input_extension, "")
plan_df["number"] = plan_df["name"].str.extract(r"(\d+)")

# read in prompts
for filename in plan_df["filename"]:

    with open(os.path.join(prompts_folder, filename), 'r', encoding='utf-8') as file:
        prompt = file.read()
    plan_df.loc[plan_df["filename"] == filename, "prompt"] = prompt


#%%
# Model Planning

#  Globals
# for model list see https://replicate.com/explore

# api_provider = "replicate"  # Options: "replicate" or "anthropic"
# # model_name = "anthropic/claude-3.5-haiku" # for testing
# model_name = "anthropic/claude-3.7-sonnet" # for actual
# # model_name = "meta/meta-llama-3.1-405b-instruct" # man this is not great
# use_thinking = False  # Whether to use thinking mode (Anthropic only)

api_provider = "anthropic"
model_name = "claude-3-7-sonnet-20250219"
use_thinking = False  # Whether to use thinking mode (Anthropic only)

use_system_prompt = False
max_tokens = 4000  # Adjust as needed
temperature = 1  # Lower for more deterministic output

#%%
# Model Planning

# User selection of plan prompt range
plan_start = "04"
plan_end = "04"

# loop over plan prompts
index_start = plan_df[plan_df["number"] == plan_start].index[0]
index_end = plan_df[plan_df["number"] == plan_end].index[0]
print(f"Looping over prompts {plan_start} to {plan_end}")
for index in range(index_start, index_end+1):    
    # Set context
    if index == plan_df.index[0]:
        context_names = "none"
    else:
        # Use all previous prompt outputs as context
        context_names = plan_df["name"].iloc[:index].tolist()
        # just the previous prompt
        # context_names = plan_df["name"][index-1] 


    print("================================================")
    print(f"Processing prompt number {plan_df['number'][index]}...")

    # set prompt
    prompt = plan_df["name"][index]

    # Feedback
    print(f"Prompt: {prompt}")
    print(f"Context: {context_names}")

    # Query the model
    response, used_prompt_name = query_llm(prompt, context_names, prompts_folder, input_extension, 
                                          api_provider, model_name, use_system_prompt, use_thinking)

    # Save
    save_response(response, used_prompt_name)

    print("================================================")



# %%
# Introduction initial sketch

# context_names = ['bib-hedging-ai','planning-01','planning-02','planning-03']
context_names = ['planning-01','planning-02','planning-03']
prompt = 'intro-01'

response, used_prompt_name = query_llm(prompt, context_names, prompts_folder, input_extension, api_provider, model_name, use_system_prompt, use_thinking)

save_response(response, used_prompt_name)


#%%
# Generate lit review

#  This makes typos in citations, need to correct in next step
context_names = ['planning-01','planning-02','planning-03'] + \
    ['bib-hedging-ai', 'bib-investing-ai', 'bib-hedging-labor', 'bib-disaster-risk'] + \
    ['all-bib'] + \
    ['intro-01']
prompt = 'intro-02'

response, used_prompt_name = query_llm(prompt, context_names, prompts_folder, input_extension, api_provider, model_name, use_system_prompt, use_thinking=True)

#%% 
# fix cite typos

task = """
Fix the citations in the following latex code. Make sure the citations match actual entries in the bib file. Respond with only corrected latex code.
"""

with open("./input-other/all-bib.bib", "r") as file:
    bib_file = file.read()

prompt = task + "\n\n" + f"Here is the latex code:\n\n{response}" + f"\n\nHere is the bib file:\n\n{bib_file}"

# query anthropic
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
temp = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=1000,
    temperature=1,
    system="You are a macroeconomic theorist. Respond only with short, concise, and clear statements.",
    messages=[  
        {
            "role": "user",
            "content": [
                {
                    "type": "text", 
                    "text": prompt
                }
            ]
        }
    ]
)

response = temp.content[0].text

print_wrapped(response)

#%%

save_response(response, used_prompt_name)