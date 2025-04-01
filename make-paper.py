#%%
# SETUP

import os
import sys
import replicate
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd
from utils import MODEL_CONFIG, print_wrapped, assemble_prompt, query_claude, query_openai, response_to_texinput, texinput_to_pdf
from utils import save_costs, aggregate_costs
import yaml
import logging
from importlib import reload
import re
import time

# User
plan_name = "plan5-streamlined"

# Define and set up output folder
temp_num, temp_name = plan_name.split("plan")[1].split("-")  # will give you "4" and "piecemeal"
output_folder = f"./output{temp_num}-{temp_name}/"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

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

# feedback
print("==== FEEDBACK ====")
print(f"Running plan {plan_name} from prompt {index_start+1} to prompt {index_end+1}")

# loop over prompts
for index in range(index_start, index_end+1):    
# for index in [0]:
    
    print("==== FEEDBACK ====")
    print(f"Processing prompt number {index+1}...")
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

    # Get max_tokens, thinking_budget, and use_system_prompt from prompt or use defaults
    max_tokens = prompts[index].get("max_tokens", config["max_tokens"])
    thinking_budget = prompts[index].get("thinking_budget", config["thinking_budget"])
    use_system_prompt = prompts[index].get("use_system_prompt", config["use_system_prompt"])
   
    # by default, use system prompt
    if use_system_prompt:
        system_prompt_current = config["system_prompt"]
    else:
        # do not use system prompt if use_system_prompt is false
        system_prompt_current = ""
   
    # save the prompt
    with open(f"{output_folder}{prompts[index]['name']}-system-prompt.xml", "w", encoding="utf-8") as f:
        f.write(system_prompt_current)
    time.sleep(0.1)
    with open(f"{output_folder}{prompts[index]['name']}-prompt.xml", "w", encoding="utf-8") as f:
        f.write(full_prompt)

    print("==== FEEDBACK ====")
    print(f"Querying {prompts[index]['model_name']}")

    # Query the model
    if MODEL_CONFIG[prompts[index]["model_name"]]["type"] == "anthropic":
        llmdat = query_claude(
            model_name=prompts[index]["model_name"],
            full_prompt=full_prompt,
            system_prompt=system_prompt_current,
            max_tokens=max_tokens,
            temperature=config["temperature"],
            thinking_budget=thinking_budget
        )
    else:
        llmdat = query_openai(
            model_name=prompts[index]["model_name"],
            full_prompt=full_prompt,
            system_prompt=system_prompt_current,
            max_tokens=max_tokens,
        )

    # save the response
    with open(f"{output_folder}{prompts[index]['name']}-response.md", "w", encoding="utf-8") as f:
        f.write(llmdat["response"])


    if config["convert_all_latex"]:
        print("==== FEEDBACK ====")
        print(f"Converting to LaTeX")

        # Convert to LaTeX
        latex_model = "haiku"
        par_per_chunk = 5
        if lit_files == []:
            bibtex_input = None
        else:
            bibtex_input = "./lit-context/bibtex-all.bib"

        llmdat_texinput = response_to_texinput(
            response_raw=llmdat["response"],
            par_per_chunk=par_per_chunk,
            model_name=latex_model,
            bibtex_raw=bibtex_input
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

    else:
        print("==== FEEDBACK ====")
        print(f"Skipping LaTeX conversion")

        latex_model = "NA"
    
        # create llmdat_texinput with zero costs
        llmdat_texinput = {
            "response": "NA",
            "input_tokens": 0,
            "output_tokens": 0,
            "input_cost": 0.0,
            "output_cost": 0.0,
            "total_cost": 0.0
        }

    # here i'm lazy and don't separate the saving
    save_costs(prompts, index, llmdat, llmdat_texinput, latex_model, output_folder)

#%%
# Compile Full Paper Latex (if specified in yaml)

import shutil
from utils import tex_to_pdf
last_prompt_name = prompts[index_end]['name']

if "full-paper" in last_prompt_name:
    print("==== FEEDBACK ====")
    print(f"Compiling full paper LaTeX")

    # read in the full paper md response
    with open(f"{output_folder}{last_prompt_name}-response.md", "r", encoding="utf-8") as f:
        full_paper_md = f.read()

    # remove everything between \documentclass and \end{document}
    i_start = full_paper_md.find("\\documentclass")
    i_end = full_paper_md.find("\\end{document}") + len("\\end{document}")
    full_paper_md = full_paper_md[i_start:i_end]

    # save the full paper md
    with open(f"{output_folder}{last_prompt_name}-cleaned.tex", "w", encoding="utf-8") as f:
        f.write(full_paper_md)

    # compile the full paper
    compile_result = tex_to_pdf(f"{last_prompt_name}-cleaned", output_folder)

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
    df = pd.read_csv(StringIO(text), sep=r'\s+')

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
