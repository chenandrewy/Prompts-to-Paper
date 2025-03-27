
#%%
# CLEAN PAPER: TINY LATEX TWEAKS

prompt_name = prompts[len(prompts)-1]["name"]

# Load the full paper latex
with open(f"{output_folder}{prompt_name}-latex.tex", "r", encoding="utf-8") as f:
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

with open(f"{output_folder}{prompt_name}-clean.tex", "w", encoding="utf-8") as f:
    f.write(clean_latex)

# Compile the clean paper
import utils
reload(utils)

from utils import tex_to_pdf

tex_to_pdf(f"{prompt_name}-clean", output_folder)
