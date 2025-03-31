#%%
# SETUP

import os
import sys
import replicate
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd
import anthropic
from utils import MODEL_CONFIG, print_wrapped, assemble_prompt, query_claude, query_openai, response_to_texinput, texinput_to_pdf
from utils import save_costs, aggregate_costs
import yaml
import logging
from importlib import reload
import re
import time
# User
plan_name = "plan3-o1"
# plan_name = "plan1-test"

# Extract output folder name from plan_name
output_folder = f"./output-{plan_name.split('-')[-1]}/"
os.makedirs(output_folder, exist_ok=True)

# Add this line right after imports
load_dotenv()

#%%
# LOOP OVER PROMPTS

# Load all config and prompts
with open(f"{plan_name}.yaml", "r") as f:
    temp = yaml.safe_load(f)

config = temp["config"]
prompts = temp["prompts"]

# Initialize
all_costs = []
index_start = config["run_range"]["start"]-1
index_end = min(config["run_range"]["end"]-1, len(prompts)-1)


# loop over prompts
for index in range(index_start, index_end+1):    
# for index in [0]:
    
    print("================================================")
    print(f"Processing prompt number {index+1}...")

    print("Assembling context")
    print(f"Instructions: {prompts[index]['instructions']}")
    if "lit_files" in prompts[index]:
        print(f"Lit files: {prompts[index]['lit_files']}")
    
    # Previous responses context
    prev_responses = [prompt["name"] for prompt in prompts[:index]]
    prev_responses = [f"{output_folder}{fname}-response.md" for fname in prev_responses]


    # Literature context
    if "lit_files" in prompts[index]:
        lit_files = prompts[index]["lit_files"]
        lit_files = [f"./lit-context/{fname}" for fname in lit_files]
    else:
        lit_files = []

    # Generate the full prompt
    full_prompt = assemble_prompt(
        instructions=prompts[index]["instructions"],
        context_files=prev_responses + lit_files
    )

    # by default, use system prompt
    if "use_system_prompt" not in prompts[index] or prompts[index]["use_system_prompt"] == True:
        system_prompt_current = config["system_prompt"]
    elif prompts[index]["use_system_prompt"] == False:
        # do not use system prompt if use_system_prompt is false
        system_prompt_current = ""
   
    # save the prompt
    with open(f"{output_folder}{prompts[index]['name']}-system-prompt.xml", "w", encoding="utf-8") as f:
        f.write(system_prompt_current)
    time.sleep(0.1)
    with open(f"{output_folder}{prompts[index]['name']}-prompt.xml", "w", encoding="utf-8") as f:
        f.write(full_prompt)

    print(f"Querying {prompts[index]['model_name']}")

    # Query the model
    if MODEL_CONFIG[prompts[index]["model_name"]]["type"] == "anthropic":
        llmdat = query_claude(
            model_name=prompts[index]["model_name"],
            full_prompt=full_prompt,
            system_prompt=system_prompt_current,
            max_tokens=prompts[index]["max_tokens"],
            temperature=config["temperature"],
            thinking_budget=prompts[index]["thinking_budget"]
        )
    else:
        llmdat = query_openai(
            model_name=prompts[index]["model_name"],
            full_prompt=full_prompt,
            system_prompt=system_prompt_current,
            max_tokens=prompts[index]["max_tokens"],
        )

    # save the response
    with open(f"{output_folder}{prompts[index]['name']}-response.md", "w", encoding="utf-8") as f:
        f.write(llmdat["response"])

    print(f"Converting to LaTeX")

    # Convert to LaTeX
    latex_model = "haiku"
    par_per_chunk = 5
    llmdat_texinput = response_to_texinput(
        response_raw=llmdat["response"],
        par_per_chunk=par_per_chunk,
        model_name=latex_model
    )

    # Save texinput
    texinput_file = f"{output_folder}{prompts[index]['name']}-texinput.tex"
    with open(texinput_file, 'w', encoding='utf-8') as file:
        file.write(llmdat_texinput["response"])
    print(f"LaTeX input saved to {texinput_file}")

    # Convert to PDF    
    compile_result = texinput_to_pdf(llmdat_texinput["response"], f"{prompts[index]['name']}-latex", output_folder)

    # if the conversion fails, use sonnet to convert to latex
    if compile_result != 0:
        print("LaTeX conversion failed, using sonnet to convert to latex")
        llmdat_texinput = response_to_texinput(
            response_raw=llmdat["response"],
            par_per_chunk=par_per_chunk,
            model_name="sonnet"
        )
        texinput_to_pdf(llmdat_texinput["response"], f"{prompts[index]['name']}-latex", output_folder)    
        
    # here i'm lazy and don't separate the saving
    save_costs(prompts, index, llmdat, llmdat_texinput, latex_model, output_folder)


    print("================================================")

#%%
# AGGREGATE COSTS

import glob
from io import StringIO

# remove all-costs.txt if it exists
if os.path.exists(f"{output_folder}all-costs.txt"):
    os.remove(f"{output_folder}all-costs.txt")

# find all *-costs.txt files
costs_files = glob.glob(f"{output_folder}*-costs.txt")

costs_df = pd.DataFrame()
for file in costs_files:
    with open(file, "r", encoding="utf-8") as f:
        text = f.read()

    # remove comma, dollar sign
    text = text.replace(",", "").replace("$", "")

    # convert to dataframe
    df = pd.read_csv(StringIO(text), delim_whitespace=True)

    # get just the filename without the path
    file_clean = os.path.basename(file)
    df.insert(0, 'filename', file_clean)

    # append to costs_df
    costs_df = pd.concat([costs_df, df])
    

# save costs to file
grand_total = costs_df['Total_Cost'].sum()
with open(f"{output_folder}all-costs.txt", "w", encoding="utf-8") as f:
    f.write(f"Grand Total: ${grand_total:.4f}\n")
    f.write(costs_df.to_string(index=False))

