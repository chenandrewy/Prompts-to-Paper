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

def convert_to_bibtex(paper_text):
    """
    Sends a paper description to Claude and asks it to convert to BibTeX format.
    
    Args:
        paper_text (str): The text description of the paper.
        
    Returns:
        str: The BibTeX entry for the paper.
    """
    instructions = """
    Convert the following literature overview into a proper BibTeX entry. 
    Include all available information such as authors, title, journal/conference, year, volume, pages, DOI, etc.
    Return ONLY the BibTeX entry, nothing else.
    Be careful to use only the information provided in the literature overview. Do not change any author names, years, titles, or journal names.
    """
    
    message = f"""
    {instructions}
    
    LITERATURE OVERVIEW:
    {paper_text}
    """
    
    print(f"Sending request to Claude for paper: {paper_text[:100]}...")

    # save message to temp/message-bib-to-bibtex.txt
    with open("./temp/message-bib-to-bibtex.txt", "w", encoding="utf-8") as f:
        f.write(message)
    
    # Start timer
    start_time = time.time()
    
    # Query Claude
    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=1000,
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
def main():
    # Create temp directory if it doesn't exist
    os.makedirs("./temp", exist_ok=True)
    
    # Gather all bib*.txt files from prompts directory
    bib_files = sorted(glob.glob("./prompts/bib-*.txt"))
    
    if not bib_files:
        print("No bibliography files found in ./prompts/ directory.")
        return
    
    print(f"Found {len(bib_files)} bibliography files.")
    
    # Process each file and collect BibTeX entries
    all_bibtex = []
    
    for file_path in bib_files:
        file_name = os.path.basename(file_path)
        print(f"\nProcessing {file_name}...")
        
        with open(file_path, "r", encoding="utf-8") as f:
            paper_text = f.read().strip()
        
        if not paper_text:
            print(f"Skipping empty file: {file_name}")
            continue
        
        bibtex_entry = convert_to_bibtex(paper_text)
        all_bibtex.append(f"% From {file_name}\n{bibtex_entry}\n")
    
    # save for prompt
    output_path1 = "./prompts/bib-99-bibtex.txt"
    with open(output_path1, "w", encoding="utf-8") as f:
        f.write("\n\n".join(all_bibtex))

    # save for latex input
    output_path2 = "./input-other/bib-99-bibtex.bib"
    with open(output_path2, "w", encoding="utf-8") as f:
        f.write("\n\n".join(all_bibtex))        
    
    print(f"\nAll BibTeX entries have been saved to {output_path1} and {output_path2}")

if __name__ == "__main__":
    main() 