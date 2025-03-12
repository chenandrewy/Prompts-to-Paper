#%%

import anthropic
import textwrap

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
        print(wrapper.fill(para))
        # Print a blank line to preserve paragraph separation
        print()

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





