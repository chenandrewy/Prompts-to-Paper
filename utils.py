"""
Utility functions for the Prompts-to-Paper project.
"""

import os
import textwrap
import pandas as pd
import anthropic
from openai import OpenAI
import glob
import time
import re

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

# functions

# docs: 
# https://docs.anthropic.com/en/docs/about-claude/models/all-models?q=sonnet+maximum+input#model-names
# https://platform.openai.com/docs/guides/reasoning?api-mode=chat

MODEL_CONFIG = {
    "sonnet": {
        "input":   3.0*10**-6,  # $3 per M tokens
        "output": 15.0*10**-6,  # $15 per M tokens
        "type": "anthropic",
        "full_name": "claude-3-7-sonnet-20250219",
        "max_output_tokens": 64000
    },
    "haiku": {
        "input": 0.8*10**-6,   
        "output": 4.0*10**-6,
        "type": "anthropic",
        "full_name": "claude-3-5-haiku-20241022",
        "max_output_tokens": 8192
    },
    "o1": {
        "input": 15.0*10**-6,   
        "output": 60.0*10**-6,  
        "type": "openai",
        "full_name": "o1",
        "max_output_tokens": 8192
    },
    "o3-mini": {
        "input":   1.10*10**-6,   
        "output": 4.40*10**-6,  
        "type": "openai",
        "full_name": "o3-mini",
        "max_output_tokens": 8192
    }
}


def assemble_prompt(instructions, context_files=None):
    """
    Assembles a prompt from instructions and optional context files
    Args:
        instructions (str): The main instructions/query
        context_files (list): Optional list of context file paths starting with @
    Returns:
        str: Assembled prompt
    """
    prompt_parts = []
    
    # Add context if provided
    if context_files:
        for file in context_files:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                prompt_parts.append(f"<context name=\"{file}\">\n{content}\n</context>")
    
    # Add instructions
    prompt_parts.append(f"<instructions>\n{instructions}\n</instructions>")
    
    return "\n\n".join(prompt_parts)

def query_claude(model_name, full_prompt, system_prompt, max_tokens, thinking_budget, temperature):
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    # set the model config
    config = MODEL_CONFIG[model_name]
    model_full_name = config["full_name"]
    max_tokens = min(max_tokens, config["max_output_tokens"])

    # set llm input parameters
    params = {
        "model": model_full_name,
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

    # set system prompt if enabled
    if system_prompt:
        params["system"] = system_prompt

    # set thinking budget if enabled
    if thinking_budget > 0:
        params["thinking"] = {
            "type": "enabled",
            "budget_tokens": thinking_budget
        }
        params["temperature"] = 1.0

    response = ""
    with client.messages.stream(**params) as stream:
        for text in stream.text_stream:
            response += text
            print(text, end='', flush=True)

    final_response = stream.get_final_message()
    
    # Calculate costs
    input_cost = final_response.usage.input_tokens * config["input"]
    output_cost = final_response.usage.output_tokens * config["output"]
    total_cost = input_cost + output_cost
    
    return {
        "response": response,
        "input_tokens": final_response.usage.input_tokens,
        "output_tokens": final_response.usage.output_tokens,
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": total_cost
    }

def query_openai(model_name, full_prompt, system_prompt, max_tokens):
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    # add system prompt before full_prompt with tags
    full_prompt2 = f"<system>\n{system_prompt}\n</system>\n\n<user>\n{full_prompt}\n</user>"

    params = {
        "model": MODEL_CONFIG[model_name]["full_name"],
        "max_completion_tokens": max_tokens,
        "messages": [
            {
                "role": "user", 
                "content": full_prompt2
            }
        ]
    }

    final_response = client.chat.completions.create(**params)
    
    # Calculate costs
    config = MODEL_CONFIG[model_name]
    input_cost = final_response.usage.prompt_tokens * config["input"]
    output_cost = final_response.usage.completion_tokens * config["output"]
    total_cost = input_cost + output_cost

    return {
        "response": final_response.choices[0].message.content,
        "input_tokens": final_response.usage.prompt_tokens,
        "output_tokens": final_response.usage.completion_tokens,
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": total_cost
    }

def response_to_texinput(response_raw, par_per_chunk=4, model_name="haiku", bibtex_raw='./lit-context/bibtex-all.bib'):
    """
    Converts raw text response to latex format using an LLM
    
    Args:
        response_raw (str): Raw text to convert to latex
        par_per_chunk (int): Number of sections to combine into each chunk
        model_name (str): Name of the model to use for conversion
        bibtex_raw (str): Path to bibtex file to use for citations
    Returns:
        dict: Contains converted latex response and usage statistics
    """
    # Initialize return structure
    llmdat_tex = {
        "response": "",
        "input_tokens": 0,
        "output_tokens": 0,
        "input_cost": 0.0,
        "output_cost": 0.0,
        "total_cost": 0.0
    }

    # Replace section numbers in headers (e.g., # 2. Model or ### 2.1 Model Setup)
    response_raw = re.sub(r'(#{1,3})\s+\d+\.?\d*\.?\s+', r'\1 ', response_raw)
    
    # -- chunk the response into sections --
    sections = re.findall(r'(#|##|###)\s+(.*?)(?=\n(?:#|##|###)|$)', response_raw, re.DOTALL)
    
    # concat the # with the section
    sections = [f"{section[0]} {section[1]}" for section in sections]

    # if no sections, split with paragraphs
    if len(sections) == 0:
        paragraphs = response_raw.split('\n\n')
        par_per_chunk = min(par_per_chunk, len(paragraphs))
        sections = [paragraphs[i:i+par_per_chunk] for i in range(0, len(paragraphs), par_per_chunk)]

    # read in the bibtex file (if supplied)
    if bibtex_raw:
        with open(bibtex_raw, 'r', encoding='utf-8') as f:
            bibtex_content = f.read()
    else:
        bibtex_content = ""
    
    tex_sections = []
    for i, section in enumerate(sections):
        print(f"  converting section {i+1} of {len(sections)}")
        
        prompt_tex = f"""
        <input-document>
        {section}
        </input-document>

        <bibtex>
        {bibtex_content}
        </bibtex>

        <instructions>
        Convert the input-document to latex. Respond with only latex input (no document environment). 

        Convert markdown headings to latex headings. # becomes \\section, ## becomes \\subsection, ### becomes \\subsubsection. 
       
        Use align environments for standalone math and dollar signs for in-line math. I repeat, make sure any math expressions are enclosed in either align environments or dollar signs. 

        Remove all unicode characters. pdflatex does not support unicode characters. Make sure to replace ★ (U+2605), ₀ (U+2080), • (U+2022). ₜ (U+209C) should be replaced with _t and enclosed in either align environments or dollar signs.
        
        If there are references in the input-document, cite from the bibtex file using \\citet{{}} and \\citep{{}}. Do not add references that are not in the input-document.

        Preserve all original text from the input-document. Do not add any text. 
        </instructions>
        """

        # use an llm to convert to latex
        temp_out = query_claude(
            model_name, 
            prompt_tex, 
            max_tokens=20000, 
            temperature=0.2, 
            system_prompt="Output only latex code.", 
            thinking_budget=0
        )

        # accumulate the costs and tokens
        llmdat_tex["input_tokens"] += temp_out["input_tokens"]
        llmdat_tex["output_tokens"] += temp_out["output_tokens"]
        llmdat_tex["input_cost"] += temp_out["input_cost"]
        llmdat_tex["output_cost"] += temp_out["output_cost"]
        llmdat_tex["total_cost"] += temp_out["total_cost"]
        
        # collect the latex sections
        tex_sections.append(temp_out["response"])

    # combine all sections into final response
    llmdat_tex["response"] = "\n\n".join(tex_sections)
    
    return llmdat_tex

def texinput_to_pdf(texinput, pdf_fname, output_folder="./responses/"):    
    
    # -- plug clean texinput into latex template --
    with open("./lit-context/template.tex", "r", encoding="utf-8") as file:
        latex_template = file.read()

    # Replace the marker with the texinput instead of an \input command
    full_tex = latex_template.replace("% [input-goes-here]", texinput)

    # Ensure we write with UTF-8 encoding
    with open(f"{output_folder}{pdf_fname}.tex", "w", encoding="utf-8") as file:
        file.write(full_tex)

    # compile the paper
    compile_result = tex_to_pdf(pdf_fname, output_folder)
    
    return compile_result

def tex_to_pdf(pdf_fname, output_folder="./responses/"):

    # -- clean aux files --
    base_files = [
        f"{pdf_fname}.aux",
        f"{pdf_fname}.bbl",
        f"{pdf_fname}.blg",
        f"{pdf_fname}.out",
        f"{pdf_fname}.toc",
        f"{pdf_fname}.lof",
        f"{pdf_fname}.lot",
        f"{pdf_fname}.bcf",
        f"{pdf_fname}.run.xml"
    ]
    aux_files = [f"{output_folder}{file}" for file in base_files]

    for file in aux_files:
        if os.path.exists(file):
            os.remove(file)
    
    # -- compile --
    # Compile with bibliography support
    compile_command = f"pdflatex -interaction=nonstopmode -halt-on-error -output-directory={output_folder} {output_folder}{pdf_fname}.tex"
    print(f"Running first LaTeX pass: {compile_command}")
    os.system(compile_command)

    # Run Biber without changing directory
    biber_command = f"biber {output_folder}{pdf_fname}"
    print(f"Running Biber: {biber_command}")
    os.system(biber_command)

    # Run LaTeX again (twice) to resolve references
    print("Running second LaTeX pass...")
    os.system(compile_command)

    print("Running final LaTeX pass...")
    compile_result = os.system(compile_command)
    print(f"LaTeX compilation result: {compile_result}")

    # remove aux files 
    # pause to avoid deleting aux files too quickly
    time.sleep(0.5)

    for file in aux_files:
        if os.path.exists(file):
            os.remove(file)

    return compile_result

def save_costs(prompts, index, llmdat, llmdat_texinput, latex_model, output_folder="./responses/"):
    # save cost data for both llmdat and llmdat_texinput
    costs_data = {
        'Operation': ['Main', 'LaTeX'],
        'Model': [prompts[index]['model_name'], latex_model],
        'Input_Tokens': [llmdat['input_tokens'], llmdat_texinput['input_tokens']],
        'Output_Tokens': [llmdat['output_tokens'], llmdat_texinput['output_tokens']],
        'Input_Cost': [llmdat['input_cost'], llmdat_texinput['input_cost']],
        'Output_Cost': [llmdat['output_cost'], llmdat_texinput['output_cost']],
        'Total_Cost': [llmdat['total_cost'], llmdat_texinput['total_cost']]
    }
    
    cost_df = pd.DataFrame(costs_data)
    
    # Format numeric columns
    cost_df['Input_Tokens'] = cost_df['Input_Tokens'].apply(lambda x: f"{x:,}")
    cost_df['Output_Tokens'] = cost_df['Output_Tokens'].apply(lambda x: f"{x:,}")
    cost_df['Input_Cost'] = cost_df['Input_Cost'].apply(lambda x: f"${x:.4f}")
    cost_df['Output_Cost'] = cost_df['Output_Cost'].apply(lambda x: f"${x:.4f}")
    cost_df['Total_Cost'] = cost_df['Total_Cost'].apply(lambda x: f"${x:.4f}")

    # Save DataFrame with formatted columns
    with open(f"{output_folder}{prompts[index]['name']}-costs.txt", "w", encoding="utf-8") as f:
        f.write(cost_df.to_string(
            index=False,
            justify='left',
            col_space={
                'Operation': 10,
                'Model': 10,
                'Input_Tokens': 15,
                'Output_Tokens': 15,
                'Input_Cost': 12,
                'Output_Cost': 12,
                'Total_Cost': 12
            }
        ))        
    
    return cost_df

def aggregate_costs(output_folder="./responses/"):
    """
    Aggregates costs from all *-costs.txt files in the output directory.
    
    Args:
        output_folder (str): Directory containing the cost files
        
    Returns:
        tuple: (costs_df, grand_total) where:
            - costs_df: DataFrame containing all cost data
            - grand_total: float of total costs across all files
    """
    # find all *costs.txt files
    costs_files = glob.glob(f"{output_folder}*-costs.txt")
    
    # read all costs files into a dataframe
    costs_data = []
    for cost_file in costs_files:
        # Read the file into a DataFrame with explicit column names
        df = pd.read_csv(cost_file, delim_whitespace=True, 
                        names=['Operation', 'Model', 'Input_Tokens', 'Output_Tokens', 
                              'Input_Cost', 'Output_Cost', 'Total_Cost'])
        
        # Add filename as reference
        df['filename'] = os.path.basename(cost_file)
        
        # Clean up numeric columns - handle both string and numeric values
        for col in ['Input_Tokens', 'Output_Tokens']:
            if df[col].dtype == 'object':  # Only process if it's a string column
                df[col] = df[col].str.replace(',', '')
            df[col] = pd.to_numeric(df[col], errors='coerce')
                
        for col in ['Input_Cost', 'Output_Cost', 'Total_Cost']:
            if df[col].dtype == 'object':  # Only process if it's a string column
                df[col] = df[col].str.replace('$', '')
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        costs_data.append(df)
    
    # Combine all dataframes
    costs_df = pd.concat(costs_data, ignore_index=True)
    
    # Reorder columns to match the original format
    column_order = ['filename', 'Operation', 'Model', 'Input_Tokens', 'Output_Tokens', 
                   'Input_Cost', 'Output_Cost', 'Total_Cost']
    costs_df = costs_df[column_order]
    
    # Format numeric columns for display
    costs_df['Input_Tokens'] = costs_df['Input_Tokens'].apply(lambda x: f"{x:,.0f}")
    costs_df['Output_Tokens'] = costs_df['Output_Tokens'].apply(lambda x: f"{x:,.0f}")
    costs_df['Input_Cost'] = costs_df['Input_Cost'].apply(lambda x: f"${x:.4f}")
    costs_df['Output_Cost'] = costs_df['Output_Cost'].apply(lambda x: f"${x:.4f}")
    costs_df['Total_Cost'] = costs_df['Total_Cost'].apply(lambda x: f"${x:.4f}")
    
    # Calculate grand total using numeric values
    grand_total = pd.to_numeric(costs_df['Total_Cost'].str.replace('$', ''), errors='coerce').sum()
    
    return costs_df, grand_total
