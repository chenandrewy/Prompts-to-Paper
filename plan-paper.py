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
from utils import clean_latex_aux_files, print_wrapped, is_jupyter
import argparse
import yaml

# Load environment variables from .env file 
load_dotenv()

#%%
# Functions

def query_llm(prompt_name, instructions, context_names=None, add_lit=False, 
              prompts_folder="./prompts", 
              response_folder = "./responses", response_ext = ".tex",
              api_provider="replicate", model_name="anthropic/claude-3.7-sonnet", thinking_budget=0, max_tokens=4000, temperature=0.5):
    """Query an llm
    
    Args:
        prompt_name: Name of the prompt file (without extension)
        instructions: The actual instructions text to send to the model
        context_names: List of context file names (without extension), or None for no context
        prompts_folder: Directory containing prompt files
        response_folder: Directory to save the response
        response_ext: File extension for the response
        api_provider: API provider to use ('replicate' or 'anthropic')
        model_name: Model version to use (e.g., "claude-3.7-sonnet", "claude-3.5-sonnet", etc.)
        thinking_budget: Budget tokens for thinking mode. If > 0, enables thinking mode with specified budget (default: 0)
    """
    # convert pandas integers to native python
    max_tokens = int(max_tokens)
    thinking_budget = int(thinking_budget)

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

    if (model_name == "claude-3-5-haiku-20241022"):
        if max_tokens > 8192:
            print(f"Warning: claude-3-5-haiku-20241022 has a context window of 8192 tokens. Setting max_tokens to 8192.")
            max_tokens = 8192
        if thinking_budget > 0:
            print(f"Warning: claude-3-5-haiku-20241022 does not support thinking mode. Setting thinking budget to 0.")
            thinking_budget = 0

    # Read the contexts if specified
    combined_context = ""
    if context_names:
        # Handle both string and list inputs for backward compatibility
        if isinstance(context_names, str) and context_names != "none":
            context_names = [context_names]
        elif isinstance(context_names, str) and context_names == "none":
            context_names = []
            
        for context_name in context_names:
            context_path = os.path.join(response_folder, context_name + "-texinput" + response_ext)
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
        lit_files = [f for f in os.listdir(prompts_folder) if f.startswith("lit-") and f.endswith(".txt")]

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

    # Get system prompt from YAML config if it exists
    system_prompt = None
    if "system_prompt" in config:
        print("Using system prompt from YAML config...")
        system_prompt = config["system_prompt"]
    
    # Prepare the full prompt with context if provided
    full_prompt = instructions
    if combined_context:
        full_prompt = f"Here is some context:\n\n{combined_context}\n\n{instructions}"
    
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

        # -- check spending --
        MODEL_PRICES = {
            "claude-3-7-sonnet-20250219": {
                "input":   3.0*10**-6,  # $3 per M tokens
                "output": 15.0*10**-6,  # $15 per M tokens
            },
            "claude-3-5-haiku-20241022": {
                "input": 0.8*10**-6,   
                "output": 4.0*10**-6,  
            }
        }

        # Get token counts from response
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        total_tokens = input_tokens + output_tokens
        
        # Calculate costs
        input_cost = input_tokens * MODEL_PRICES[anthropic_model]["input"]
        output_cost = output_tokens * MODEL_PRICES[anthropic_model]["output"]
        total_cost = input_cost + output_cost        

        # Summarize costs
        cost_summary = f"""
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

        # add cost summary to result
        result = f"{cost_summary}\n\n{result}"

        if output_tokens >= 0.95 * max_tokens:
            print(f"Warning: Max tokens were nearly reached. Output tokens: {output_tokens}, Max tokens: {max_tokens}")

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

    # -- save latex input file --
    # Create the base output file path
    output_file = f"{output_dir}/{prompt_name}-texinput{file_ext}"
    
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(response)
    print(f"\n\nResponse saved to {output_file}")      

    # -- output latex document --
    print(f"Outputting latex for {prompt_name}...")
    
    # read in latex template from new location
    with open("./input-other/latex-template.txt", "r") as file:
        latex_template = file.read()

    # replace [prompt-name] with prompt_name
    latex_template = latex_template.replace("% [input-goes-here]", f"\\input{{../responses/{prompt_name}-texinput.tex}}")

    # save complete latex doc
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

#%%
# SETUP

# User
plan_name = "planning-prompts-test"

# Global (tbc: make it nicer somehow?)
prompts_folder = "./prompts"

# Load all config and prompts
with open(os.path.join(prompts_folder, f"{plan_name}.yaml"), "r") as f:
    settings = yaml.safe_load(f)

# Get config
config = settings["config"]
api_provider = config["api_provider"]

# Create DataFrame from YAML data
plan_df = pd.DataFrame(settings["prompts"])

# Sort by number to ensure correct order
plan_df = plan_df.sort_values("number").reset_index(drop=True)

# Fix run range
plan_start = max(int(config["run_range"]["start"]), plan_df["number"].min())
plan_end = min(int(config["run_range"]["end"]), plan_df["number"].max())

# Find index for start
index_start = plan_df[plan_df["number"] == plan_start].index[0] 
index_end = plan_df[plan_df["number"] == plan_end].index[0]

print(f"Processing plan prompts from {plan_start} to {plan_df['number'].iloc[index_end]}")

#%%
# LOOP OVER PROMPTS

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

    # extract instructions and parameters
    instructions = plan_df["instructions"][index]
    
    # Require max_tokens and thinking_budget in YAML
    if "max_tokens" not in plan_df.columns or "thinking_budget" not in plan_df.columns:
        raise ValueError("YAML must specify max_tokens and thinking_budget for each prompt")
    
    prompt_max_tokens = plan_df["max_tokens"].iloc[index]
    prompt_thinking_budget = plan_df["thinking_budget"].iloc[index]

    # Feedback
    print(f"Instructions: {instructions}")
    print(f"Context: {context_names}")
    print(f"Max tokens: {prompt_max_tokens}")
    print(f"Thinking budget: {prompt_thinking_budget}")

    # Determine if this prompt should include bibliography from YAML
    add_lit = plan_df["include_lit"][index]
    print(f"Including literature: {add_lit}")

    # Query the model
    response, used_prompt_name = query_llm(
        prompt_name = plan_df["name"][index], 
        instructions = instructions,
        context_names = context_names, 
        add_lit = add_lit, 
        prompts_folder = prompts_folder, 
        response_folder = "./responses", 
        response_ext = ".tex",
        api_provider = api_provider, 
        model_name = plan_df["model_name"][index], 
        thinking_budget = prompt_thinking_budget,
        max_tokens = prompt_max_tokens,
        temperature = config["temperature"]
    )

    # Save
    save_response(response, used_prompt_name)

    print("================================================")


# %%
