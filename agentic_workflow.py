from langgraph.graph import StateGraph, END
from discovery_agent import run_discovery_agent
from code_analysis_agent import run_code_analysis_agent
from recommendation_agent import run_recommendation_agent
from typing import TypedDict
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Ensure the GitHub token is loaded
github_token = os.getenv("GITHUB_TOKEN")
if not github_token:
    raise ValueError("GitHub token not found in environment variables")

# Define the state machine for the agentic workflow
class AgenticWorkflowState(TypedDict):
    repo_url: str
    file_tree: str
    file_contents: str
    programming_languages: str
    analysis_result: str
    recommendations: str
    iteration: int
    pdf_path: str  # New field for PDF path

def run_discovery(state: AgenticWorkflowState):
    """Function to run the Discovery Agent"""
    try:
        # Pass the github_token to the discovery agent
        discovery_result = run_discovery_agent(state["repo_url"], github_token)
        if discovery_result:
            state["file_tree"] = discovery_result["file_tree"]
            state["file_contents"] = discovery_result["file_contents"]
            state["programming_languages"] = discovery_result["programming_languages"]
            if not state["file_contents"]:
                print("No code found in the repository.")
                return None
        else:
            print(f"Repository not found or access denied: {state['repo_url']}")
            return None
    except Exception as e:
        print(f"An error occurred while fetching the repository content: {str(e)}")
        return None
    return state

def run_code_analysis(state: AgenticWorkflowState):
    """Function to run the Code Analysis Agent"""
    if not state["file_contents"]:
        print("No code found, skipping analysis stage")
        return None
        
    analysis_result = run_code_analysis_agent(
        state["file_tree"], 
        state["file_contents"], 
        state["programming_languages"]
    )
    
    if analysis_result and "analysis_result" in analysis_result:
        state["analysis_result"] = analysis_result["analysis_result"]
        if "pdf_path" in analysis_result:
            state["pdf_path"] = analysis_result["pdf_path"]
    return state

def run_recommendation(state: AgenticWorkflowState):
    """Function to run the Recommendation Agent"""
    if not state["analysis_result"]:
        print("No analysis result available, skipping recommendations")
        return None
        
    recommendation_result = run_recommendation_agent(
        state["file_tree"], 
        state["file_contents"], 
        state["programming_languages"], 
        state["analysis_result"]
    )
    
    if recommendation_result:
        state["recommendations"] = recommendation_result.get("recommendations", "")
        if "pdf_path" in recommendation_result:
            state["pdf_path"] = recommendation_result["pdf_path"]
            return 
    return state

def should_continue(state: AgenticWorkflowState):
    """Determines if workflow should continue"""
    if state is None:
        return END
    if state.get("iteration", 0) >= 1:
        return END
    return "run_code_analysis"

# Initialize the state graph
graph_builder = StateGraph(AgenticWorkflowState)

# Add nodes
graph_builder.add_node("run_discovery", run_discovery)
graph_builder.add_node("run_code_analysis", run_code_analysis)
graph_builder.add_node("run_recommendation", run_recommendation)

# Set the entry point
graph_builder.set_entry_point("run_discovery")

# Add simple linear edges
graph_builder.add_edge("run_discovery", "run_code_analysis")
graph_builder.add_edge("run_code_analysis", "run_recommendation")
graph_builder.add_edge("run_recommendation", END)

# Compile the graph
graph = graph_builder.compile()

def run_agentic_workflow(repo_url: str, user_input: str = "", resume: bool = False):
    """Main entry point for running the workflow"""
     # Normalize the repository URL
    repo_url = repo_url.strip()
    if repo_url.endswith('/'):
        repo_url = repo_url[:-1]
    if repo_url.endswith('.git'):
        repo_url = repo_url[:-4]

    # Initialize the agent's state
    initial_state = {
        "repo_url": repo_url,
        "file_tree": "",
        "file_contents": "",
        "programming_languages": "",
        "analysis_result": "",
        "recommendations": "",
        "iteration": 0,
        "pdf_path": ""  # Initialize PDF path
    }
    
    try:
        # Run workflow
        if resume:
            initial_state["iteration"] = 1
            final_state = graph.invoke(initial_state)
        else:
            final_state = graph.invoke(initial_state)
        
        # Return final state without printing
        return final_state
        
    except Exception as e:
        print(f"An error occurred in the workflow: {str(e)}")
        return None

if __name__ == "__main__":
    repo_url = input("Enter the GitHub repository URL: ")
    result = run_agentic_workflow(repo_url)
    if result:
        print(f"Analysis and recommendations saved to: {result['pdf_path']}")