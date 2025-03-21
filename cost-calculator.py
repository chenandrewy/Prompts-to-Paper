#%%
import pandas as pd
import numpy as np

# -- check spending --
MODEL_PRICES = {
    "sonnet": {
        "input":   3.0*10**-6,  # $3 per M tokens
        "output": 15.0*10**-6,  # $15 per M tokens
    },
    "haiku": {
        "input": 0.8*10**-6,   
        "output": 4.0*10**-6,  
    }
}

# set model
model = "sonnet"

# per call
input_tokens = 10000
output_tokens = 4000

cost_per_call = MODEL_PRICES[model]["input"] * input_tokens + MODEL_PRICES[model]["output"] * output_tokens

calls_per_paper = 5

cost_per_paper = cost_per_call * calls_per_paper

num_papers = 10

total_cost = cost_per_paper * num_papers

print(f"Model: {model}")
print(f"Cost per paper: ${cost_per_paper:.2f}")
print(f"Cost for {num_papers} papers: ${total_cost:.2f}")

