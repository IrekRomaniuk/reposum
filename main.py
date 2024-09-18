import os
import yaml
import openai
import pandas as pd
from dotenv import load_dotenv
from github import Github

# Load .env file
load_dotenv()

# GitHub token and OpenAI API key
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Initialize GitHub and OpenAI
g = Github(GITHUB_TOKEN)
openai.api_key = OPENAI_API_KEY

# Load repository names from the YAML file
with open('repos.yaml', 'r') as file:
    config = yaml.safe_load(file)

repos = config['repositories']

# Function to call LLM and get function details using ChatCompletion
def get_function_summary(code_snippet):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a Python code analyzer."},
                {"role": "user", "content": f"Summarize the following Python function and provide its name, input parameters, output, and a brief description:\n\n{code_snippet}"}
            ],
            max_tokens=150,
            temperature=0.5
        )
        return response['choices'][0]['message']['content'].strip()
    except openai.error.InvalidRequestError as e:
        return f"Invalid request error: {e}"
    except Exception as e:
        return f"An error occurred: {str(e)}"

# Initialize list to hold function details
function_details = []

# Process each repository
for repo_name in repos:
    try:
        repo = g.get_repo(repo_name)
        contents = repo.get_contents("")

        while contents:
            file_content = contents.pop(0)
            if file_content.type == "dir":
                contents.extend(repo.get_contents(file_content.path))
            elif file_content.name.endswith(".py"):  # Only analyze Python files
                file_data = repo.get_contents(file_content.path).decoded_content.decode("utf-8")
                
                # Split the file data into functions (basic parsing, real parsing can be enhanced)
                for line in file_data.splitlines():
                    if line.startswith("def "):
                        func_name = line.split('(')[0].replace("def ", "")
                        summary = get_function_summary(line)
                        function_details.append({
                            "Repository": repo_name,
                            "Function Name": func_name,
                            "Description": summary
                        })

    except Exception as e:
        print(f"Error processing repository {repo_name}: {e}")

# Convert function details to DataFrame and save to CSV
df = pd.DataFrame(function_details)
df.to_csv("functions_summary.csv", index=False)

print("Function summary table created and saved to 'functions_summary.csv'.")
