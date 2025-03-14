#%%
import os
import glob
import anthropic
import time
import textwrap
from dotenv import load_dotenv

# Load environment variables (API key)
load_dotenv()

# Initialize Anthropic client
client = anthropic.Anthropic()

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

def convert_to_bibtex(lit_overview):
    """
    Sends a literature overview to Claude and asks it to convert to BibTeX format.
    
    Args:
        lit_overview (str): The text of the literature overview.
        
    Returns:
        str: The BibTeX entries for the paper.
    """
    instructions = """
    Convert the following literature overview into BibTeX entries. 
    Include authors, title, journal/conference, year, volume, pages, DOI, if available. Be careful to use only the information provided in the literature overview. Do not change any author names, years, titles, or journal names. Return ONLY the BibTeX entries, nothing else. Format the bibtex entries as [first author][year][title first word], all lowercase, e.g. "chen2025singularity".
    """
    
    message = f"""
    {instructions}
    
    LITERATURE OVERVIEW:
    {lit_overview}
    """
    
    print(f"Sending request to Claude for lit overview: {lit_overview[:1000]}...")

    # save message to temp/message-lit-to-bibtex.txt
    with open("./temp/message-lit-to-bibtex.txt", "w", encoding="utf-8") as f:
        f.write(message)
    
    # Start timer
    start_time = time.time()
    
    # Query Claude
    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=5000,
        temperature=0.2,
        messages=[
            {"role": "user", "content": message}
        ]
    )
    
    # End timer
    end_time = time.time()
    print(f"Time taken: {round((end_time - start_time), 2)} seconds")
    
    return response.content[0].text.strip()

#%%
# Main 1: Setup

# Create temp directory if it doesn't exist
os.makedirs("./temp", exist_ok=True)

# Gather all bib*.txt files from prompts directory
bib_files = sorted(glob.glob("./prompts/lit-*.txt"))

# remove lit-99-bibtex.txt from list
bib_files = [f for f in bib_files if "lit-99-bibtex.txt" not in f]

print(f"Found {len(bib_files)} bibliography files.")


#%%
# Main 2: Convert to BibTeX

# Process each file and collect BibTeX entries
all_bibtex = []

for file_path in bib_files:
    file_name = os.path.basename(file_path)
    print(f"\nProcessing {file_name}...")
    
    with open(file_path, "r", encoding="utf-8") as f:
        lit_overview = f.read().strip()
    
    if not lit_overview:
        print(f"Skipping empty file: {file_name}")
        continue
    
    bibtex_claude = convert_to_bibtex(lit_overview)        

    all_bibtex.append(f"% From {file_name}\n{bibtex_claude}\n")

#%%

# clean up output

all_bibtex_clean = []

for bibtex in all_bibtex:
    # remove any lines with ```
    bibtex_clean = "\n".join([line for line in bibtex.split("\n") if "```" not in line])
    all_bibtex_clean.append(bibtex_clean)


#%%
# save to file

# save for prompt
output_path1 = "./prompts/lit-99-bibtex.txt"
with open(output_path1, "w", encoding="utf-8") as f:
    f.write("\n\n".join(all_bibtex_clean))

# save for latex input
output_path2 = "./input-other/lit-99-bibtex.bib"
with open(output_path2, "w", encoding="utf-8") as f:
    f.write("\n\n".join(all_bibtex_clean))        

print(f"\nAll BibTeX entries have been saved to {output_path1} and {output_path2}")



