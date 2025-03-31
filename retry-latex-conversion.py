#%% 
from utils import response_to_texinput, texinput_to_pdf
from dotenv import load_dotenv
load_dotenv()

# User
output_folder = "output-o1/"
response_name = "02-simplified-model"

#%%

# Read the existing response
with open(f"{output_folder}/{response_name}-response.md", "r", encoding="utf-8") as f:
    response = f.read()

# Convert to LaTeX
latex_model = "haiku"
par_per_chunk = 5
llmdat_texinput = response_to_texinput(
    response_raw=response,
    par_per_chunk=par_per_chunk,
    model_name=latex_model
)

#%%

# Save texinput
with open(f"{output_folder}/{response_name}-texinput.tex", "w", encoding="utf-8") as f:
    f.write(llmdat_texinput["response"])

#%%

# Convert to PDF    
texinput_to_pdf(llmdat_texinput["response"], f"{response_name}-latex", output_folder)

