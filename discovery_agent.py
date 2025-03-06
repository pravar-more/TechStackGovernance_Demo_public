import os
import time
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from typing import TypedDict
from github import Github, GithubException
from langchain_core.messages import SystemMessage, HumanMessage
import pygments
from pygments.lexers import guess_lexer_for_filename, ClassNotFound

# Load environment variables from .env file
load_dotenv()

# Define configuration variables for the Azure OpenAI API
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
key = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_GPT4_DEPLOYMENT_NAME = os.getenv("AZURE_GPT4_DEPLOYMENT_NAME")

# Initialize Azure OpenAI model
model = AzureChatOpenAI(
    temperature=0.1,
    model=AZURE_GPT4_DEPLOYMENT_NAME,
    azure_endpoint=endpoint,
    openai_api_key=key,
    api_version=AZURE_OPENAI_API_VERSION
)

class AgentState(TypedDict):
    """State definition for the Discovery Agent"""
    task: str
    repo_url: str
    github_token: str
    file_tree: str
    file_contents: str
    programming_languages: str

GATHER_REPO_CONTENT_PROMPT = """
You are an expert in reading GitHub repositories. 
Generate report in around 150 to 200 words extend if required.
Your task is to:

1. Analyze repository structure and contents
2. Create a detailed file tree
3. Extract and validate file contents
4. Identify programming languages and frameworks
5. Pay special attention to:
   - Configuration files
   - Source code files
   - Test files
   - Documentation
   - Build files
   - pom.xml file
   - Dependency files

Ignore:
- Binary files
- Build output directories (target/, build/, dist/)
- IDE configuration files (.idea/, .vscode/)
- Dependency directories (node_modules/, venv/)
- System files (.git/, .DS_Store)
"""

def format_file_tree(file_tree: dict, indent: str = "") -> str:
    """Format the file tree dictionary into a readable string"""
    tree_str = ""
    for key, value in sorted(file_tree.items()):
        if value is None:
            tree_str += f"{indent}├── {os.path.basename(key)}\n"
        else:
            tree_str += f"{indent}├── {os.path.basename(key)}/\n"
            tree_str += format_file_tree(value, indent + "│   ")
    return tree_str

def gather_repo_content_node(state: AgentState) -> dict:
    """Gather content from a GitHub repository with authentication"""
    try:
        # Initialize GitHub with token
        g = Github(state["github_token"])
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # Check rate limit
                rate_limit = g.get_rate_limit()
                if rate_limit.core.remaining == 0:
                    wait_time = int(rate_limit.core.reset.timestamp() - time.time()) + 1
                    print(f"Rate limit exceeded. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue

                # Parse repository URL and get repo
                parts = state["repo_url"].rstrip('/').split('/')
                owner = parts[-2]
                repo_name = parts[-1].replace('.git', '')
                repo = g.get_repo(f"{owner}/{repo_name}")

                # Initialize containers
                file_tree = {}
                file_contents = []
                programming_languages = set()

                # Process repository contents
                contents = repo.get_contents("")
                while contents:
                    file_content = contents.pop(0)
                    
                    # Skip unwanted directories
                    if any(skip in file_content.path.lower() for skip in 
                        ['target/', 'build/', '.git/', '.idea/', 'node_modules/', 'venv/']):
                        continue

                    if file_content.type == "dir":
                        contents.extend(repo.get_contents(file_content.path))
                        current_dict = file_tree
                        for part in file_content.path.split('/'):
                            current_dict = current_dict.setdefault(part, {})
                    else:
                        try:
                            content_str = file_content.decoded_content.decode('utf-8')
                            file_contents.append(f"File: {file_content.path}\nContent:\n{content_str}\n")
                            
                            try:
                                lexer = guess_lexer_for_filename(file_content.path, content_str)
                                programming_languages.add(lexer.name)
                            except ClassNotFound:
                                print(f"No lexer found for {file_content.path}")
                                
                            # Add to file tree
                            current_dict = file_tree
                            parts = file_content.path.split('/')
                            for part in parts[:-1]:
                                current_dict = current_dict.setdefault(part, {})
                            current_dict[parts[-1]] = None

                        except UnicodeDecodeError:
                            print(f"Skipping binary file: {file_content.path}")
                            continue

                # Format results
                file_tree_str = format_file_tree(file_tree)
                file_contents_str = "\n".join(file_contents)
                programming_languages_str = ", ".join(sorted(programming_languages))

                # Generate analysis
                combined_content = (
                    f"{state['task']}\n\n"
                    f"File Tree:\n{file_tree_str}\n\n"
                    f"File Contents:\n{file_contents_str}\n\n"
                    f"Programming Languages: {programming_languages_str}"
                )

                response = model.invoke([
                    SystemMessage(content=GATHER_REPO_CONTENT_PROMPT),
                    HumanMessage(content=combined_content)
                ])

                return {
                    "file_tree": file_tree_str,
                    "file_contents": file_contents_str,
                    "programming_languages": programming_languages_str
                }

            except GithubException as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"GitHub API error. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                print(f"GitHub API error: {str(e)}")
                return None

    except Exception as e:
        print(f"Error processing repository: {str(e)}")
        return None

def run_discovery_agent(repo_url: str, github_token: str) -> dict:
    """Main entry point for the Discovery Agent"""
    print(f"Starting analysis of repository: {repo_url}")
    try:
        initial_state = {
            "task": "Analyze repository structure and contents",
            "repo_url": repo_url,
            "github_token": github_token,
            "file_tree": "",
            "file_contents": "",
            "programming_languages": ""
        }
        
        final_state = gather_repo_content_node(initial_state)
        if not final_state:
            print("Repository analysis failed")
            return None

        print(f"Analysis complete. Found languages: {final_state['programming_languages']}")    
        return final_state
        
    except Exception as e:
        print(f"Error analyzing repository: {str(e)}")
        return None
