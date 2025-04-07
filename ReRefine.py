# import os
# import json
# import re
# from typing import Dict, Any, List, Optional
# from langchain_groq import ChatGroq
# from dotenv import load_dotenv
# from langchain.schema import SystemMessage, HumanMessage
# from mcp.server.fastmcp import FastMCP
# import sys

# # Load environment variables
# load_dotenv()

# # Initialize MCP server
# mcp = FastMCP("userstory-invest-mcp")

# # Validate environment variables
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# GROQ_MODEL = os.getenv("GROQ_MODEL")

# if not GROQ_API_KEY or not GROQ_MODEL:
#     raise ValueError("GROQ_API_KEY or GROQ_MODEL environment variables not set")


# def sanitize_json_string(json_str):
#     """Sanitize a JSON string by removing or replacing control characters."""
#     json_str = re.sub(r'[\x00-\x09\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', json_str)
    
#     def clean_string_value(match):
#         value = match.group(1)
#         value = value.replace('\n', '\\n').replace('\t', '\\t').replace('\r', '\\r')
#         return f'"{value}"'
    
#     json_str = re.sub(r'"((?:\\.|[^"\\])*)"', clean_string_value, json_str)
#     return json_str


# def preprocess_input(user_input):
#     """Preprocess user input to ensure valid JSON structure."""
#     if isinstance(user_input, dict):
#         return user_input
        
#     try:
#         # If it's already valid JSON, return it
#         return json.loads(user_input)
#     except json.JSONDecodeError:
#         # Attempt to fix common issues
#         cleaned_input = user_input.strip().replace('\n', '').replace('\r', '')
#         # Check if it starts with "UserStory" without proper nesting
#         if '"UserStory":' in cleaned_input and '"Title":' in cleaned_input:
#             # Reconstruct the JSON by wrapping the UserStory content properly
#             try:
#                 # Extract the UserStory part up to AdditionalInformation
#                 story_match = re.search(r'"UserStory":\s*"Title":\s*"([^"]+)",\s*"Description":\s*"([^"]+)",\s*"AcceptanceCriteria":\s*\[(.*?)\],\s*"AdditionalInformation":\s*"([^"]+)"', cleaned_input)
#                 if story_match:
#                     title, desc, ac, add_info = story_match.groups()
#                     ac_list = [item.strip().strip('"') for item in ac.split(',')]
#                     fixed_story = {
#                         "UserStory": {
#                             "Title": title,
#                             "Description": desc,
#                             "AcceptanceCriteria": ac_list,
#                             "AdditionalInformation": add_info
#                         }
#                     }
#                     # Append remaining fields if present
#                     for section in ["Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable", "overall"]:
#                         section_match = re.search(rf'"{section}":\s*{{(.*?)}}', cleaned_input)
#                         if section_match:
#                             section_content = '{' + section_match.group(1) + '}'
#                             fixed_story[section] = json.loads(section_content)
#                     return fixed_story
#             except Exception:
#                 pass
#         # If we can't fix it, raise an error with guidance
#         raise ValueError("Invalid JSON format. Please ensure the input is a properly structured JSON object, e.g., {\"UserStory\": {\"Title\": \"...\", ...}}")


# def create_analysis_prompt(user_story):
#     """Create the prompt messages for user story extraction and INVEST analysis."""
#     if not isinstance(user_story, str):
#         user_story = json.dumps(user_story)
        
#     messages = [
#         SystemMessage(content="""You are an expert agile coach specializing in analyzing user stories using the INVEST criteria. 
# Your task is twofold:
# 1. Analyze the original user story and calculate its INVEST score.
# 2. Create an improved version and provide a detailed refinement summary.

# Follow this structured approach:
# - Extract the original components (Title, Description, AcceptanceCriteria, AdditionalInformation).
# - Score the original story against each INVEST criterion (1-5 scale), considering all provided details accurately.
# - Identify specific weaknesses in the original story.
# - Create an improved version addressing those weaknesses, including all components.
# - Calculate the improved INVEST score.
# - Generate a detailed refinement summary comparing the two versions."""),
#         HumanMessage(content=f"""
#         # User Story: {user_story}

#         ## Task Overview

#         Perform a complete INVEST analysis on the provided user story with these steps:

#         ### Step 1: Analyze the Original User Story
#         - Extract or identify all components (Title, Description, AcceptanceCriteria, AdditionalInformation).
#         - Score each INVEST criterion (1-5 scale) for the ORIGINAL story AS IS, using all provided details (e.g., evaluate existing acceptance criteria accurately).
#         - Calculate the total INVEST score for the original story.
#         - Identify specific weaknesses and areas for improvement.

#         ### Step 2: Create an Improved Version
#         - Generate an improved user story (Title, Description, AcceptanceCriteria, AdditionalInformation) addressing each weakness.
#         - Re-score each INVEST criterion for the IMPROVED version.
#         - Calculate the new total INVEST score.

#         ### Step 3: Generate Analysis Output
#         - Include both original and improved user story components.
#         - For each INVEST criterion, explain the original score and provide specific recommendations.
#         - Ensure explanations reflect the actual content (e.g., don't claim missing acceptance criteria if they're present).

#         ### Step 4: Create a Dynamic Refinement Summary
#         - List specific improvements as bullet points (using '*' on new lines).
#         - Include concrete examples of changes between versions.
#         - End with "INVEST Score improved from X/30 to Y/30".

#         ## Response Format:

#         Return a structured JSON:

#         {{
#           "OriginalUserStory": {{
#             "Title": "string",
#             "Description": "string",
#             "AcceptanceCriteria": ["string", ...],
#             "AdditionalInformation": "string"
#           }},
#           "ImprovedUserStory": {{
#             "Title": "string",
#             "Description": "string",
#             "AcceptanceCriteria": ["string", ...],
#             "AdditionalInformation": "string"
#           }},
#           "Independent": {{
#             "score": number,
#             "explanation": "string",
#             "recommendation": "string"
#           }},
#           "Negotiable": {{
#             "score": number,
#             "explanation": "string",
#             "recommendation": "string"
#           }},
#           "Valuable": {{
#             "score": number,
#             "explanation": "string",
#             "recommendation": "string"
#           }},
#           "Estimable": {{
#             "score": number,
#             "explanation": "string",
#             "recommendation": "string"
#           }},
#           "Small": {{
#             "score": number,
#             "explanation": "string",
#             "recommendation": "string"
#           }},
#           "Testable": {{
#             "score": number,
#             "explanation": "string",
#             "recommendation": "string"
#           }},
#           "overall": {{
#             "score": number,
#             "improved_score": number,
#             "summary": "string",
#             "refinement_summary": "string with '*' bullets on new lines"
#           }}
#         }}

#         IMPORTANT:
#         - Return ONLY structured JSON without markdown or backticks(most important).
#         - Ensure scores are integers (1-5), overall scores sum correctly (max 30).
#         - Use simple '*' bullets on new lines in refinement_summary.
#         - Accurately reflect provided acceptance criteria in scoring.
#         """)
#     ]
#     return messages


# def analyze_user_story(user_story, chat_model=None):
#     """Extract components and perform INVEST analysis."""
#     try:
#         # Initialize the LLM if not provided
#         if not chat_model:
#             chat_model = ChatGroq(model=GROQ_MODEL, api_key=GROQ_API_KEY)
        
#         # Create the analysis prompt and invoke the model
#         analysis_prompt = create_analysis_prompt(user_story)
#         response = chat_model.invoke(analysis_prompt)
#         content = response.content.strip()
        
#         # Process and validate the response
#         json_content = sanitize_json_string(content)
#         result = json.loads(json_content)
        
#         # Validate required fields
#         required_sections = ["OriginalUserStory", "ImprovedUserStory", "Independent", "Negotiable", 
#                             "Valuable", "Estimable", "Small", "Testable", "overall"]
#         for section in required_sections:
#             if section not in result:
#                 if section in ["OriginalUserStory", "ImprovedUserStory"]:
#                     result[section] = {"Title": "", "Description": "", "AcceptanceCriteria": [], "AdditionalInformation": ""}
#                 elif section == "overall":
#                     result[section] = {"score": 0, "improved_score": 0, "summary": "", "refinement_summary": ""}
#                 else:
#                     result[section] = {"score": 0, "explanation": "", "recommendation": ""}
                    
#         # Validate scores
#         for criterion in ["Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable"]:
#             result[criterion]["score"] = max(1, min(5, int(result[criterion]["score"])))
        
#         result["overall"]["score"] = sum(result[c]["score"] for c in ["Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable"])
#         result["overall"]["improved_score"] = min(30, int(result["overall"].get("improved_score", 0)))
        
#         return result
        
#     except Exception as e:
#         return {
#             "error": f"Analysis failed: {str(e)}",
#             "OriginalUserStory": {"Title": "", "Description": "", "AcceptanceCriteria": [], "AdditionalInformation": ""},
#             "ImprovedUserStory": {"Title": "", "Description": "", "AcceptanceCriteria": [], "AdditionalInformation": ""},
#             "Independent": {"score": 0, "explanation": "", "recommendation": ""},
#             "Negotiable": {"score": 0, "explanation": "", "recommendation": ""},
#             "Valuable": {"score": 0, "explanation": "", "recommendation": ""},
#             "Estimable": {"score": 0, "explanation": "", "recommendation": ""},
#             "Small": {"score": 0, "explanation": "", "recommendation": ""},
#             "Testable": {"score": 0, "explanation": "", "recommendation": ""},
#             "overall": {"score": 0, "improved_score": 0, "summary": "Error in analysis", "refinement_summary": ""}
#         }


# def format_invest_results(result: Dict[str, Any]) -> str:
#     """Format the INVEST analysis results into human-readable text."""
#     output = []

#     if "error" in result:
#         return f"Error: {result['error']}"

#     # Original User Story section
#     output.append("# Original User Story")
#     output.append(f"## Title\n{result['OriginalUserStory']['Title']}")
#     output.append(f"## Description\n{result['OriginalUserStory']['Description']}")
    
#     output.append("## Acceptance Criteria")
#     for i, criterion in enumerate(result['OriginalUserStory']['AcceptanceCriteria'], 1):
#         output.append(f"{i}. {criterion}")
    
#     if result['OriginalUserStory']['AdditionalInformation']:
#         output.append(f"## Additional Information\n{result['OriginalUserStory']['AdditionalInformation']}")
    
#     # INVEST Analysis section
#     output.append("\n# INVEST Analysis")
    
#     criteria = ["Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable"]
#     for criterion in criteria:
#         output.append(f"## {criterion} - Score: {result[criterion]['score']}/5")
#         output.append(f"**Explanation**: {result[criterion]['explanation']}")
#         output.append(f"**Recommendation**: {result[criterion]['recommendation']}")
    
#     # Overall Analysis
#     output.append(f"\n# Overall Analysis")
#     output.append(f"**Original Score**: {result['overall']['score']}/30")
#     output.append(f"**Improved Score**: {result['overall']['improved_score']}/30")
#     output.append(f"**Summary**: {result['overall']['summary']}")
    
#     # Improved User Story section
#     output.append("\n# Improved User Story")
#     output.append(f"## Title\n{result['ImprovedUserStory']['Title']}")
#     output.append(f"## Description\n{result['ImprovedUserStory']['Description']}")
    
#     output.append("## Acceptance Criteria")
#     for i, criterion in enumerate(result['ImprovedUserStory']['AcceptanceCriteria'], 1):
#         output.append(f"{i}. {criterion}")
    
#     if result['ImprovedUserStory']['AdditionalInformation']:
#         output.append(f"## Additional Information\n{result['ImprovedUserStory']['AdditionalInformation']}")
    
#     # Refinement Summary
#     output.append("\n# Refinement Summary")
#     refinement_points = result['overall']['refinement_summary'].split('*')
#     for point in refinement_points:
#         if point.strip():
#             output.append(f"* {point.strip()}")
    
#     return "\n".join(output)


# @mcp.tool(description="Analyzes user stories using the INVEST criteria and suggests improvements.")
# async def invest_analyze(
#     user_story: Dict[str, Any],
#     format_output: Optional[bool] = True
# ) -> Dict[str, Any]:
#     """
#     Analyze a user story using INVEST criteria and provide improvement recommendations.
    
#     Parameters:
#     user_story (Dict): A user story object containing at minimum Title, Description, and AcceptanceCriteria
#     format_output (bool): Whether to return the results as formatted text (True) or raw JSON (False)
    
#     Returns:
#     Dict: Analysis results with INVEST scores and improvement suggestions
#     """
#     try:
#         # Preprocess the input to handle various formats
#         processed_story = preprocess_input(user_story)
        
#         # Perform the INVEST analysis
#         analysis_result = analyze_user_story(processed_story)
        
#         if format_output:
#             # Return a formatted text version for human readability
#             formatted_results = format_invest_results(analysis_result)
#             return {"content": [{"type": "text", "text": formatted_results}]}
#         else:
#             # Return the raw analysis results as JSON
#             return {"content": [{"type": "json", "json": analysis_result}]}
            
#     except Exception as e:
#         return {"content": [{"type": "text", "text": f"Error analyzing user story: {str(e)}"}], "isError": True}


# # if __name__ == "__main__":
# #     print("UserStory INVEST Analyzer MCP server running on stdio...")
# #     mcp.run()

# # if __name__ == "__main__":
# #     print("UserStory INVEST Analyzer MCP server running on stdio...")
# #     input_data = sys.stdin.read()  # Read raw input for debugging
# #     print(f"Debug: Received input: {input_data}")
# #     mcp.run()  # This might override stdin, so test separately
# #     print("Server finished running")

# if __name__ == "__main__":
#     print("UserStory INVEST Analyzer MCP server running on stdio...")
#     print("Debug: Waiting for input...")
    
#     # Read input from stdin
#     input_data = sys.stdin.readline().strip()
    
#     if not input_data:
#         print("Debug: No input received")
#         sys.exit(1)
    
#     print(f"Debug: Received input: {input_data}")
    
#     try:
#         # Parse the JSON request
#         request = json.loads(input_data)
#         tool = request.get("tool")
#         params = request.get("parameters", {})
        
#         if tool != "invest_analyze":
#             print(f"Error: Unknown tool '{tool}'")
#             sys.exit(1)
        
#         print("Debug: Processing request...")
        
#         # Call the invest_analyze function directly
#         result = invest_analyze(
#             user_story=params.get("user_story", {}),
#             format_output=params.get("format_output", True)
#         )
        
#         # Output the result as JSON
#         print("Debug: Sending response...")
#         print(json.dumps(result))
        
#     except json.JSONDecodeError:
#         print("Error: Invalid JSON input")
#     except Exception as e:
#         print(f"Error: {str(e)}")



















import os
import json
import re
from typing import Dict, Any, List, Optional
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain.schema import SystemMessage, HumanMessage
from mcp.server.fastmcp import FastMCP
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("MCP-Server")

# Load environment variables
load_dotenv()

# Initialize MCP server
mcp = FastMCP("userstory-invest-mcp")

# Validate environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL")

if not GROQ_API_KEY or not GROQ_MODEL:
    raise ValueError("GROQ_API_KEY or GROQ_MODEL environment variables not set")

def sanitize_json_string(json_str):
    """Sanitize a JSON string by removing or replacing control characters."""
    json_str = re.sub(r'[\x00-\x09\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', json_str)
    
    def clean_string_value(match):
        value = match.group(1)
        value = value.replace('\n', '\\n').replace('\t', '\\t').replace('\r', '\\r')
        return f'"{value}"'
    
    json_str = re.sub(r'"((?:\\.|[^"\\])*)"', clean_string_value, json_str)
    return json_str

def preprocess_input(user_input):
    """Preprocess user input to ensure valid JSON structure."""
    if isinstance(user_input, dict):
        return user_input
        
    try:
        return json.loads(user_input)
    except json.JSONDecodeError:
        cleaned_input = user_input.strip().replace('\n', '').replace('\r', '')
        if '"UserStory":' in cleaned_input and '"Title":' in cleaned_input:
            try:
                story_match = re.search(r'"UserStory":\s*"Title":\s*"([^"]+)",\s*"Description":\s*"([^"]+)",\s*"AcceptanceCriteria":\s*\[(.*?)\],\-reli,"AdditionalInformation":\s*"([^"]+)"', cleaned_input)
                if story_match:
                    title, desc, ac, add_info = story_match.groups()
                    ac_list = [item.strip().strip('"') for item in ac.split(',')]
                    fixed_story = {
                        "UserStory": {
                            "Title": title,
                            "Description": desc,
                            "AcceptanceCriteria": ac_list,
                            "AdditionalInformation": add_info
                        }
                    }
                    for section in ["Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable", "overall"]:
                        section_match = re.search(rf'"{section}":\s*{{(.*?)}}', cleaned_input)
                        if section_match:
                            section_content = '{' + section_match.group(1) + '}'
                            fixed_story[section] = json.loads(section_content)
                    return fixed_story
            except Exception:
                pass
        raise ValueError("Invalid JSON format. Please ensure the input is a properly structured JSON object.")

def create_analysis_prompt(user_story):
    """Create the prompt messages for user story extraction and INVEST analysis."""
    if not isinstance(user_story, str):
        user_story = json.dumps(user_story)
        
    messages = [
        SystemMessage(content="""You are an expert agile coach specializing in analyzing user stories using the INVEST criteria. 
Your task is twofold:
1. Analyze the original user story and calculate its INVEST score.
2. Create an improved version and provide a detailed refinement summary.

Follow this structured approach:
- Extract the original components (Title, Description, AcceptanceCriteria, AdditionalInformation).
- Score the original story against each INVEST criterion (1-5 scale), considering all provided details accurately.
- Identify specific weaknesses in the original story.
- Create an improved version addressing those weaknesses, including all components.
- Calculate the improved INVEST score.
- Generate a detailed refinement summary comparing the two versions."""),
        HumanMessage(content=f"""
        # User Story: {user_story}

        ## Task Overview

        Perform a complete INVEST analysis on the provided user story with these steps:

        ### Step 1: Analyze the Original User Story
        - Extract or identify all components (Title, Description, AcceptanceCriteria, AdditionalInformation).
        - Score each INVEST criterion (1-5 scale) for the ORIGINAL story AS IS, using all provided details.
        - Calculate the total INVEST score for the original story.
        - Identify specific weaknesses and areas for improvement.

        ### Step 2: Create an Improved Version
        - Generate an improved user story (Title, Description, AcceptanceCriteria, AdditionalInformation) addressing each weakness.
        - Re-score each INVEST criterion for the IMPROVED version.
        - Calculate the new total INVEST score.

        ### Step 3: Generate Analysis Output
        - Include both original and improved user story components.
        - For each INVEST criterion, explain the original score and provide specific recommendations.
        - Ensure explanations reflect the actual content.

        ### Step 4: Create a Dynamic Refinement Summary
        - List specific improvements as bullet points (using '*' on new lines).
        - Include concrete examples of changes between versions.
        - End with "INVEST Score improved from X/30 to Y/30".

        ## Response Format:

        Return a structured JSON:

        {{
          "OriginalUserStory": {{
            "Title": "string",
            "Description": "string",
            "AcceptanceCriteria": ["string", ...],
            "AdditionalInformation": "string"
          }},
          "ImprovedUserStory": {{
            "Title": "string",
            "Description": "string",
            "AcceptanceCriteria": ["string", ...],
            "AdditionalInformation": "string"
          }},
          "Independent": {{
            "score": number,
            "explanation": "string",
            "recommendation": "string"
          }},
          "Negotiable": {{
            "score": number,
            "explanation": "string",
            "recommendation": "string"
          }},
          "Valuable": {{
            "score": number,
            "explanation": "string",
            "recommendation": "string"
          }},
          "Estimable": {{
            "score": number,
            "explanation": "string",
            "recommendation": "string"
          }},
          "Small": {{
            "score": number,
            "explanation": "string",
            "recommendation": "string"
          }},
          "Testable": {{
            "score": number,
            "explanation": "string",
            "recommendation": "string"
          }},
          "overall": {{
            "score": number,
            "improved_score": number,
            "summary": "string",
            "refinement_summary": "string with '*' bullets on new lines"
          }}
        }}

        IMPORTANT:
        - Return ONLY structured JSON without markdown or backticks.
        - Ensure scores are integers (1-5), overall scores sum correctly (max 30).
        - Use simple '*' bullets on new lines in refinement_summary.
        """)
    ]
    return messages

def analyze_user_story(user_story, chat_model=None):
    """Extract components and perform INVEST analysis."""
    try:
        if not chat_model:
            chat_model = ChatGroq(model=GROQ_MODEL, api_key=GROQ_API_KEY)
        
        analysis_prompt = create_analysis_prompt(user_story)
        response = chat_model.invoke(analysis_prompt)
        content = response.content.strip()
        
        json_content = sanitize_json_string(content)
        result = json.loads(json_content)
        
        required_sections = ["OriginalUserStory", "ImprovedUserStory", "Independent", "Negotiable", 
                            "Valuable", "Estimable", "Small", "Testable", "overall"]
        for section in required_sections:
            if section not in result:
                if section in ["OriginalUserStory", "ImprovedUserStory"]:
                    result[section] = {"Title": "", "Description": "", "AcceptanceCriteria": [], "AdditionalInformation": ""}
                elif section == "overall":
                    result[section] = {"score": 0, "improved_score": 0, "summary": "", "refinement_summary": ""}
                else:
                    result[section] = {"score": 0, "explanation": "", "recommendation": ""}
                    
        for criterion in ["Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable"]:
            result[criterion]["score"] = max(1, min(5, int(result[criterion]["score"])))
        
        result["overall"]["score"] = sum(result[c]["score"] for c in ["Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable"])
        result["overall"]["improved_score"] = min(30, int(result["overall"].get("improved_score", 0)))
        
        return result
        
    except Exception as e:
        return {
            "error": f"Analysis failed: {str(e)}",
            "OriginalUserStory": {"Title": "", "Description": "", "AcceptanceCriteria": [], "AdditionalInformation": ""},
            "ImprovedUserStory": {"Title": "", "Description": "", "AcceptanceCriteria": [], "AdditionalInformation": ""},
            "Independent": {"score": 0, "explanation": "", "recommendation": ""},
            "Negotiable": {"score": 0, "explanation": "", "recommendation": ""},
            "Valuable": {"score": 0, "explanation": "", "recommendation": ""},
            "Estimable": {"score": 0, "explanation": "", "recommendation": ""},
            "Small": {"score": 0, "explanation": "", "recommendation": ""},
            "Testable": {"score": 0, "explanation": "", "recommendation": ""},
            "overall": {"score": 0, "improved_score": 0, "summary": "Error in analysis", "refinement_summary": ""}
        }

def format_invest_results(result: Dict[str, Any]) -> str:
    """Format the INVEST analysis results into human-readable text."""
    output = []

    if "error" in result:
        return f"Error: {result['error']}"

    output.append("# Original User Story")
    output.append(f"## Title\n{result['OriginalUserStory']['Title']}")
    output.append(f"## Description\n{result['OriginalUserStory']['Description']}")
    
    output.append("## Acceptance Criteria")
    for i, criterion in enumerate(result['OriginalUserStory']['AcceptanceCriteria'], 1):
        output.append(f"{i}. {criterion}")
    
    if result['OriginalUserStory']['AdditionalInformation']:
        output.append(f"## Additional Information\n{result['OriginalUserStory']['AdditionalInformation']}")
    
    output.append("\n# INVEST Analysis")
    
    criteria = ["Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable"]
    for criterion in criteria:
        output.append(f"## {criterion} - Score: {result[criterion]['score']}/5")
        output.append(f"**Explanation**: {result[criterion]['explanation']}")
        output.append(f"**Recommendation**: {result[criterion]['recommendation']}")
    
    output.append(f"\n# Overall Analysis")
    output.append(f"**Original Score**: {result['overall']['score']}/30")
    output.append(f"**Improved Score**: {result['overall']['improved_score']}/30")
    output.append(f"**Summary**: {result['overall']['summary']}")
    
    output.append("\n# Improved User Story")
    output.append(f"## Title\n{result['ImprovedUserStory']['Title']}")
    output.append(f"## Description\n{result['ImprovedUserStory']['Description']}")
    
    output.append("## Acceptance Criteria")
    for i, criterion in enumerate(result['ImprovedUserStory']['AcceptanceCriteria'], 1):
        output.append(f"{i}. {criterion}")
    
    if result['ImprovedUserStory']['AdditionalInformation']:
        output.append(f"## Additional Information\n{result['ImprovedUserStory']['AdditionalInformation']}")
    
    output.append("\n# Refinement Summary")
    refinement_points = result['overall']['refinement_summary'].split('*')
    for point in refinement_points:
        if point.strip():
            output.append(f"* {point.strip()}")
    
    return "\n".join(output)

# @mcp.tool(description="Analyzes user stories using the INVEST criteria and suggests improvements.")
# async def invest_analyze(
#     user_story: Dict[str, Any],
#     format_output: Optional[bool] = True
# ) -> Dict[str, Any]:
#     """
#     Analyze a user story using INVEST criteria and provide improvement recommendations.
    
#     Parameters:
#     user_story (Dict): A user story object containing at minimum Title, Description, and AcceptanceCriteria
#     format_output (bool): Whether to return the results as formatted text (True) or raw JSON (False)
    
#     Returns:
#     Dict: Analysis results with INVEST scores and improvement suggestions
#     """
#     try:
#         processed_story = preprocess_input(user_story)
#         analysis_result = analyze_user_story(processed_story)
        
#         if format_output:
#             formatted_results = format_invest_results(analysis_result)
#             return {"content": [{"type": "text", "text": formatted_results}]}
#         else:
#             return {"content": [{"type": "json", "json": analysis_result}]}
            
#     except Exception as e:
#         return {"content": [{"type": "text", "text": f"Error analyzing user story: {str(e)}"}], "isError": True}

@mcp.tool(description="Analyzes user stories using the INVEST criteria and suggests improvements.")
async def invest_analyze(
    user_story: Dict[str, Any],
    format_output: Optional[bool] = True
) -> Dict[str, Any]:
    try:
        processed_story = preprocess_input(user_story)
        analysis_result = analyze_user_story(processed_story)
        
        if format_output:
            formatted_results = format_invest_results(analysis_result)
            return {"content": [{"type": "text", "text": formatted_results}]}
        else:
            # Return core JSON directly without wrappers
            return analysis_result
            
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error analyzing user story: {str(e)}"}], "isError": True}

if __name__ == "__main__":
    print("UserStory INVEST Analyzer MCP server running on stdio...")
    mcp.run(transport='stdio')@mcp.tool(description="Analyzes user stories using the INVEST criteria and suggests improvements.")
async def invest_analyze(
    user_story: Dict[str, Any],
    format_output: Optional[bool] = True
) -> Dict[str, Any]:
    logger.debug("Entering invest_analyze")
    try:
        logger.debug(f"Preprocessing user story: {user_story}")
        processed_story = preprocess_input(user_story)
        
        logger.debug("Performing analysis")
        analysis_result = analyze_user_story(processed_story)
        
        logger.debug(f"Analysis result: {analysis_result}")
        if format_output:
            logger.debug("Formatting results")
            formatted_results = format_invest_results(analysis_result)
            return {"content": [{"type": "text", "text": formatted_results}]}
        else:
            return {"content": [{"type": "json", "json": analysis_result}]}
            
    except Exception as e:
        logger.error(f"Error in invest_analyze: {str(e)}")
        return {"content": [{"type": "text", "text": f"Error analyzing user story: {str(e)}"}], "isError": True}

if __name__ == "__main__":
    logger.info("UserStory INVEST Analyzer MCP server running on stdio...")
    logger.debug("Starting MCP server...")
    mcp.run(transport='stdio')
    logger.debug("MCP server finished (should not reach here unless stopped)")