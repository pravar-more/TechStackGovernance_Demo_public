import os
from typing import Annotated, TypedDict
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langgraph.graph import StateGraph, END
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Define configuration variables for the Azure OpenAI API
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
key = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_GPT4_DEPLOYMENT_NAME = os.getenv("AZURE_GPT4_DEPLOYMENT_NAME")

# Initialize an instance of AzureChatOpenAI
llm = AzureChatOpenAI(
    temperature=0.1,
    model=AZURE_GPT4_DEPLOYMENT_NAME,
    azure_endpoint=endpoint,
    openai_api_key=key,
    api_version=AZURE_OPENAI_API_VERSION
)

class AnalysisState(TypedDict):
    """TypedDict for maintaining analysis state"""
    file_tree: str
    file_contents: str
    programming_language: str
    analysis_result: str
    iteration: int
    human_input: str

# PROMPT_TEMPLATE 
PROMPT_TEMPLATE = """
You are Code Analyzer Agent (CAA), an expert AI code analyst. Your task is to analyze the provided code and project structure for potential issues and provide comprehensive insights.
IMPORTANT::: Genrate the report in less than 100 words.

**Input:**
*   **Code:**
    ```
    {code}
    ```
*   **File Tree:**
    ```
    {file_tree}
    ```
*   **Programming Language:** {language}
*   **Analysis Focus:** {analysis_focus}
*   **Style Guide:** {style_guide}
*   **Specific Instructions:** {specific_instructions}

**Analysis Categories:**
1. Code Quality:
   - Readability (variable names, code structure)
   - Maintainability 
   - Coding standards compliance
   - Documentation completeness

2. Security Issues:
   - Injection vulnerabilities
   - Hardcoded credentials/secrets
   - Authentication/authorization
   - Data protection measures

3. Dependencies:
   - Vulnerabilities
   - Package versions
   - Known vulnerabilities 
   - License compliance
   - Compatibility status

4. Performance:
   - Logic efficiency
   - Resource management
   - Database operations
   - Caching implementation

5. Best Practices:
   - Vulnerabilities   
   - Exception handling
   - Logging implementation  
   - Unit test coverage
   - Design patterns usage

**Guardrails:**
* **Security:**
   * DO NOT expose PII, secrets, API keys, or confidential data
   * DO NOT execute provided code
   * Avoid suggesting risky operations
* **Factuality:**
   * Back recommendations with evidence (cite line numbers)
   * State uncertainties clearly
   * Stay within analysis scope
* **Ethics:**
   * Use neutral language
   * Avoid bias in assessments

**Output Format (Markdown):**
## Code Analysis Report

### Project Overview
[Brief description of structure and tech stack]

### High Severity Issues
* **Issue:** [Description]
* **Category:** [Security/Performance/etc]
* **Location:** [File:line]
* **Impact:** [Consequences]
* **Recommendation:** [Solution]

### Medium Severity Issues
[Follow same format as above]

### Low Severity Issues  
[Follow same format as above]

### Best Practices Review
* Testing: [Coverage analysis]
* Logging: [Implementation review]
* Error Handling: [Strategy assessment]

### Recommendations
[Prioritized list of actionable improvements]

### Conclusion
[Key findings summary]
"""

def save_analysis_to_pdf(analysis_results, project_info, output_path="analysis_reports"):
    """Saves analysis results to a PDF file with colored dependencies and bold titles"""
    os.makedirs(output_path, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(output_path, f"code_analysis_{timestamp}.pdf")
    
    # Create PDF document
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=18,
        spaceAfter=30
    )
    
    header_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        spaceAfter=12
    )
    
    content_style = ParagraphStyle(
        'CustomContent',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        spaceAfter=10
    )
    
    dependency_style = ParagraphStyle(
        'DependencyStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.red,
        spaceAfter=10
    )
    
    # Add title
    story.append(Paragraph("Code Analysis Report", title_style))
    story.append(Spacer(1, 20))
    
    
    # Add dependency table section
    dependency_table_style = ParagraphStyle(
        'DependencyTableHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        spaceAfter=12
    )
    
    story.append(Paragraph("Dependency Analysis", dependency_table_style))
    story.append(Spacer(1, 12))

    # Create dependency data
    dependency_data = [
        ["Dependency Name", "Current Version", "Recommended Version"],
        ["Spring Boot", "2.7.5", "3.1.0"],
        ["Spring Security", "5.7.2", "6.1.1"], 
        ["Hibernate", "6.1.1", "6.2.0"],
        ["PostgreSQL Driver", "42.3.6", "42.5.0"]
    ]

    # Create and style the table
    table = Table(dependency_data, colWidths=[250, 150, 150])
    table.setStyle(TableStyle([
        # Header row styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Data rows styling
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    story.append(table)
    story.append(Spacer(1, 20))   
    
    # Add project information with bold headers
    for key, value in project_info.items():
        story.append(Paragraph(f"<b>{key}:</b> {value}", content_style))
    
    story.append(Spacer(1, 20))
    
    # Process analysis results
    for i, result in enumerate(analysis_results, 1):
        # Add section header
        story.append(Paragraph(f"Analysis Iteration {i}", header_style))
        story.append(Spacer(1, 12))
        
        # Split content and process each section
        sections = result.split('\n\n')
        for section in sections:
            if section.strip():
                # Check if this is a dependency section
                if "dependency" in section.lower() or "package" in section.lower() or "vulnerabilities" in section.lower():
                    story.append(Paragraph(section, dependency_style))
                # Check if this is a header section
                elif section.startswith('#') or section.startswith('###'):
                    cleaned_header = section.strip('#').strip()
                    story.append(Paragraph(f"<b>{cleaned_header}</b>", header_style))
                else:
                    story.append(Paragraph(section, content_style))
                story.append(Spacer(1, 10))
    
    # Build PDF
    doc.build(story)
    return filename


def analyze_code(state: AnalysisState):
    """Analyzes code based on provided state"""
    analysis_prompt = PROMPT_TEMPLATE.format(
        code=state['file_contents'],
        file_tree=state['file_tree'],
        language=state['programming_language'],
        analysis_focus="security, performance, code quality",
        style_guide="PEP 8" if state['programming_language'] == "Python" else "",
        specific_instructions=state.get('human_input', "Focus on security best practices and code quality")
    )
    response = llm.invoke([{"role": "system", "content": analysis_prompt}])
    return {"analysis_result": response.content, "iteration": state["iteration"] + 1}

def reflect_on_analysis(state: AnalysisState):
    """Reflects on previous analysis results"""
    reflection_prompt = PROMPT_TEMPLATE.format(
        code=state['file_contents'],
        file_tree=state['file_tree'],
        language=state['programming_language'],
        analysis_focus="security vulnerabilities, performance bottlenecks, code style, maintainability",
        style_guide="PEP 8" if state['programming_language'] == "Python" else "",
        specific_instructions=state.get('human_input', "Focus on potential vulnerabilities and error handling")
    )
    response = llm.invoke([{"role": "system", "content": reflection_prompt}])
    return {"analysis_result": response.content, "iteration": state["iteration"] + 1}

def should_continue(state: AnalysisState):
    """Determines if analysis iteration should continue"""
    if state["iteration"] >= 1:
        return END
    return "reflect_on_analysis"

def run_code_analysis_agent(file_tree: str, file_contents: str, programming_language: str, human_input: str = ""):
    """Main entry point for running code analysis"""
    initial_state = {
        "file_tree": file_tree,
        "file_contents": file_contents,
        "programming_language": programming_language,
        "analysis_result": "",
        "iteration": 0,
        "human_input": human_input
    }

    # Initialize and configure the state graph
    graph_builder = StateGraph(AnalysisState)
    graph_builder.add_node("analyze_code", analyze_code)
    graph_builder.add_node("reflect_on_analysis", reflect_on_analysis)
    graph_builder.set_entry_point("analyze_code")
    
    # Add graph edges
    graph_builder.add_conditional_edges(
        "reflect_on_analysis",
        should_continue,
        {END: END, "reflect_on_analysis": "reflect_on_analysis"}
    )
    graph_builder.add_edge("analyze_code", "reflect_on_analysis")
    
    # Compile and run the graph
    graph = graph_builder.compile()
    final_state = graph.invoke(initial_state)
    
    # Collect all analysis results
    analysis_results = []
    project_info = {
        "Programming Language": programming_language,
        "Analysis Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Total Iterations": final_state["iteration"]
    }
    
    for i in range(1, final_state["iteration"]):
        analysis_results.append(final_state["analysis_result"])
    
    # Add final analysis
    analysis_results.append(final_state["analysis_result"])
    
    # Save results to PDF
    pdf_path = save_analysis_to_pdf(analysis_results, project_info)
    print(f"Analysis report saved to: {pdf_path}")
    
    return final_state

if __name__ == "__main__":
    # Test code analysis
    test_file_tree = "example/tree/structure"
    test_file_contents = "def example(): pass"
    test_language = "Python"
    result = run_code_analysis_agent(test_file_tree, test_file_contents, test_language)