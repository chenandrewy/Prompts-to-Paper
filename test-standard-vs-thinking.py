#%%

import anthropic
import textwrap
from utils import print_wrapped  # Import utility function
from dotenv import load_dotenv
import os

# Load environment variables (API key)
load_dotenv()

# Initialize Anthropic client
client = anthropic.Anthropic()

#%%

prompt = """
Consider a neoclassical model with two households who differ in their time preference. Prove that the more patient household own all capital in the steady state.
"""

#%%
# standard mode

response_standard = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=1000,
    temperature=1,
    system="You are a macroeconomic theorist. Respond only with short, concise, and clear statements.",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text", 
                    "text": prompt
                }
            ]
        }
    ]

)


#%%
# thinking mode
# https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking

response_thinking = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    thinking={
        "type": "enabled",
        "budget_tokens": 1600
    },
    max_tokens=20000,
    temperature=1,
    system="You are a macroeconomic theorist. Respond only with short, concise, and clear statements.",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text", 
                    "text": prompt
                }
            ]
        }
    ]

)


#%%
# compare
print(prompt)
print("Standard mode:")
print_wrapped(response_standard.content[0].text)
print("\n\n")

print("Thinking mode:")
print_wrapped(response_thinking.content[1].text)





