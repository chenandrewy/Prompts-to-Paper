#%%
# SETUP

import os
import sys
import replicate
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd
from utils import MODEL_CONFIG, print_wrapped, assemble_prompt, query_claude, query_openai, response_to_texinput, texinput_to_pdf

load_dotenv()

from utils import save_costs, aggregate_costs, is_jupyter
import yaml
import logging
from importlib import reload
import re
import time
import argparse


#%%
# Parse command line / hard coded arguments
plan_default = "plan0408-piecewise"

if is_jupyter():
    # User
    plan_name = plan_default
else:
    parser = argparse.ArgumentParser(description="Generate a paper from a plan")
    parser.add_argument("--plan_name", type=str, default=plan_default, help="Name of the plan to use")
    args = parser.parse_args()
    plan_name = args.plan_name

#%% 
# Set up folder and loops

# Define and set up output folder
temp_num, temp_name = plan_name.split("plan")[1].split("-") 
output_folder = f"./output{temp_num}-{temp_name}/"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Set up logging
log_file = os.path.join(output_folder, "paper_generation.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)  # This ensures output still goes to console
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"Starting paper generation for plan: {plan_name}")

# Load all config and prompts
with open(f"{plan_name}.yaml", "r") as f:
    temp = yaml.safe_load(f)

config = temp["config"]
prompts = temp["prompts"]

# Initialize
all_costs = []
index_start = config["run_range"]["start"]-1
index_end = min(config["run_range"]["end"]-1, len(prompts)-1)

#%%
# LOOP OVER PROMPTS

# feedback
logger.info("==== FEEDBACK ====")
logger.info(f"Running plan {plan_name} from prompt {index_start+1} to prompt {index_end+1}")

# loop over prompts
for index in range(index_start, index_end+1):    
# for index in [0]:
    
    logger.info("==== FEEDBACK ====")
    logger.info(f"Processing prompt number {index+1}...")
    logger.info(f"Instructions: {prompts[index]['instructions']}")

    if "lit_files" in prompts[index]:
        logger.info(f"Lit files: {prompts[index]['lit_files']}")
    
    # Previous responses context
    prev_responses = [prompt["name"] for prompt in prompts[:index]]
    prev_responses = [f"{output_folder}{fname}-response.md" for fname in prev_responses]

    # Literature context
    if "lit_files" in prompts[index]:
        lit_files = prompts[index]["lit_files"]
        lit_files = [f"./lit-context/{fname}" for fname in lit_files]
    else:
        lit_files = []

    # LaTeX files
    if "latex_files" in prompts[index]:
        latex_files = prompts[index]["latex_files"]
        latex_files = [f"./latex-input/{fname}" for fname in latex_files]
    else:
        latex_files = []

    # Generate the full prompt
    full_prompt = assemble_prompt(
        instructions=prompts[index]["instructions"],
        context_files=prev_responses + lit_files + latex_files
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

    logger.info("==== FEEDBACK ====")
    logger.info(f"Querying {prompts[index]['model_name']}")

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
        logger.info("==== FEEDBACK ====")
        logger.info(f"Converting to LaTeX")

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
        logger.info(f"LaTeX input saved to {texinput_file}")

        # Convert to PDF    
        compile_result = texinput_to_pdf(llmdat_texinput["response"], f"{prompts[index]['name']}-latex", output_folder)

        # if the conversion fails, use sonnet to convert to latex
        if compile_result != 0:
            logger.warning("LaTeX conversion failed, using sonnet to convert to latex")
            llmdat_texinput = response_to_texinput(
                response_raw=llmdat["response"],
                par_per_chunk=par_per_chunk,
                model_name="sonnet"
            )
            texinput_to_pdf(llmdat_texinput["response"], f"{prompts[index]['name']}-latex", output_folder)    

    else:
        logger.info("==== FEEDBACK ====")
        logger.info(f"Skipping LaTeX conversion")

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

# reload for easy modifications
import utils
reload(utils)
from utils import create_readme_appendix, create_appendix

import shutil
from utils import tex_to_pdf
import glob
last_prompt_name = prompts[index_end]['name']

if "full-paper" in last_prompt_name:
    logger.info("==== FEEDBACK ====")
    logger.info(f"Compiling full paper LaTeX")

    # Generate appendix first
    logger.info("Generating appendix with README...")
    create_readme_appendix()

    logger.info("Generating appendix with prompt listing...")
    create_appendix(plan_name + ".yaml")

    # copy latex-inputs to output folder
    # Copy all .tex files from latex-input to output folder
    logger.info("Copying .tex files from latex-input to output folder...")
    for tex_file in glob.glob("latex-input/*.tex"):
        shutil.copy(tex_file, output_folder)
    shutil.copy("latex-input/econstyle.sty", output_folder)

    # read in the full paper md response
    with open(f"{output_folder}{last_prompt_name}-response.md", "r", encoding="utf-8") as f:
        full_paper_md = f.read()

    # remove everything between \documentclass and \end{document}
    i_start = full_paper_md.find("\\documentclass")
    i_end = full_paper_md.find("\\end{document}") + len("\\end{document}")
    full_paper_md = full_paper_md[i_start:i_end]

    # update "../latex-input/" to "./"
    full_paper_md = full_paper_md.replace("../latex-input/", "./")

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

logger.info(f"Paper generation completed. Log saved to {log_file}")
