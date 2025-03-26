#%%
# 2025 03 25 sketching out a cleaner process


import anthropic
from openai import OpenAI
from utils import calculate_costs, print_wrapped
import os

max_tokens = 20000
thinking_budget = 4000

model_name = "o1"
temperature = 0.5

system_prompt = """
You are an asset pricing theorist. You think carefully with mathematics and check your work, step by step. 

Your team is writing a paper with a simple point: the high valuations of AI stocks could be in part because they hedge against a negative AI singularity (an explosion of AI development that is devastating for the representative investor). Since the AI singularity is inherently unpredictable, the paper is more qualitative than quantitative. 

The research team is non-traditional and skeptical of economic theory. The writing should reflect this skepticism. Write in a style that is conversational, concise, and direct.

Respond with only new content. Do not repeat anything in the context.  
"""    

system_prompt = None

# easy prompt
# instructions = """
# consider a simplified barro rietz disaster risk asset pricing model. Consumption growth is either 0 or -b, i.i.d. CRRA utility. Infinite horizon. Consider an asset that pays consumption if there is no disaster, and F times consumption if there is a disaster. is the price/consumption ratio of this asset constant? Is the price/dividend ratio constant? 
# """

# harder
instructions = """
Write down a simple model to prove the point: the high valuations of AI stocks could be in part because they hedge against a negative AI singularity. The model can be very simple but it must be infinite horizon, quantitative, and incorporate risk aversion. Use parameter values that prove the point.
"""

context_files = None

# docs: 
# https://docs.anthropic.com/en/docs/about-claude/models/all-models?q=sonnet+maximum+input#model-names
# I don't understand why haiku errors if I input for more than 8192 tokens.

MODEL_CONFIG = {
    "sonnet": {
        "input":   3.0*10**-6,  # $3 per M tokens
        "output": 15.0*10**-6,  # $15 per M tokens
        "type": "anthropic",
        "full_name": "claude-3-7-sonnet-20250219",
        "max_output_tokens": 8192,
        "max_thinking_tokens": 8192
    },
    "haiku": {
        "input": 0.8*10**-6,   
        "output": 4.0*10**-6,
        "type": "anthropic",
        "full_name": "claude-3-5-haiku-20241022",
        "max_output_tokens": 8192,
        "max_thinking_tokens": 0
    },
    "o1": {
        "input": 15.0*10**-6,   
        "output": 60.0*10**-6,  
        "type": "openai",
        "full_name": "o1",
        "max_output_tokens": 8192,
        "max_thinking_tokens": 0 # does not apply
    },
    "o3-mini": {
        "input":   1.10*10**-6,   
        "output": 4.40*10**-6,  
        "type": "openai",
        "full_name": "o3-mini",
        "max_output_tokens": 8192,
        "max_thinking_tokens": 0 # does not apply
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
            if file.startswith('@'):
                file_path = file[1:]  # Remove @ symbol
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        prompt_parts.append(f"<context>\n{content}\n</context>")
                except FileNotFoundError:
                    print(f"Warning: Context file {file_path} not found")
    
    # Add instructions
    prompt_parts.append(f"<instructions>\n{instructions}\n</instructions>")
    
    return "\n\n".join(prompt_parts)

def query_claude(model_name, instructions, max_tokens, temperature, system_prompt, thinking_budget, context_files=None):
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    # set the model config
    config = MODEL_CONFIG[model_name]
    model_full_name = config["full_name"]
    max_tokens = min(max_tokens, config["max_output_tokens"])
    thinking_budget = min(thinking_budget, config["max_thinking_tokens"])

    # assemble the prompt
    full_prompt = assemble_prompt(instructions, context_files)

    # set llm input parameters
    params = {
        "model": model_full_name,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "system": system_prompt,
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

def query_openai(model_name, instructions, max_tokens, system_prompt, context_files=None):
    client = OpenAI()

    full_prompt0 = assemble_prompt(instructions, context_files)

    # add system prompt before full_prompt0 with tags
    full_prompt = f"<system>\n{system_prompt}\n</system>\n\n<user>\n{full_prompt0}\n</user>"

    params = {
        "model": MODEL_CONFIG[model_name]["full_name"],
        "max_completion_tokens": max_tokens,
        "messages": [
            {
                "role": "user", 
                "content": full_prompt
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

#%%
# Main execution
print(f"Model: {model_name}")
print(f"Temperature: {temperature}")
print(f"Max tokens: {max_tokens}")
print(f"Instructions: {instructions}")

# assemble the prompt
full_prompt = assemble_prompt(instructions, context_files)

# query the model
if MODEL_CONFIG[model_name]["type"] == "anthropic":
    llmdat = query_claude(model_name, full_prompt, max_tokens, temperature, system_prompt, thinking_budget)
else:
    llmdat = query_openai(model_name, full_prompt, max_tokens, system_prompt)

# save to disk
with open('./responses/test-openai-texinput.md', 'w', encoding='utf-8') as f:
    f.write(llmdat['response'])

# feedback to log / console
print_wrapped(llmdat['response'])
print(f"\nToken Usage:")
print(f"Input tokens: {llmdat['input_tokens']}")
print(f"Output tokens: {llmdat['output_tokens']}")
print(f"\nCosts:")
print(f"Input cost: ${llmdat['input_cost']:.6f}")
print(f"Output cost: ${llmdat['output_cost']:.6f}")
print(f"Total cost: ${llmdat['total_cost']:.6f}")

#%%

prompt_tex = f"""
<context>
{llmdat['response']}
</context>

<instructions>
convert the document to latex. 
</instructions>
"""

#%%

# use an llm to convert to latex
llmdat_tex = query_claude('sonnet', prompt_tex, 20000, 0.2, system_prompt = "Output only latex code. Include preamble and document tags. Preserve all original text.", thinking_budget = None)

#%%

# remove all lines before \documentclass and after \end{document}
tex_content = llmdat_tex['response']
tex_lines = tex_content.split('\n')
start_idx = next(i for i, line in enumerate(tex_lines) if r'\documentclass' in line)
end_idx = next(i for i, line in enumerate(tex_lines) if r'\end{document}' in line) + 1
llmdat_tex_output = '\n'.join(tex_lines[start_idx:end_idx])

#%%

# save to disk
with open('./responses/sketch-cleaner-converted.tex', 'w', encoding='utf-8') as f:
    f.write(llmdat_tex_output)

#%%

# build the pdf

# -- compile --
compile_command = f"pdflatex -interaction=nonstopmode -halt-on-error -output-directory=./responses ./responses/sketch-cleaner-converted.tex"
os.system(compile_command)

#%%
# print costs of o1 query
print(f"Input cost: ${llmdat['input_cost']:.6f}")
print(f"Output cost: ${llmdat['output_cost']:.6f}")
print(f"Total cost: ${llmdat['total_cost']:.6f}")

# print costs of haiku query
print(f"Input cost: ${llmdat_tex['input_cost']:.6f}")
print(f"Output cost: ${llmdat_tex['output_cost']:.6f}")
print(f"Total cost: ${llmdat_tex['total_cost']:.6f}")




