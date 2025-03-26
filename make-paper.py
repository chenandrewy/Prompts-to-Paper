#%%
# Setup

import os
import sys
import replicate
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd
import anthropic  # Add anthropic import
from utils import MODEL_CONFIG, print_wrapped, assemble_prompt, query_claude, query_openai, response_to_texinput, texinput_to_pdf
from utils import save_costs, aggregate_costs
import yaml
import logging
from importlib import reload
import re

# User
# plan_name = "prompts-try2"
# plan_name = "prompts-try1"
plan_name = "prompts-test"

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
    par_per_chunk = 5
    llmdat_texinput = response_to_texinput(
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

#%%
# Clean Paper: tiny latex tweaks

prompt_name = prompts[len(prompts)-1]["name"]

# Load the full paper latex
with open(f"./responses/{prompt_name}-latex.tex", "r", encoding="utf-8") as f:
    paper_latex = f.read()

clean_latex = paper_latex

# -- Find Stuff --

# Find position of abstract
abstract_match = re.search(r'\\section\*\{Abstract\}', paper_latex)
abstract_pos = abstract_match.start() if abstract_match else None

# Extract abstract content
abstract = None
if abstract_match:
    abstract_content_match = re.search(
        r'\\section\*\{Abstract\}\s*(.+?)(?=\\section|\Z)', 
        paper_latex[abstract_pos:], 
        re.DOTALL
    )
    if abstract_content_match:
        abstract = abstract_content_match.group(1).strip()

# Find title
title = None
if abstract_pos:
    sections_before_abstract = list(re.finditer(r'\\section\{(.+?)\}', paper_latex[:abstract_pos]))
    if sections_before_abstract:
        title = sections_before_abstract[-1].group(1).strip()

# -- Replace Stuff --

# replace abstract with \begin{abstract} {abstract} \end{abstract}
if abstract_match:
    clean_latex = re.sub(
        r'\\section\*\{Abstract\}\s*(.+?)(?=\\section|\Z)',
        r'\\begin{abstract}\n' + abstract + r'\n\\end{abstract}\n\n',
        paper_latex,
        flags=re.DOTALL
    )

# replace title section with \title{} and \maketitle
if title:
    clean_latex = re.sub(
        r'\\section\{' + re.escape(title) + r'\}',
        r'\\title{' + title + r'}\n\n\\author{}\n\n\\date{}\n\n\\maketitle',
        clean_latex

    )

with open(f"./responses/{prompt_name}-clean.tex", "w", encoding="utf-8") as f:
    f.write(clean_latex)

# Compile the clean paper
import utils
reload(utils)

from utils import tex_to_pdf

tex_to_pdf(f"{prompt_name}-clean")
