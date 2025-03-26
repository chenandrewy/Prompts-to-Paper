#%%
# Setup

import os
import sys
import replicate
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd
import anthropic  # Add anthropic import
from utils import MODEL_CONFIG, print_wrapped, assemble_prompt, query_claude, query_openai, convert_to_texinput, texinput_to_pdf
from utils import save_costs, aggregate_costs
import yaml
import logging
from importlib import reload

# User
# plan_name = "prompts-try2"
# plan_name = "prompts-try1"
plan_name = "prompts-test"

#%%
# SETUP

# Load all config and prompts
with open(f"{plan_name}.yaml", "r") as f:
    temp = yaml.safe_load(f)

config = temp["config"]
prompts = temp["prompts"]



#%%
# LOOP OVER PROMPTS

# At the start of the script, before the loop
# Initialize an empty list to store all cost dictionaries
all_costs = []

index_start = config["run_range"]["start"]-1
index_end = min(config["run_range"]["end"]-1, len(prompts)-1)


# loop over plan prompts
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
    prev_responses = [f"./responses/{fname}-response.md" for fname in prev_responses]


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
   
    # save the prompt
    with open(f"./responses/{prompts[index]['name']}-prompt.xml", "w", encoding="utf-8") as f:
        f.write(full_prompt)


    print(f"Querying {prompts[index]['model_name']}")

    # Query the model
    if MODEL_CONFIG[prompts[index]["model_name"]]["type"] == "anthropic":
        llmdat = query_claude(
            model_name=prompts[index]["model_name"],
            full_prompt=full_prompt,
            system_prompt=config["system_prompt"],
            max_tokens=prompts[index]["max_tokens"],
            temperature=config["temperature"],
            thinking_budget=prompts[index]["thinking_budget"]
        )
    else:
        llmdat = query_openai(
            model_name=prompts[index]["model_name"],
            full_prompt=full_prompt,
            system_prompt=config["system_prompt"],
            max_tokens=prompts[index]["max_tokens"],
        )

    # save the response
    with open(f"./responses/{prompts[index]['name']}-response.md", "w", encoding="utf-8") as f:
        f.write(llmdat["response"])

    print(f"Converting to LaTeX")

    # Convert to LaTeX
    latex_model = "haiku"
    par_per_chunk = 10
    llmdat_texinput = convert_to_texinput(
        response_raw=llmdat["response"],
        par_per_chunk=par_per_chunk,
        model_name=latex_model
    )

    # Save texinput
    texinput_file = f"./responses/{prompts[index]['name']}-texinput.tex"
    with open(texinput_file, 'w', encoding='utf-8') as file:
        file.write(llmdat_texinput["response"])
    print(f"LaTeX input saved to {texinput_file}")

    # Convert to PDF    
    texinput_to_pdf(llmdat_texinput["response"], f"{prompts[index]['name']}-latex")

    # here i'm lazy and don't separate the saving
    save_costs(prompts, index, llmdat, llmdat_texinput, latex_model)


    print("================================================")

#%%
# aggregate costs

import glob
from io import StringIO

# remove all-costs.txt if it exists
if os.path.exists("./responses/all-costs.txt"):
    os.remove("./responses/all-costs.txt")

# find all *-costs.txt files
costs_files = glob.glob("./responses/*-costs.txt")

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
with open(f"./responses/all-costs.txt", "w", encoding="utf-8") as f:
    f.write(f"Grand Total: ${grand_total:.4f}\n")
    f.write(costs_df.to_string(index=False))
