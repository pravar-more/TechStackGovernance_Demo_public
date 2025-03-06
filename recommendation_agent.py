import os
from typing import TypedDict
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langgraph.graph import StateGraph, END
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Load environment variables
load_dotenv()

# Initialize Azure OpenAI
llm = AzureChatOpenAI(
    temperature=0.1,
    model=os.getenv("AZURE_GPT4_DEPLOYMENT_NAME"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION")
)

class RecommendationState(TypedDict):
    file_tree: str
    file_contents: str
    programming_languages: str
    analysis_result: str
    recommendations: str
    iteration: int


# Define the prompt template for generating recommendations
PROMPT_TEMPLATE = """
You are Recommendations Agent (RA), an expert AI code analyst. Your task is to analyze the provided code and file structure to generate actionable recommendations.

**Input:**
* **File Tree Structure:**
    ```
    {file_tree}
    ```
* **Code Content:**
    ```
    {file_contents}
    ```
* **Programming Languages:** {programming_languages}
* **Code Analysis Report:**
    ```
    {analysis_result}
    ```

**Guardrails:**
* **Security:**
    * DO NOT expose any PII, secrets, API keys, passwords, or confidential data
    * DO NOT execute the provided code
    * Avoid suggesting dangerous operations that could introduce vulnerabilities
* **Factuality & Accuracy:**
    * Back all recommendations with evidence from the code (cite line numbers)
    * Avoid speculation - state any uncertainties clearly
    * Stay within the specified scope
* **Ethics & Bias:**
    * Use neutral and objective language
    * Avoid biases about coding styles or language preferences

**Output Format (Markdown):**
## Recommendations Report

### Summary
[Brief overview highlighting key areas for improvement]

### High Priority Recommendations
[List critical recommendations addressing security, performance, or reliability issues]

* **Issue:** [Brief description]
* **Location:** [File and line numbers]
* **Recommendation:** [Detailed steps to address]
* **Rationale:** [Why this is important]

### Medium Priority Recommendations 
[List recommendations for code quality and maintainability improvements]

* **Issue:** [Brief description]
* **Location:** [File and line numbers]
* **Recommendation:** [Steps to improve]
* **Rationale:** [Benefits of implementing]

### Low Priority Recommendations
[List minor improvements for style and optimization]

* **Issue:** [Brief description]
* **Location:** [File and line numbers]
* **Recommendation:** [Suggested changes]
* **Rationale:** [Expected benefits]

### Conclusion
[Summary of key recommendations and expected impact]
"""

def save_recommendations_to_pdf(recommendations_results, project_info, output_path="recommendation_reports"):
    """Saves recommendations to a PDF file with different text sizes for code and content"""
    os.makedirs(output_path, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(output_path, f"recommendations_{timestamp}.pdf")
    
    # Create PDF document
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=16,
        spaceAfter=30
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        spaceAfter=12
    )
    
    subheader_style = ParagraphStyle(
        'CustomSubHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        spaceAfter=10
    )
    
    content_style = ParagraphStyle(
        'CustomContent',
        parent=styles['Normal'],
        fontSize=12,
        leading=14,
        spaceAfter=10
    )
    
    code_style = ParagraphStyle(
        'CodeContent',
        parent=styles['Code'],
        fontSize=10,
        leading=12,
        fontName='Courier',
        spaceAfter=10
    )
    
    # Add title
    story.append(Paragraph("Code Recommendations Report", title_style))
    story.append(Spacer(1, 20))
    
    # Add project information
    for key, value in project_info.items():
        story.append(Paragraph(f"<b>{key}:</b> {value}", content_style))
    
    story.append(Spacer(1, 20))
    
    # Process recommendations
    for i, result in enumerate(recommendations_results, 1):
        # Add iteration header
        story.append(Paragraph(f"Recommendation Iteration {i}", header_style))
        story.append(Spacer(1, 12))
        
        # Split content into sections
        sections = result.split('\n\n')
        for section in sections:
            if section.strip():
                # Check for code blocks
                if '```' in section:
                    # Process code blocks with smaller font
                    story.append(Paragraph(section.replace('```', ''), code_style))
                # Check for headers/subheaders
                elif section.startswith('#'):
                    level = section.count('#')
                    cleaned_header = section.strip('#').strip()
                    if level <= 2:
                        story.append(Paragraph(cleaned_header, header_style))
                    else:
                        story.append(Paragraph(cleaned_header, subheader_style))
                else:
                    # Regular content with larger font
                    story.append(Paragraph(section.replace('\n', '<br/>'), content_style))
                story.append(Spacer(1, 10))
    
    # Build PDF
    doc.build(story)
    return filename

def generate_recommendations(state: RecommendationState):
    """Generates initial recommendations"""
    recommendation_prompt = PROMPT_TEMPLATE.format(
        file_tree=state['file_tree'],
        file_contents=state['file_contents'],
        programming_languages=state['programming_languages'],
        analysis_result=state['analysis_result']
    )
    response = llm.invoke([{"role": "system", "content": recommendation_prompt}])
    return {
        "recommendations": response.content, 
        "iteration": state["iteration"] + 1
    }

def reflect_on_recommendations(state: RecommendationState):
    """Reflects on previous recommendations"""
    reflection_prompt = PROMPT_TEMPLATE.format(
        file_tree=state['file_tree'],
        file_contents=state['file_contents'],
        programming_languages=state['programming_languages'],
        analysis_result=state['analysis_result']
    )
    response = llm.invoke([{"role": "system", "content": reflection_prompt}])
    return {
        "recommendations": response.content, 
        "iteration": state["iteration"] + 1
    }

def should_continue(state: RecommendationState):
    """Determines if reflection should continue"""
    if state["iteration"] >= 2:
        return END
    return "reflect_on_recommendations"

# Initialize state graph
graph_builder = StateGraph(RecommendationState)
graph_builder.add_node("generate_recommendations", generate_recommendations)
graph_builder.add_node("reflect_on_recommendations", reflect_on_recommendations)
graph_builder.set_entry_point("generate_recommendations")

# Add edges
graph_builder.add_conditional_edges(
    "reflect_on_recommendations",
    should_continue,
    {END: END, "reflect_on_recommendations": "reflect_on_recommendations"}
)
graph_builder.add_edge("generate_recommendations", "reflect_on_recommendations")

# Compile graph
graph = graph_builder.compile()

def run_recommendation_agent(file_tree: str, file_contents: str, programming_languages: str, analysis_result: str):
    """Main entry point for running recommendations"""
    # Initialize state
    initial_state = {
        "file_tree": file_tree,
        "file_contents": file_contents,
        "programming_languages": programming_languages,
        "analysis_result": analysis_result,
        "recommendations": "",
        "iteration": 0
    }
    
    # Run recommendation workflow
    final_state = graph.invoke(initial_state)
    
    # Collect all recommendations
    recommendations_results = []
    project_info = {
        "Programming Languages": programming_languages,
        "Generation Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Total Iterations": final_state["iteration"]
    }
    
    for i in range(1, final_state["iteration"]):
        recommendations_results.append(final_state["recommendations"])
    
    # Add final recommendations
    recommendations_results.append(final_state["recommendations"])
    
    # Save to PDF
    pdf_path = save_recommendations_to_pdf(recommendations_results, project_info)
    print(f"Recommendations report saved to: {pdf_path}")
    return {"pdf_path": pdf_path, "state": final_state}
