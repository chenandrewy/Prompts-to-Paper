#%%
import os
import glob
import anthropic
import subprocess
from dotenv import load_dotenv

# Load environment variables (API key)
load_dotenv()

# Initialize Anthropic client
client = anthropic.Anthropic()

#%%
# Gather all planning*.tex files from responses directory
planning_files = glob.glob("responses/planning*.tex")

# Read content from planning files
context = ""
for file_path in planning_files:
    with open(file_path, "r") as f:
        file_content = f.read()
        file_name = os.path.basename(file_path)
        context += f"\n\nContent of {file_name}:\n{file_content}"

#%% 
# Gather all bibliography inputs
bib_files = glob.glob("input-other/bib*.txt")

bib_context = ""
for file_path in bib_files:
    with open(file_path, "r", encoding="utf-8") as f:
        file_content = f.read()
        file_name = os.path.basename(file_path)
        bib_context += f"\n\nContent of {file_name}:\n{file_content}"


#%%
main_prompt = """
Write an academic paper titled "Hedging the AI Singularity"based on the following planning and bibliography documents. Make sure all citations match actual papers in the bibliography documents. Output as md.
"""

# Construct the message
message = f"{main_prompt}\n\n Planning documents:\n{context}\n\n Bibliography:\n{bib_context}"

print("Sending request to Claude...")

# Query with streaming
with client.messages.stream(
    model="claude-3-7-sonnet-20250219",
    max_tokens=500*20,
    temperature=0.5,
    messages=[
        {"role": "user", "content": message}
    ]
) as stream:
    # Process the response as it comes in
    for text in stream.text_stream:
        # Process or display each chunk of text as it arrives
        print(text, end="", flush=True)  # For example
    
    # If you need the final complete message
    final_message = stream.get_final_message()


#%%

# save to ./responses/paper.md
with open("./responses/paper.md", "w", encoding="utf-8") as f:
    f.write(final_message.content[0].text)

#%%
# print the response nicely
# Extract the response text
response_text = response.content[0].text

# Print the response with nice formatting
print("\nResponse from Claude:")
print("-" * 80)

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

# Print the response with nice formatting
print_wrapped(response_text)
print("-" * 80)

