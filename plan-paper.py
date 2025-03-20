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
from utils import clean_latex_aux_files, print_wrapped, is_jupyter, validate_arguments
import argparse

# Load environment variables from .env file 
load_dotenv()


#%%
# Parse arguments

# for reference
# model_name = "claude-3-7-sonnet-20250219"
# model_name = "claude-3-5-haiku-20241022"

# parse from command line
def parse_arguments():
    parser = argparse.ArgumentParser(description='Generate an academic paper using Claude AI')
    parser.add_argument('--model_name', type=str, default="claude-3-7-sonnet-20250219",
                        help='Model to use for generation (default: claude-3-7-sonnet-20250219)')
    parser.add_argument('--temperature', type=float, default=0.5,
                        help='Temperature for generation (default: 0.5)')
    parser.add_argument('--max-tokens', type=int, default=10000,
                        help='Maximum tokens to generate (default: 10000)')
    parser.add_argument('--thinking-budget', type=int, default=0,
                        help='Budget tokens for thinking mode (default: 0)')
    parser.add_argument('--plan-range', type=str, default="01-99",
                        help='Range of planning prompts to process (format: XX-YY, default: 01-99)')
    parser.add_argument('--lit-range', type=str, default="01-99",
                        help='Range of prompts that should include literature context (format: XX-YY, default: 01-99)')
    return parser.parse_args()

# parse for jupyter notebook (testing)
if is_jupyter():
    class DefaultArgs:
        def __init__(self):
            self.model_name = "claude-3-7-sonnet-20250219"
            self.temperature = 0.5
            self.max_tokens = 4000
            self.plan_range = "01-01"
            self.lit_range = "09-99"
            self.thinking_budget = 4000

    args = DefaultArgs()
    print("Running in Jupyter notebook with default arguments")
else:
    # Get command line arguments when running as a script
    args = parse_arguments()
    print(f"Running as script with arguments: model_name={args.model_name}, temperature={args.temperature}, "
          f"max_tokens={args.max_tokens}, plan_range={args.plan_range}, lit_range={args.lit_range}")

# validate arguments
args = validate_arguments(args)

#%%
# Functions

def query_llm(prompt_name, context_names=None, add_lit=False, 
              prompts_folder="./prompts", input_extension=".txt", 
              response_folder = "./responses", response_ext = ".tex",
              api_provider="replicate", model_name="anthropic/claude-3.7-sonnet", use_system_prompt=True, thinking_budget=0, max_tokens=4000, temperature=0.5):
    """Query an llm
    
    Args:
        prompt_name: Name of the prompt file (without extension)
        context_names: List of context file names (without extension), or None for no context
        prompts_folder: Directory containing prompt files
        input_extension: File extension for prompt and context files
        api_provider: API provider to use ('replicate' or 'anthropic')
        model_name: Model version to use (e.g., "claude-3.7-sonnet", "claude-3.5-sonnet", etc.)
        use_system_prompt: Whether to use the system prompt (default: True)
        thinking_budget: Budget tokens for thinking mode. If > 0, enables thinking mode with specified budget (default: 0)
    """

    # Argument check
    if (thinking_budget > 0) & (temperature != 1):
        print(f"Warning: Thinking mode is enabled, but temperature is not 1. Setting temperature to 1.")
        temperature = 1

    if thinking_budget >= max_tokens:
        print(f"Warning: Thinking budget ({thinking_budget}) cannot be greater than max tokens ({max_tokens}). Setting thinking budget equal to 1/2 of max tokens.")
        thinking_budget = max_tokens // 2
    
    if (thinking_budget > 0) & (thinking_budget < 1024):
        print(f"Warning: Thinking budget ({thinking_budget}) is less than 1024. Setting thinking budget to 1024.")
        thinking_budget = 1024
    
    
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
            context_path = os.path.join(response_folder, context_name + response_ext)
            if os.path.exists(context_path):
                print(f"Reading context from {context_path}...")
                with open(context_path, 'r', encoding='utf-8') as file:
                    context_content = file.read()
                combined_context += f"--- BEGIN CONTEXT: {context_name} ---\n{context_content}\n--- END CONTEXT: {context_name} ---\n\n"
            else:
                # Error out if context file is not found
                raise FileNotFoundError(f"Context file not found: {context_path}")

    # add literature context if requested
    if add_lit:
        # find all lit files in prompts folder
        lit_files = [f for f in os.listdir(prompts_folder) if f.startswith("lit-") and f.endswith(input_extension)]

        # if no lit files, error out
        if not lit_files:
            raise FileNotFoundError("No lit files found in prompts folder")

        # read in lit files
        for lit_file in lit_files:
            lit_path = os.path.join(prompts_folder, lit_file)
            print(f"Reading lit from {lit_path}...")
            with open(lit_path, 'r', encoding='utf-8') as file:
                lit_content = file.read()
            combined_context += f"--- BEGIN LITERATURE ---\n{lit_content}\n--- END LITERATURE ---\n\n"

    # Read the system prompt if it exists and is requested
    system_prompt_path = os.path.join(prompts_folder, "system-prompt.txt")
    system_prompt = None
    if use_system_prompt and os.path.exists(system_prompt_path):
        print(f"Reading system prompt from {system_prompt_path}...")
        with open(system_prompt_path, 'r', encoding='utf-8') as file:
            system_prompt = file.read()
    
    # Prepare the full prompt with context if provided
    full_prompt = prompt
    if combined_context:
        full_prompt = f"Here is some context:\n\n{combined_context}\n\n{prompt}"
    
    # save full prompt to responses folder
    temp_prompt_path = os.path.join(response_folder, f"{prompt_name}-full-prompt.txt")
    with open(temp_prompt_path, "w", encoding="utf-8") as file:
        file.write(full_prompt)

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
        if thinking_budget > 0:
            print(f"Thinking mode: enabled with budget {thinking_budget} tokens")
        else:
            print(f"Thinking mode: disabled")
        print(f"First 1000 characters of full prompt: {full_prompt[:1000]}")
        
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
        
        # Add thinking parameters if budget > 0
        if thinking_budget > 0:
            params["thinking"] = {
                "type": "enabled",
                "budget_tokens": thinking_budget
            }
        
        # Call the API
        print(f"Thinking budget: {thinking_budget}")
        print(f"Max tokens: {max_tokens}")
        response = client.messages.create(**params)
        
        # Extract the response text based on whether thinking mode is enabled
        if thinking_budget > 0:
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
    latex_template = latex_template.replace("% [input-goes-here]", f"\\input{{../responses/{prompt_name}.tex}}")

    # save latex template
    with open(f"./latex/{prompt_name}.tex", "w") as file:
        file.write(latex_template)

    # clean aux files
    clean_latex_aux_files(prompt_name)
    
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

def planning_loop(plan_range, lit_range="04-99", prompts_folder="./prompts", input_extension=".txt", 
                 api_provider="anthropic", model_name="claude-3-7-sonnet-20250219", 
                 use_system_prompt=True, thinking_budget=0, max_tokens=4000, temperature=1):
    """
    Process a sequence of planning prompts with context from previous prompts.
    
    Args:
        plan_range: Range of prompts to process (e.g., "01-03" or "full")
        lit_range: Range of prompts that should include literature context (e.g., "04-99")
        prompts_folder: Directory containing prompt files
        input_extension: File extension for prompt files
        api_provider: API provider to use ('replicate' or 'anthropic')
        model_name: Model version to use
        use_system_prompt: Whether to use the system prompt
        thinking_budget: Budget tokens for thinking mode. If > 0, enables thinking mode (default: 0)
        max_tokens: Maximum tokens for response
        temperature: Temperature for response generation
    """
    # Get list of plan prompts
    plan_prompts = [f for f in os.listdir(prompts_folder) if f.startswith("plan") and f.endswith(input_extension)]

    # create a dataframe of the planning prompts
    plan_df = pd.DataFrame(plan_prompts, columns=["filename"])

    # extract name and prompt number
    plan_df["name"] = plan_df["filename"].str.replace(input_extension, "")
    plan_df["number"] = plan_df["name"].str.extract(r"(\d+)").astype(int)
    plan_df["prompt"] = ""  # Pre-allocate the prompt column with empty strings
    
    # Sort by number to ensure correct order
    plan_df = plan_df.sort_values("number").reset_index(drop=True)

    # read in prompts
    for filename in plan_df["filename"]:
        with open(os.path.join(prompts_folder, filename), 'r', encoding='utf-8') as file:
            prompt = file.read()
        plan_df.loc[plan_df["filename"] == filename, "prompt"] = prompt

    # Parse the range format "XX-YY"
    plan_parts = plan_range.split("-")
    plan_start = max(int(plan_parts[0]), plan_df["number"].min())
    plan_end = min(int(plan_parts[1]), plan_df["number"].max())
    
    # Find index for start
    index_start = plan_df[plan_df["number"] == plan_start].index[0] 
    index_end = plan_df[plan_df["number"] == plan_end].index[0]

    print(f"Processing plan prompts from {plan_start} to {plan_df['number'].iloc[index_end]}")

    # Parse the literature range
    lit_parts = lit_range.split("-")
    lit_start = int(lit_parts[0])
    lit_end = int(lit_parts[1]) if len(lit_parts) > 1 else lit_start
    print(f"Using literature for prompts {lit_start} through {lit_end}")
    
    # loop over plan prompts
    for index in range(index_start, index_end+1):    
        # Set context
        if index == 0:
            context_names = "none"
        else:
            # Use all previous prompt outputs as context
            context_names = plan_df["name"].iloc[:index].tolist()

        print("================================================")
        print(f"Processing prompt number {plan_df['number'][index]}...")

        # set prompt
        prompt = plan_df["name"][index]

        # Feedback
        print(f"Prompt: {prompt}")
        print(f"Context: {context_names}")

        # Determine if this prompt should include bibliography
        current_prompt_num = int(plan_df["number"][index])
        add_lit = lit_start <= current_prompt_num <= lit_end
        print(f"Including literature: {add_lit}")

        # Query the model
        response, used_prompt_name = query_llm(
            prompt_name = prompt, 
            context_names = context_names, 
            add_lit = add_lit, 
            prompts_folder = prompts_folder, 
            input_extension = input_extension, 
            api_provider = api_provider, 
            model_name = model_name, 
            thinking_budget = thinking_budget,
            max_tokens = max_tokens,
            temperature = temperature
        )

        # Save
        save_response(response, used_prompt_name)

        print("================================================")


#%%
# main

api_provider = "anthropic"
prompts_folder = "./prompts"
input_extension = ".txt"

# Call the planning loop with the plan range and bib range
planning_loop(
    plan_range = args.plan_range, 
    lit_range = args.lit_range, 
    model_name = args.model_name, 
    thinking_budget = args.thinking_budget,
    max_tokens = args.max_tokens, 
    temperature = args.temperature
)    
