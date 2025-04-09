# import os
# import json
# import re
# from typing import Dict, Any, List, Optional
# from langchain_groq import ChatGroq
# from dotenv import load_dotenv
# from langchain.schema import SystemMessage, HumanMessage
# from mcp.server.fastmcp import FastMCP
# import logging

# # Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

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

# def preprocess_input(user_input: str | Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Dict[str, Any]], str, str, int]:
#     """Preprocess user input to extract UserStory, INVEST criteria, and refinement guidance."""
#     try:
#         if isinstance(user_input, str):
#             data = json.loads(user_input)
#         else:
#             data = user_input

#         logger.info(f"Preprocessed input: {data}")

#         if "UserStory" not in data:
#             raise ValueError("Input must contain a 'UserStory' object with Title, Description, AcceptanceCriteria, and AdditionalInformation.")
        
#         user_story = data["UserStory"]
#         required_fields = ["Title", "Description", "AcceptanceCriteria", "AdditionalInformation"]
#         for field in required_fields:
#             if field not in user_story:
#                 raise ValueError(f"UserStory must contain the field: {field}")

#         # Extract INVEST criteria
#         invest_criteria = {}
#         required_criteria = ["Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable"]
#         for criterion in required_criteria:
#             if criterion not in data:
#                 raise ValueError(f"Input must contain '{criterion}' with score, explanation, and recommendation.")
#             invest_criteria[criterion] = {
#                 "score": data[criterion].get("score", 0),
#                 "explanation": data[criterion].get("explanation", ""),
#                 "recommendation": data[criterion].get("recommendation", "")
#             }
#             if not isinstance(invest_criteria[criterion]["score"], (int,

# float)):
#                 invest_criteria[criterion]["score"] = 0
#             invest_criteria[criterion]["score"] = max(1, min(5, int(invest_criteria[criterion]["score"])))

#         aspects_to_enhance = data.get("aspects_to_enhance", "No specific aspects provided.")
#         if not isinstance(aspects_to_enhance, str):
#             raise ValueError("'aspects_to_enhance' must be a string.")

#         additional_context = data.get("additional_context", "No additional context provided.")
#         if not isinstance(additional_context, str):
#             raise ValueError("'additional_context' must be a string.")

#         input_score = data.get("overall", {}).get("score", 0)
#         if not isinstance(input_score, (int, float)):
#             input_score = 0
#         input_score = max(0, min(30, int(input_score)))

#         return user_story, invest_criteria, aspects_to_enhance, additional_context, input_score

#     except json.JSONDecodeError:
#         raise ValueError("Invalid JSON format. Please ensure the input is a properly structured JSON object.")
#     except Exception as e:
#         raise ValueError(f"Error processing input: {str(e)}")

# def create_analysis_prompt(user_story: Dict[str, Any], invest_criteria: Dict[str, Dict[str, Any]], aspects_to_enhance: str, additional_context: str, input_score: int) -> List[SystemMessage | HumanMessage]:
#     """Create the prompt messages for user story refinement using provided INVEST criteria."""
#     user_story_str = json.dumps(user_story)
#     invest_criteria_str = json.dumps(invest_criteria)
#     messages = [
#         SystemMessage(content="""You are an expert agile coach specializing in refining user stories using the INVEST criteria. 
# Your task is to:
# 1. Use the provided user story and its existing INVEST scores as the original baseline.
# 2. Create an improved version based on the refinement guidance and provided recommendations.

# Follow this structured approach:
# - Use the provided original components (Title, Description, AcceptanceCriteria, AdditionalInformation) and INVEST scores as the starting point.
# - Identify weaknesses based on the provided scores, explanations, and recommendations.
# - Create an improved version addressing those weaknesses, incorporating the aspects to enhance and additional context.
# - If the aspects to enhance or additional context indicate "No specific aspects provided." or "No additional context provided.", focus on improving areas with lower scores based on the provided recommendations.
# - Re-score each INVEST criterion for the improved user story (1-5 scale).
# - Calculate the improved INVEST score by summing the improved scores.
# - Generate a detailed refinement summary comparing the two versions."""),
#         HumanMessage(content=f"""
#         # Original User Story: {user_story_str}

#         # Original INVEST Criteria: {invest_criteria_str}

#         ## Refinement Guidance

#         ### Aspects of the user story to enhance:
#         {aspects_to_enhance}

#         ### Additional information or context to consider:
#         {additional_context}

#         ## Task Overview

#         Refine the provided user story with these steps:

#         ### Step 1: Use the Original User Story and Scores
#         - Use the provided components (Title, Description, AcceptanceCriteria, AdditionalInformation).
#         - Use the provided INVEST scores and explanations as the baseline for the original story.
#         - The user has provided an input score of {input_score}/30 for the original story as the overall baseline.

#         ### Step 2: Create an Improved Version
#         - Generate an improved user story (Title, Description, AcceptanceCriteria, AdditionalInformation) addressing weaknesses identified in the provided INVEST criteria.
#         - Incorporate the aspects to enhance and additional context to guide the refinement.
#         - Re-score each INVEST criterion for the IMPROVED version (1-5 scale).
#         - Calculate the new total INVEST score for the improved version by summing the improved scores.

#         ### Step 3: Generate Analysis Output
#         - Include both original and improved user story components.
#         - For each INVEST criterion, use the provided original score, provide the improved score, use the provided explanation, and update the recommendation based on the improvements made.
#         - Ensure recommendations reflect the changes made in the improved version.

#         ### Step 4: Create a Dynamic Refinement Summary
#         - List specific improvements as bullet points (using '*' on new lines).
#         - Include concrete examples of changes between versions.
#         - End with "INVEST Score improved from {input_score}/30 to Y/30", where Y is the total improved score.

#         ## Response Format:

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
#             "improved_score": number,
#             "explanation": "string",
#             "recommendation": "string"
#           }},
#           "Negotiable": {{
#             "score": number,
#             "improved_score": number,
#             "explanation": "string",
#             "recommendation": "string"
#           }},
#           "Valuable": {{
#             "score": number,
#             "improved_score": number,
#             "explanation": "string",
#             "recommendation": "string"
#           }},
#           "Estimable": {{
#             "score": number,
#             "improved_score": number,
#             "explanation": "string",
#             "recommendation": "string"
#           }},
#           "Small": {{
#             "score": number,
#             "improved_score": number,
#             "explanation": "string",
#             "recommendation": "string"
#           }},
#           "Testable": {{
#             "score": number,
#             "improved_score": number,
#             "explanation": "string",
#             "recommendation": "string"
#           }},
#           "overall": {{
#             "input_score": number,
#             "improved_score": number,
#             "summary": "string",
#             "refinement_summary": "string with '*' bullets on new lines"
#           }}
#         }}

#         IMPORTANT:
#         - Return ONLY raw JSON without markdown or backticks.
#         - Ensure scores are integers (1-5), overall scores sum correctly (max 30).
#         - Use the provided input_score ({input_score}/30) as the overall.input_score in the response.
#         - Use simple '*' bullets on new lines in refinement_summary.
#         - Use the provided INVEST scores and explanations as the original baseline.
#         """)
#     ]
#     return messages

# def analyze_user_story(user_story: Dict[str, Any], invest_criteria: Dict[str, Dict[str, Any]], aspects_to_enhance: str = "", additional_context: str = "", input_score: int = 0, chat_model=None) -> Dict[str, Any]:
#     """Refine the user story using provided INVEST criteria and generate an improved version."""
#     try:
#         if not chat_model:
#             chat_model = ChatGroq(model=GROQ_MODEL, api_key=GROQ_API_KEY)
        
#         analysis_prompt = create_analysis_prompt(user_story, invest_criteria, aspects_to_enhance, additional_context, input_score)
#         response = chat_model.invoke(analysis_prompt)
#         content = response.content.strip()
        
#         json_content = sanitize_json_string(content)
#         result = json.loads(json_content)
        
#         # Validate required fields and populate with provided data
#         required_sections = ["OriginalUserStory", "ImprovedUserStory", "Independent", "Negotiable", 
#                             "Valuable", "Estimable", "Small", "Testable", "overall"]
#         for section in required_sections:
#             if section not in result:
#                 if section == "OriginalUserStory":
#                     result[section] = user_story
#                 elif section == "ImprovedUserStory":
#                     result[section] = {"Title": "", "Description": "", "AcceptanceCriteria": [], "AdditionalInformation": ""}
#                 elif section == "overall":
#                     result[section] = {"input_score": input_score, "improved_score": 0, "summary": "", "refinement_summary": ""}
#                 else:
#                     result[section] = invest_criteria.get(section, {"score": 0, "improved_score": 0, "explanation": "", "recommendation": ""})
#             elif section in invest_criteria:
#                 result[section]["score"] = invest_criteria[section]["score"]
#                 result[section]["explanation"] = invest_criteria[section]["explanation"]
        
#         # Validate scores
#         criteria = ["Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable"]
#         for criterion in criteria:
#             result[criterion]["score"] = max(1, min(5, int(result[criterion].get("score", 0))))
#             result[criterion]["improved_score"] = max(1, min(5, int(result[criterion].get("improved_score", 0))))
        
#         # Calculate and validate overall scores
#         calculated_improved_score = sum(result[c]["improved_score"] for c in criteria)
#         result["overall"]["input_score"] = max(0, min(30, int(input_score)))
#         result["overall"]["improved_score"] = min(30, calculated_improved_score)
        
#         # Update refinement_summary with correct scores
#         if "refinement_summary" in result["overall"]:
#             result["overall"]["refinement_summary"] = re.sub(
#                 r"INVEST Score improved from \d+/30 to \d+/30",
#                 f"INVEST Score improved from {input_score}/30 to {calculated_improved_score}/30",
#                 result["overall"]["refinement_summary"]
#             )
        
#         return result
        
#     except Exception as e:
#         return {
#             "error": f"Analysis failed: {str(e)}",
#             "OriginalUserStory": user_story,
#             "ImprovedUserStory": {"Title": "", "Description": "", "AcceptanceCriteria": [], "AdditionalInformation": ""},
#             "Independent": invest_criteria.get("Independent", {"score": 0, "improved_score": 0, "explanation": "", "recommendation": ""}),
#             "Negotiable": invest_criteria.get("Negotiable", {"score": 0, "improved_score": 0, "explanation": "", "recommendation": ""}),
#             "Valuable": invest_criteria.get("Valuable", {"score": 0, "improved_score": 0, "explanation": "", "recommendation": ""}),
#             "Estimable": invest_criteria.get("Estimable", {"score": 0, "improved_score": 0, "explanation": "", "recommendation": ""}),
#             "Small": invest_criteria.get("Small", {"score": 0, "improved_score": 0, "explanation": "", "recommendation": ""}),
#             "Testable": invest_criteria.get("Testable", {"score": 0, "improved_score": 0, "explanation": "", "recommendation": ""}),
#             "overall": {"input_score": input_score, "improved_score": 0, "summary": "Error in analysis", "refinement_summary": ""}
#         }

# def format_invest_results(result: Dict[str, Any]) -> str:
#     """Format the INVEST analysis results into human-readable text."""
#     output = []

#     if "error" in result:
#         return f"Error: {result['error']}"

#     output.append("# Original User Story")
#     output.append(f"## Title\n{result['OriginalUserStory']['Title']}")
#     output.append(f"## Description\n{result['OriginalUserStory']['Description']}")
    
#     output.append("## Acceptance Criteria")
#     for i, criterion in enumerate(result['OriginalUserStory']['AcceptanceCriteria'], 1):
#         output.append(f"{i}. {criterion}")
    
#     if result['OriginalUserStory']['AdditionalInformation']:
#         output.append(f"## Additional Information\n{result['OriginalUserStory']['AdditionalInformation']}")
    
#     output.append("\n# INVEST Analysis")
    
#     criteria = ["Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable"]
#     for criterion in criteria:
#         output.append(f"## {criterion} - Original Score: {result[criterion]['score']}/5, Improved Score: {result[criterion]['improved_score']}/5")
#         output.append(f"**Explanation**: {result[criterion]['explanation']}")
#         output.append(f"**Recommendation**: {result[criterion]['recommendation']}")
    
#     output.append(f"\n# Overall Analysis")
#     output.append(f"**Input Score**: {result['overall']['input_score']}/30")
#     output.append(f"**Improved Score**: {result['overall']['improved_score']}/30")
#     output.append(f"**Summary**: {result['overall']['summary']}")
    
#     output.append("\n# Improved User Story")
#     output.append(f"## Title\n{result['ImprovedUserStory']['Title']}")
#     output.append(f"## Description\n{result['ImprovedUserStory']['Description']}")
    
#     output.append("## Acceptance Criteria")
#     for i, criterion in enumerate(result['ImprovedUserStory']['AcceptanceCriteria'], 1):
#         output.append(f"{i}. {criterion}")
    
#     if result['ImprovedUserStory']['AdditionalInformation']:
#         output.append(f"## Additional Information\n{result['ImprovedUserStory']['AdditionalInformation']}")
    
#     output.append("\n# Refinement Summary")
#     refinement_points = result['overall']['refinement_summary'].split('*')
#     for point in refinement_points:
#         if point.strip():
#             output.append(f"* {point.strip()}")
    
#     return "\n".join(output)

# @mcp.tool(description="Analyzes and refines user stories using provided INVEST criteria.")
# async def invest_analyze(
#     user_story: Dict[str, Any],  # Explicitly expect the full dictionary as user_story
#     format_output: Optional[bool] = True
# ) -> Dict[str, Any]:
#     """Refine a user story using provided INVEST criteria and provide improvement recommendations."""
#     try:
#         logger.info(f"Received user_story: {user_story}")
#         processed_story, invest_criteria, aspects, context, input_score = preprocess_input(user_story)
#         analysis_result = analyze_user_story(processed_story, invest_criteria, aspects, context, input_score)
        
#         if format_output:
#             formatted_results = format_invest_results(analysis_result)
#             return {"content": [{"type": "text", "text": formatted_results}]}
#         else:
#             return {"content": [{"type": "json", "json": analysis_result}]}
            
#     except Exception as e:
#         error_msg = f"Error analyzing user story: {str(e)}"
#         logger.error(error_msg)
#         return {
#             "content": [{"type": "text", "text": error_msg}],
#             "isError": True
#         }

# if __name__ == "__main__":
#     print("UserStory INVEST Analyzer MCP server running on stdio...")
#     mcp.run()







































# import os
# import json
# import re
# from typing import Dict, Any, List, Optional
# from langchain_groq import ChatGroq
# from dotenv import load_dotenv
# from langchain.schema import SystemMessage, HumanMessage
# from mcp.server.fastmcp import FastMCP
# import logging

# # Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

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

# def preprocess_input(user_input: str | Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Dict[str, Any]], str, str, int]:
#     """Preprocess user input to extract UserStory, INVEST criteria, and refinement guidance."""
#     try:
#         if isinstance(user_input, str):
#             data = json.loads(user_input)
#         else:
#             data = user_input

#         logger.info(f"Preprocessed input: {data}")

#         if "UserStory" not in data:
#             raise ValueError("Input must contain a 'UserStory' object with Title, Description, AcceptanceCriteria, and AdditionalInformation.")
        
#         user_story = data["UserStory"]
#         required_fields = ["Title", "Description", "AcceptanceCriteria", "AdditionalInformation"]
#         for field in required_fields:
#             if field not in user_story:
#                 raise ValueError(f"UserStory must contain the field: {field}")

#         invest_criteria = {}
#         required_criteria = ["Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable"]
#         for criterion in required_criteria:
#             if criterion not in data:
#                 raise ValueError(f"Input must contain '{criterion}' with score, explanation, and recommendation.")
#             invest_criteria[criterion] = {
#                 "score": data[criterion].get("score", 0),
#                 "explanation": data[criterion].get("explanation", ""),
#                 "recommendation": data[criterion].get("recommendation", "")
#             }
#             if not isinstance(invest_criteria[criterion]["score"], (int, float)):
#                 invest_criteria[criterion]["score"] = 0
#             invest_criteria[criterion]["score"] = max(1, min(5, int(invest_criteria[criterion]["score"])))

#         aspects_to_enhance = data.get("aspects_to_enhance", "No specific aspects provided.")
#         if not isinstance(aspects_to_enhance, str):
#             raise ValueError("'aspects_to_enhance' must be a string.")

#         additional_context = data.get("additional_context", "No additional context provided.")
#         if not isinstance(additional_context, str):
#             raise ValueError("'additional_context' must be a string.")

#         input_score = data.get("overall", {}).get("score", 0)
#         if not isinstance(input_score, (int, float)):
#             input_score = 0
#         input_score = max(0, min(30, int(input_score)))

#         return user_story, invest_criteria, aspects_to_enhance, additional_context, input_score

#     except json.JSONDecodeError:
#         raise ValueError("Invalid JSON format. Please ensure the input is a properly structured JSON object.")
#     except Exception as e:
#         raise ValueError(f"Error processing input: {str(e)}")

# def create_analysis_prompt(user_story: Dict[str, Any], invest_criteria: Dict[str, Dict[str, Any]], aspects_to_enhance: str, additional_context: str, input_score: int) -> List[SystemMessage | HumanMessage]:
#     """Create the prompt messages for user story refinement using provided INVEST criteria."""
#     user_story_str = json.dumps(user_story)
#     invest_criteria_str = json.dumps(invest_criteria)
#     messages = [
#         SystemMessage(content="""You are an expert agile coach specializing in refining user stories using the INVEST criteria. 
# Your task is to:
# 1. Use the provided user story and its existing INVEST scores as the original baseline.
# 2. Create an improved version based on the refinement guidance and provided recommendations.

# Follow this structured approach:
# - Use the provided original components (Title, Description, AcceptanceCriteria, AdditionalInformation) and INVEST scores as the starting point.
# - Identify weaknesses based on the provided scores, explanations, and recommendations.
# - Create an improved version addressing those weaknesses, incorporating the aspects to enhance and additional context.
# - If the aspects to enhance or additional context indicate "No specific aspects provided." or "No additional context provided.", focus on improving areas with lower scores based on the provided recommendations.
# - Re-score each INVEST criterion for the improved user story (1-5 scale).
# - Calculate the improved INVEST score by summing the improved scores.
# - Generate a detailed refinement summary comparing the two versions."""),
#         HumanMessage(content=f"""
#         # Original User Story: {user_story_str}

#         # Original INVEST Criteria: {invest_criteria_str}

#         ## Refinement Guidance

#         ### Aspects of the user story to enhance:
#         {aspects_to_enhance}

#         ### Additional information or context to consider:
#         {additional_context}

#         ## Task Overview

#         Refine the provided user story with these steps:

#         ### Step 1: Use the Original User Story and Scores
#         - Use the provided components (Title, Description, AcceptanceCriteria, AdditionalInformation).
#         - Use the provided INVEST scores and explanations as the baseline for the original story.
#         - The user has provided an input score of {input_score}/30 for the original story as the overall baseline.

#         ### Step 2: Create an Improved Version
#         - Generate an improved user story (Title, Description, AcceptanceCriteria, AdditionalInformation) addressing weaknesses identified in the provided INVEST criteria.
#         - Incorporate the aspects to enhance and additional context to guide the refinement.
#         - Re-score each INVEST criterion for the IMPROVED version (1-5 scale).
#         - Calculate the new total INVEST score for the improved version by summing the improved scores.

#         ### Step 3: Generate Analysis Output
#         - Include both original and improved user story components.
#         - For each INVEST criterion, use the provided original score, provide the improved score, use the provided explanation, and update the recommendation based on the improvements made.
#         - Ensure recommendations reflect the changes made in the improved version.

#         ### Step 4: Create a Dynamic Refinement Summary
#         - List specific improvements as bullet points (using '*' on new lines).
#         - Include concrete examples of changes between versions.
#         - End with "INVEST Score improved from {input_score}/30 to Y/30", where Y is the total improved score.

#         ## Response Format:

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
#           "INVESTAnalysis": {{
#             "Independent": {{
#               "OriginalScore": number,
#               "ImprovedScore": number,
#               "Explanation": "string",
#               "Recommendation": "string"
#             }},
#             "Negotiable": {{
#               "OriginalScore": number,
#               "ImprovedScore": number,
#               "Explanation": "string",
#               "Recommendation": "string"
#             }},
#             "Valuable": {{
#               "OriginalScore": number,
#               "ImprovedScore": number,
#               "Explanation": "string",
#               "Recommendation": "string"
#             }},
#             "Estimable": {{
#               "OriginalScore": number,
#               "ImprovedScore": number,
#               "Explanation": "string",
#               "Recommendation": "string"
#             }},
#             "Small": {{
#               "OriginalScore": number,
#               "ImprovedScore": number,
#               "Explanation": "string",
#               "Recommendation": "string"
#             }},
#             "Testable": {{
#               "OriginalScore": number,
#               "ImprovedScore": number,
#               "Explanation": "string",
#               "Recommendation": "string"
#             }}
#           }},
#           "Overall": {{
#             "InputScore": number,
#             "ImprovedScore": number,
#             "Summary": "string",
#             "RefinementSummary": ["string", ...]
#           }}
#         }}

#         IMPORTANT:
#         - Return ONLY raw JSON without markdown or backticks.
#         - Ensure scores are integers (1-5), overall scores sum correctly (max 30).
#         - Use the provided input_score ({input_score}/30) as the Overall.InputScore in the response.
#         - List RefinementSummary as an array of strings (one per bullet point).
#         - Use the provided INVEST scores and explanations as the original baseline.
#         """)
#     ]
#     return messages

# def analyze_user_story(user_story: Dict[str, Any], invest_criteria: Dict[str, Dict[str, Any]], aspects_to_enhance: str = "", additional_context: str = "", input_score: int = 0, chat_model=None) -> Dict[str, Any]:
#     """Refine the user story using provided INVEST criteria and generate an improved version."""
#     try:
#         if not chat_model:
#             chat_model = ChatGroq(model=GROQ_MODEL, api_key=GROQ_API_KEY)
        
#         analysis_prompt = create_analysis_prompt(user_story, invest_criteria, aspects_to_enhance, additional_context, input_score)
#         response = chat_model.invoke(analysis_prompt)
#         content = response.content.strip()
        
#         json_content = sanitize_json_string(content)
#         result = json.loads(json_content)
        
#         # Validate and restructure the result
#         required_sections = ["OriginalUserStory", "ImprovedUserStory", "INVESTAnalysis", "Overall"]
#         for section in required_sections:
#             if section not in result:
#                 if section == "OriginalUserStory":
#                     result[section] = user_story
#                 elif section == "ImprovedUserStory":
#                     result[section] = {"Title": "", "Description": "", "AcceptanceCriteria": [], "AdditionalInformation": ""}
#                 elif section == "INVESTAnalysis":
#                     result[section] = {criterion: {"OriginalScore": 0, "ImprovedScore": 0, "Explanation": "", "Recommendation": ""} for criterion in ["Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable"]}
#                 elif section == "Overall":
#                     result[section] = {"InputScore": input_score, "ImprovedScore": 0, "Summary": "", "RefinementSummary": []}
        
#         # Populate original scores and explanations from invest_criteria
#         criteria = ["Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable"]
#         for criterion in criteria:
#             if criterion in invest_criteria:
#                 result["INVESTAnalysis"][criterion]["OriginalScore"] = invest_criteria[criterion]["score"]
#                 result["INVESTAnalysis"][criterion]["Explanation"] = invest_criteria[criterion]["explanation"]
        
#         # Validate scores
#         for criterion in criteria:
#             result["INVESTAnalysis"][criterion]["OriginalScore"] = max(1, min(5, int(result["INVESTAnalysis"][criterion].get("OriginalScore", 0))))
#             result["INVESTAnalysis"][criterion]["ImprovedScore"] = max(1, min(5, int(result["INVESTAnalysis"][criterion].get("ImprovedScore", 0))))
        
#         # Calculate and validate overall scores
#         calculated_improved_score = sum(result["INVESTAnalysis"][c]["ImprovedScore"] for c in criteria)
#         result["Overall"]["InputScore"] = max(0, min(30, int(input_score)))
#         result["Overall"]["ImprovedScore"] = min(30, calculated_improved_score)
        
#         # Update RefinementSummary
#         if "RefinementSummary" in result["Overall"] and isinstance(result["Overall"]["RefinementSummary"], str):
#             result["Overall"]["RefinementSummary"] = [point.strip() for point in result["Overall"]["RefinementSummary"].split('*') if point.strip()]
#         result["Overall"]["RefinementSummary"] = [re.sub(r"INVEST Score improved from \d+/30 to \d+/30", f"INVEST Score improved from {input_score}/30 to {calculated_improved_score}/30", point) for point in result["Overall"]["RefinementSummary"]]
        
#         return result
        
#     except Exception as e:
#         return {
#             "error": f"Analysis failed: {str(e)}",
#             "OriginalUserStory": user_story,
#             "ImprovedUserStory": {"Title": "", "Description": "", "AcceptanceCriteria": [], "AdditionalInformation": ""},
#             "INVESTAnalysis": {criterion: {"OriginalScore": invest_criteria.get(criterion, {}).get("score", 0), "ImprovedScore": 0, "Explanation": invest_criteria.get(criterion, {}).get("explanation", ""), "Recommendation": ""} for criterion in ["Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable"]},
#             "Overall": {"InputScore": input_score, "ImprovedScore": 0, "Summary": "Error in analysis", "RefinementSummary": []}
#         }

# @mcp.tool(description="Analyzes and refines user stories using provided INVEST criteria.")
# async def invest_analyze(
#     user_story: Dict[str, Any],
#     format_output: Optional[bool] = False  # Default to JSON output
# ) -> Dict[str, Any]:
#     """Refine a user story using provided INVEST criteria and provide improvement recommendations."""
#     try:
#         logger.info(f"Received user_story: {user_story}")
#         processed_story, invest_criteria, aspects, context, input_score = preprocess_input(user_story)
#         analysis_result = analyze_user_story(processed_story, invest_criteria, aspects, context, input_score)
        
#         return {"content": [{"type": "json", "json": analysis_result}]}
            
#     except Exception as e:
#         error_msg = f"Error analyzing user story: {str(e)}"
#         logger.error(error_msg)
#         return {
#             "content": [{"type": "text", "text": error_msg}],
#             "isError": True
#         }

# if __name__ == "__main__":
#     print("UserStory INVEST Analyzer MCP server running on stdio...")
#     mcp.run()










# import os
# import json
# import re
# from typing import Dict, Any, List, Optional
# from langchain_groq import ChatGroq
# from dotenv import load_dotenv
# from langchain.schema import SystemMessage, HumanMessage
# from mcp.server.fastmcp import FastMCP
# from fastapi import FastAPI, Request
# import logging
# import time

# # Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Load environment variables
# load_dotenv()

# # Initialize MCP server
# mcp = FastMCP("userstory-invest-mcp")

# # Initialize FastAPI app
# app = FastAPI(title="UserStory INVEST Analyzer API")

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

# def preprocess_input(user_input: str | Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Dict[str, Any]], str, str, int]:
#     """Preprocess user input to extract UserStory, INVEST criteria, and refinement guidance."""
#     try:
#         if isinstance(user_input, str):
#             data = json.loads(user_input)
#         else:
#             data = user_input

#         logger.info(f"Preprocessed input: {data}")

#         if "UserStory" not in data:
#             raise ValueError("Input must contain a 'UserStory' object with Title, Description, AcceptanceCriteria, and AdditionalInformation.")
        
#         user_story = data["UserStory"]
#         required_fields = ["Title", "Description", "AcceptanceCriteria", "AdditionalInformation"]
#         for field in required_fields:
#             if field not in user_story:
#                 raise ValueError(f"UserStory must contain the field: {field}")

#         invest_criteria = {}
#         required_criteria = ["Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable"]
#         for criterion in required_criteria:
#             if criterion not in data:
#                 raise ValueError(f"Input must contain '{criterion}' with score, explanation, and recommendation.")
#             invest_criteria[criterion] = {
#                 "score": data[criterion].get("score", 0),
#                 "explanation": data[criterion].get("explanation", ""),
#                 "recommendation": data[criterion].get("recommendation", "")
#             }
#             if not isinstance(invest_criteria[criterion]["score"], (int, float)):
#                 invest_criteria[criterion]["score"] = 0
#             invest_criteria[criterion]["score"] = max(1, min(5, int(invest_criteria[criterion]["score"])))

#         aspects_to_enhance = data.get("aspects_to_enhance", "No specific aspects provided.")
#         if not isinstance(aspects_to_enhance, str):
#             raise ValueError("'aspects_to_enhance' must be a string.")

#         additional_context = data.get("additional_context", "No additional context provided.")
#         if not isinstance(additional_context, str):
#             raise ValueError("'additional_context' must be a string.")

#         input_score = data.get("overall", {}).get("score", 0)
#         if not isinstance(input_score, (int, float)):
#             input_score = 0
#         input_score = max(0, min(30, int(input_score)))

#         return user_story, invest_criteria, aspects_to_enhance, additional_context, input_score

#     except json.JSONDecodeError:
#         raise ValueError("Invalid JSON format. Please ensure the input is a properly structured JSON object.")
#     except Exception as e:
#         raise ValueError(f"Error processing input: {str(e)}")

# def create_analysis_prompt(user_story: Dict[str, Any], invest_criteria: Dict[str, Dict[str, Any]], aspects_to_enhance: str, additional_context: str, input_score: int) -> List[SystemMessage | HumanMessage]:
#     """Create the prompt messages for user story refinement using provided INVEST criteria."""
#     user_story_str = json.dumps(user_story)
#     invest_criteria_str = json.dumps(invest_criteria)
#     timestamp = time.time()  # Add timestamp for variability
#     messages = [
#         SystemMessage(content="""You are an expert agile coach specializing in refining user stories using the INVEST criteria. 
# Your task is to:
# 1. Use the provided user story and its existing INVEST scores as the original baseline.
# 2. Create an improved version that dynamically refines the original story, addressing all identified weaknesses.

# Follow this structured approach:
# - Use the provided original components (Title, Description, AcceptanceCriteria, AdditionalInformation) and INVEST scores as the starting point.
# - Identify weaknesses based on the provided scores, explanations, and recommendations, focusing on areas specified in aspects_to_enhance.
# - Generate an improved version that enhances all weak areas (e.g., testability if score is low), incorporating the aspects to enhance and additional context.
# - Ensure the improved story is noticeably different from the original in clarity, specificity, and quality, and varies creatively with each generation.
# - Re-score each INVEST criterion for the improved user story (1-5 scale), aiming for a perfect 30/30.
# - Calculate the improved INVEST score by summing the improved scores.
# - Generate a detailed refinement summary highlighting the differences."""),
#         HumanMessage(content=f"""
#         # Original User Story: {user_story_str}

#         # Original INVEST Criteria: {invest_criteria_str}

#         ## Refinement Guidance

#         ### Aspects of the user story to enhance:
#         {aspects_to_enhance}

#         ### Additional information or context to consider:
#         {additional_context}

#         ## Task Overview

#         Refine the provided user story with these steps:

#         ### Step 1: Use the Original User Story and Scores
#         - Use the provided components (Title, Description, AcceptanceCriteria, AdditionalInformation).
#         - Use the provided INVEST scores and explanations as the baseline for the original story.
#         - The user has provided an input score of {input_score}/30 for the original story as the overall baseline.

#         ### Step 2: Create an Improved Version
#         - Generate an improved user story (Title, Description, AcceptanceCriteria, AdditionalInformation) dynamically based on the original story, addressing weaknesses identified in the provided INVEST criteria.
#         - Incorporate the aspects to enhance and additional context to guide the refinement.
#         - Ensure the improved version varies creatively with each run, avoiding repetition of exact phrasing unless structurally required, while maintaining the original intent.
#         - Re-score each INVEST criterion for the IMPROVED version (1-5 scale), targeting improvements where scores are low (e.g., Testable to 5/5 if originally low).
#         - Calculate the new total INVEST score for the improved version by summing the improved scores (target: 30/30).

#         ### Step 3: Generate Analysis Output
#         - Include both original and improved user story components.
#         - For each INVEST criterion, use the provided original score, provide the improved score, use the provided explanation, and update the recommendation based on the improvements made.
#         - Ensure recommendations reflect the changes made in the improved version.

#         ### Step 4: Create a Dynamic Refinement Summary
#         - List specific improvements as bullet points (using '*' on new lines).
#         - Include concrete examples of changes between versions, emphasizing improvements in weak areas.
#         - End with "INVEST Score improved from {input_score}/30 to Y/30", where Y is the total improved score.

#         ## Response Format:

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
#           "INVESTAnalysis": {{
#             "Independent": {{
#               "OriginalScore": number,
#               "ImprovedScore": number,
#               "Explanation": "string",
#               "Recommendation": "string"
#             }},
#             "Negotiable": {{
#               "OriginalScore": number,
#               "ImprovedScore": number,
#               "Explanation": "string",
#               "Recommendation": "string"
#             }},
#             "Valuable": {{
#               "OriginalScore": number,
#               "ImprovedScore": number,
#               "Explanation": "string",
#               "Recommendation": "string"
#             }},
#             "Estimable": {{
#               "OriginalScore": number,
#               "ImprovedScore": number,
#               "Explanation": "string",
#               "Recommendation": "string"
#             }},
#             "Small": {{
#               "OriginalScore": number,
#               "ImprovedScore": number,
#               "Explanation": "string",
#               "Recommendation": "string"
#             }},
#             "Testable": {{
#               "OriginalScore": number,
#               "ImprovedScore": number,
#               "Explanation": "string",
#               "Recommendation": "string"
#             }}
#           }},
#           "Overall": {{
#             "InputScore": number,
#             "ImprovedScore": number,
#             "Summary": "string",
#             "RefinementSummary": ["string", ...]
#           }}
#         }}

#         IMPORTANT:
#         - Return ONLY raw JSON without markdown or backticks.
#         - Ensure scores are integers (1-5), overall scores sum correctly (max 30).
#         - Use the provided input_score ({input_score}/30) as the Overall.InputScore in the response.
#         - List RefinementSummary as an array of strings (one per bullet point).
#         - Generate the ImprovedUserStory dynamically based on the input, enhancing weak areas (e.g., add detailed, testable acceptance criteria if Testable is low) without hardcoding a specific story.
#         - Introduce creative variations in phrasing with each run to reflect the timestamp: {timestamp}.
#         - Use the provided INVEST scores and explanations as the original baseline.
#         """)
#     ]
#     return messages

# def analyze_user_story(user_story: Dict[str, Any], invest_criteria: Dict[str, Dict[str, Any]], aspects_to_enhance: str = "", additional_context: str = "", input_score: int = 0, chat_model=None) -> Dict[str, Any]:
#     """Refine the user story using provided INVEST criteria and generate an improved version."""
#     try:
#         if not chat_model:
#             chat_model = ChatGroq(model=GROQ_MODEL, api_key=GROQ_API_KEY, temperature=0.5)
        
#         analysis_prompt = create_analysis_prompt(user_story, invest_criteria, aspects_to_enhance, additional_context, input_score)
#         response = chat_model.invoke(analysis_prompt)
#         content = response.content.strip()
        
#         json_content = sanitize_json_string(content)
#         result = json.loads(json_content)
        
#         # Validate and restructure the result
#         required_sections = ["OriginalUserStory", "ImprovedUserStory", "INVESTAnalysis", "Overall"]
#         for section in required_sections:
#             if section not in result:
#                 if section == "OriginalUserStory":
#                     result[section] = user_story
#                 elif section == "ImprovedUserStory":
#                     result[section] = {
#                         "Title": user_story["Title"],
#                         "Description": f"{user_story['Description']} (Refined for clarity and testability)",
#                         "AcceptanceCriteria": user_story["AcceptanceCriteria"] + ["Additional criteria added for verification."],
#                         "AdditionalInformation": f"{user_story['AdditionalInformation']} Enhanced dynamically."
#                     }
#                 elif section == "INVESTAnalysis":
#                     result[section] = {criterion: {"OriginalScore": 0, "ImprovedScore": 0, "Explanation": "", "Recommendation": ""} for criterion in ["Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable"]}
#                 elif section == "Overall":
#                     result[section] = {"InputScore": input_score, "ImprovedScore": 0, "Summary": "", "RefinementSummary": []}
        
#         # Populate original scores and explanations from invest_criteria
#         criteria = ["Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable"]
#         for criterion in criteria:
#             if criterion in invest_criteria:
#                 result["INVESTAnalysis"][criterion]["OriginalScore"] = invest_criteria[criterion]["score"]
#                 result["INVESTAnalysis"][criterion]["Explanation"] = invest_criteria[criterion]["explanation"]
        
#         # Validate scores
#         for criterion in criteria:
#             result["INVESTAnalysis"][criterion]["OriginalScore"] = max(1, min(5, int(result["INVESTAnalysis"][criterion].get("OriginalScore", 0))))
#             result["INVESTAnalysis"][criterion]["ImprovedScore"] = max(1, min(5, int(result["INVESTAnalysis"][criterion].get("ImprovedScore", 0))))
        
#         # Calculate and validate overall scores
#         calculated_improved_score = sum(result["INVESTAnalysis"][c]["ImprovedScore"] for c in criteria)
#         result["Overall"]["InputScore"] = max(0, min(30, int(input_score)))
#         result["Overall"]["ImprovedScore"] = min(30, calculated_improved_score)
        
#         # Update RefinementSummary
#         if "RefinementSummary" in result["Overall"] and isinstance(result["Overall"]["RefinementSummary"], str):
#             result["Overall"]["RefinementSummary"] = [point.strip() for point in result["Overall"]["RefinementSummary"].split('*') if point.strip()]
#         result["Overall"]["RefinementSummary"] = [re.sub(r"INVEST Score improved from \d+/30 to \d+/30", f"INVEST Score improved from {input_score}/30 to {calculated_improved_score}/30", point) for point in result["Overall"]["RefinementSummary"]]
        
#         return result
        
#     except Exception as e:
#         return {
#             "error": f"Analysis failed: {str(e)}",
#             "OriginalUserStory": user_story,
#             "ImprovedUserStory": {
#                 "Title": user_story["Title"],
#                 "Description": f"{user_story['Description']} (Refined dynamically due to error)",
#                 "AcceptanceCriteria": user_story["AcceptanceCriteria"] + ["Fallback criteria for testing added."],
#                 "AdditionalInformation": f"{user_story['AdditionalInformation']} Enhanced with minimal context."
#             },
#             "INVESTAnalysis": {criterion: {"OriginalScore": invest_criteria.get(criterion, {}).get("score", 0), "ImprovedScore": 0, "Explanation": invest_criteria.get(criterion, {}).get("explanation", ""), "Recommendation": ""} for criterion in ["Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable"]},
#             "Overall": {"InputScore": input_score, "ImprovedScore": 0, "Summary": "Error in analysis", "RefinementSummary": []}
#         }

# @mcp.tool(description="Analyzes and refines user stories using provided INVEST criteria.")
# async def invest_analyze(user_story: Dict[str, Any], format_output: Optional[bool] = False) -> Dict[str, Any]:
#     """Refine a user story using provided INVEST criteria and provide improvement recommendations."""
#     try:
#         logger.info(f"Received user_story: {user_story}")
#         processed_story, invest_criteria, aspects, context, input_score = preprocess_input(user_story)
#         analysis_result = analyze_user_story(processed_story, invest_criteria, aspects, context, input_score)
        
#         return {"content": [{"type": "json", "json": analysis_result}]}
            
#     except Exception as e:
#         error_msg = f"Error analyzing user story: {str(e)}"
#         logger.error(error_msg)
#         return {
#             "content": [{"type": "text", "text": error_msg}],
#             "isError": True
#         }

# @app.post("/invest_analyze")
# async def http_invest_analyze(request: Request):
#     """HTTP endpoint to analyze and refine a user story."""
#     try:
#         data = await request.json()
#         result = await invest_analyze(data)
#         return result
#     except json.JSONDecodeError:
#         return {"content": [{"type": "text", "text": "Invalid JSON format"}], "isError": True}
#     except Exception as e:
#         return {"content": [{"type": "text", "text": f"Error: {str(e)}"}], "isError": True}

# if __name__ == "__main__":
#     import uvicorn
#     # Uncomment the line below to run as MCP server instead of FastAPI
#     # print("UserStory INVEST Analyzer MCP server running on stdio...")
#     # mcp.run()
#     print("Starting FastAPI server for UserStory INVEST Analyzer...")
#     uvicorn.run(app, host="127.0.0.1", port=8000)








# import os
# import json
# import re
# from typing import Dict, Any, List, Optional
# from langchain_groq import ChatGroq
# from dotenv import load_dotenv
# from langchain.schema import SystemMessage, HumanMessage
# from mcp.server.fastmcp import FastMCP
# from fastapi import FastAPI, Request
# from fastapi.responses import JSONResponse
# from pydantic import BaseModel
# import logging
# import time

# # Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Load environment variables
# load_dotenv()

# # Initialize MCP server
# mcp = FastMCP("userstory-invest-mcp")

# # Initialize FastAPI app
# app = FastAPI(title="UserStory INVEST Analyzer API")

# # Validate environment variables
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# GROQ_MODEL = os.getenv("GROQ_MODEL")

# if not GROQ_API_KEY or not GROQ_MODEL:
#     raise ValueError("GROQ_API_KEY or GROQ_MODEL environment variables not set")

# # Pydantic Model for Input Validation
# class UserStoryInput(BaseModel):
#     UserStory: Dict[str, Any]
#     Independent: Dict[str, Any]
#     Negotiable: Dict[str, Any]
#     Valuable: Dict[str, Any]
#     Estimable: Dict[str, Any]
#     Small: Dict[str, Any]
#     Testable: Dict[str, Any]
#     overall: Dict[str, Any]
#     aspects_to_enhance: str
#     additional_context: str

# # Pydantic Model for Response
# class AnalysisResponse(BaseModel):
#     content: List[Dict[str, Any]]
#     isError: Optional[bool] = False

# def sanitize_json_string(json_str):
#     """Sanitize a JSON string by removing or replacing control characters."""
#     json_str = re.sub(r'[\x00-\x09\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', json_str)
#     def clean_string_value(match):
#         value = match.group(1)
#         value = value.replace('\n', '\\n').replace('\t', '\\t').replace('\r', '\\r')
#         return f'"{value}"'
#     json_str = re.sub(r'"((?:\\.|[^"\\])*)"', clean_string_value, json_str)
#     return json_str

# def preprocess_input(user_input: str | Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Dict[str, Any]], str, str, int]:
#     """Preprocess user input to extract UserStory, INVEST criteria, and refinement guidance."""
#     try:
#         if isinstance(user_input, str):
#             data = json.loads(user_input)
#         else:
#             data = user_input

#         logger.info(f"Preprocessed input: {data}")

#         if "UserStory" not in data:
#             raise ValueError("Input must contain a 'UserStory' object with Title, Description, AcceptanceCriteria, and AdditionalInformation.")
        
#         user_story = data["UserStory"]
#         required_fields = ["Title", "Description", "AcceptanceCriteria", "AdditionalInformation"]
#         for field in required_fields:
#             if field not in user_story:
#                 raise ValueError(f"UserStory must contain the field: {field}")

#         invest_criteria = {}
#         required_criteria = ["Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable"]
#         for criterion in required_criteria:
#             if criterion not in data:
#                 raise ValueError(f"Input must contain '{criterion}' with score, explanation, and recommendation.")
#             invest_criteria[criterion] = {
#                 "score": data[criterion].get("score", 0),
#                 "explanation": data[criterion].get("explanation", ""),
#                 "recommendation": data[criterion].get("recommendation", "")
#             }
#             if not isinstance(invest_criteria[criterion]["score"], (int, float)):
#                 invest_criteria[criterion]["score"] = 0
#             invest_criteria[criterion]["score"] = max(1, min(5, int(invest_criteria[criterion]["score"])))

#         aspects_to_enhance = data.get("aspects_to_enhance", "No specific aspects provided.")
#         if not isinstance(aspects_to_enhance, str):
#             raise ValueError("'aspects_to_enhance' must be a string.")

#         additional_context = data.get("additional_context", "No additional context provided.")
#         if not isinstance(additional_context, str):
#             raise ValueError("'additional_context' must be a string.")

#         input_score = data.get("overall", {}).get("score", 0)
#         if not isinstance(input_score, (int, float)):
#             input_score = 0
#         input_score = max(0, min(30, int(input_score)))

#         return user_story, invest_criteria, aspects_to_enhance, additional_context, input_score

#     except json.JSONDecodeError:
#         raise ValueError("Invalid JSON format. Please ensure the input is a properly structured JSON object.")
#     except Exception as e:
#         raise ValueError(f"Error processing input: {str(e)}")

# def create_analysis_prompt(user_story: Dict[str, Any], invest_criteria: Dict[str, Dict[str, Any]], aspects_to_enhance: str, additional_context: str, input_score: int) -> List[SystemMessage | HumanMessage]:
#     """Create the prompt messages for user story refinement using provided INVEST criteria."""
#     user_story_str = json.dumps(user_story)
#     invest_criteria_str = json.dumps(invest_criteria)
#     timestamp = time.time()  # Add timestamp for variability
#     messages = [
#         SystemMessage(content="""You are an expert agile coach specializing in refining user stories using the INVEST criteria. 
# Your task is to:
# 1. Use the provided user story and its existing INVEST scores as the original baseline.
# 2. Create an improved version that dynamically refines the original story, addressing all identified weaknesses.

# Follow this structured approach:
# - Use the provided original components (Title, Description, AcceptanceCriteria, AdditionalInformation) and INVEST scores as the starting point.
# - Identify weaknesses based on the provided scores, explanations, and recommendations, focusing on areas specified in aspects_to_enhance.
# - Generate an improved version that enhances all weak areas (e.g., testability if score is low), incorporating the aspects to enhance and additional context.
# - Ensure the improved story is noticeably different from the original in clarity, specificity, and quality, and varies creatively with each generation.
# - Re-score each INVEST criterion for the improved user story (1-5 scale), aiming for a perfect 30/30.
# - Calculate the improved INVEST score by summing the improved scores.
# - Generate a detailed refinement summary highlighting the differences."""),
#         HumanMessage(content=f"""
#         # Original User Story: {user_story_str}

#         # Original INVEST Criteria: {invest_criteria_str}

#         ## Refinement Guidance

#         ### Aspects of the user story to enhance:
#         {aspects_to_enhance}

#         ### Additional information or context to consider:
#         {additional_context}

#         ## Task Overview

#         Refine the provided user story with these steps:

#         ### Step 1: Use the Original User Story and Scores
#         - Use the provided components (Title, Description, AcceptanceCriteria, AdditionalInformation).
#         - Use the provided INVEST scores and explanations as the baseline for the original story.
#         - The user has provided an input score of {input_score}/30 for the original story as the overall baseline.

#         ### Step 2: Create an Improved Version
#         - Generate an improved user story (Title, Description, AcceptanceCriteria, AdditionalInformation) dynamically based on the original story, addressing weaknesses identified in the provided INVEST criteria.
#         - Incorporate the aspects to enhance and additional context to guide the refinement.
#         - Ensure the improved version varies creatively with each run, avoiding repetition of exact phrasing unless structurally required, while maintaining the original intent.
#         - Re-score each INVEST criterion for the IMPROVED version (1-5 scale), targeting improvements where scores are low (e.g., Testable to 5/5 if originally low).
#         - Calculate the new total INVEST score for the improved version by summing the improved scores (target: 30/30).

#         ### Step 3: Generate Analysis Output
#         - Include both original and improved user story components.
#         - For each INVEST criterion, use the provided original score, provide the improved score, use the provided explanation, and update the recommendation based on the improvements made.
#         - Ensure recommendations reflect the changes made in the improved version.

#         ### Step 4: Create a Dynamic Refinement Summary
#         - List specific improvements as bullet points (using '*' on new lines).
#         - Include concrete examples of changes between versions, emphasizing improvements in weak areas.
#         - End with "INVEST Score improved from {input_score}/30 to Y/30", where Y is the total improved score.

#         ## Response Format:

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
#           "INVESTAnalysis": {{
#             "Independent": {{
#               "OriginalScore": number,
#               "ImprovedScore": number,
#               "Explanation": "string",
#               "Recommendation": "string"
#             }},
#             "Negotiable": {{
#               "OriginalScore": number,
#               "ImprovedScore": number,
#               "Explanation": "string",
#               "Recommendation": "string"
#             }},
#             "Valuable": {{
#               "OriginalScore": number,
#               "ImprovedScore": number,
#               "Explanation": "string",
#               "Recommendation": "string"
#             }},
#             "Estimable": {{
#               "OriginalScore": number,
#               "ImprovedScore": number,
#               "Explanation": "string",
#               "Recommendation": "string"
#             }},
#             "Small": {{
#               "OriginalScore": number,
#               "ImprovedScore": number,
#               "Explanation": "string",
#               "Recommendation": "string"
#             }},
#             "Testable": {{
#               "OriginalScore": number,
#               "ImprovedScore": number,
#               "Explanation": "string",
#               "Recommendation": "string"
#             }}
#           }},
#           "Overall": {{
#             "InputScore": number,
#             "ImprovedScore": number,
#             "Summary": "string",
#             "RefinementSummary": ["string", ...]
#           }}
#         }}

#         IMPORTANT:
#         - Return ONLY raw JSON without markdown or backticks.
#         - Ensure scores are integers (1-5), overall scores sum correctly (max 30).
#         - Use the provided input_score ({input_score}/30) as the Overall.InputScore in the response.
#         - List RefinementSummary as an array of strings (one per bullet point).
#         - Generate the ImprovedUserStory dynamically based on the input, enhancing weak areas (e.g., add detailed, testable acceptance criteria if Testable is low) without hardcoding a specific story.
#         - Introduce creative variations in phrasing with each run to reflect the timestamp: {timestamp}.
#         - Use the provided INVEST scores and explanations as the original baseline.
#         """)
#     ]
#     return messages

# def analyze_user_story(user_story: Dict[str, Any], invest_criteria: Dict[str, Dict[str, Any]], aspects_to_enhance: str = "", additional_context: str = "", input_score: int = 0, chat_model=None) -> Dict[str, Any]:
#     """Refine the user story using provided INVEST criteria and generate an improved version."""
#     try:
#         if not chat_model:
#             chat_model = ChatGroq(model=GROQ_MODEL, api_key=GROQ_API_KEY, temperature=0.9)
        
#         analysis_prompt = create_analysis_prompt(user_story, invest_criteria, aspects_to_enhance, additional_context, input_score)
#         response = chat_model.invoke(analysis_prompt)
#         content = response.content.strip()
        
#         json_content = sanitize_json_string(content)
#         result = json.loads(json_content)
        
#         # Validate and restructure the result
#         required_sections = ["OriginalUserStory", "ImprovedUserStory", "INVESTAnalysis", "Overall"]
#         for section in required_sections:
#             if section not in result:
#                 if section == "OriginalUserStory":
#                     result[section] = user_story
#                 elif section == "ImprovedUserStory":
#                     result[section] = {
#                         "Title": user_story["Title"],
#                         "Description": f"{user_story['Description']} (Refined for clarity and testability)",
#                         "AcceptanceCriteria": user_story["AcceptanceCriteria"] + ["Additional criteria added for verification."],
#                         "AdditionalInformation": f"{user_story['AdditionalInformation']} Enhanced dynamically."
#                     }
#                 elif section == "INVESTAnalysis":
#                     result[section] = {criterion: {"OriginalScore": 0, "ImprovedScore": 0, "Explanation": "", "Recommendation": ""} for criterion in ["Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable"]}
#                 elif section == "Overall":
#                     result[section] = {"InputScore": input_score, "ImprovedScore": 0, "Summary": "", "RefinementSummary": []}
        
#         # Populate original scores and explanations from invest_criteria
#         criteria = ["Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable"]
#         for criterion in criteria:
#             if criterion in invest_criteria:
#                 result["INVESTAnalysis"][criterion]["OriginalScore"] = invest_criteria[criterion]["score"]
#                 result["INVESTAnalysis"][criterion]["Explanation"] = invest_criteria[criterion]["explanation"]
        
#         # Validate scores
#         for criterion in criteria:
#             result["INVESTAnalysis"][criterion]["OriginalScore"] = max(1, min(5, int(result["INVESTAnalysis"][criterion].get("OriginalScore", 0))))
#             result["INVESTAnalysis"][criterion]["ImprovedScore"] = max(1, min(5, int(result["INVESTAnalysis"][criterion].get("ImprovedScore", 0))))
        
#         # Calculate and validate overall scores
#         calculated_improved_score = sum(result["INVESTAnalysis"][c]["ImprovedScore"] for c in criteria)
#         result["Overall"]["InputScore"] = max(0, min(30, int(input_score)))
#         result["Overall"]["ImprovedScore"] = min(30, calculated_improved_score)
        
#         # Update RefinementSummary
#         if "RefinementSummary" in result["Overall"] and isinstance(result["Overall"]["RefinementSummary"], str):
#             result["Overall"]["RefinementSummary"] = [point.strip() for point in result["Overall"]["RefinementSummary"].split('*') if point.strip()]
#         result["Overall"]["RefinementSummary"] = [re.sub(r"INVEST Score improved from \d+/30 to \d+/30", f"INVEST Score improved from {input_score}/30 to {calculated_improved_score}/30", point) for point in result["Overall"]["RefinementSummary"]]
        
#         return result
        
#     except Exception as e:
#         return {
#             "error": f"Analysis failed: {str(e)}",
#             "OriginalUserStory": user_story,
#             "ImprovedUserStory": {
#                 "Title": user_story["Title"],
#                 "Description": f"{user_story['Description']} (Refined dynamically due to error)",
#                 "AcceptanceCriteria": user_story["AcceptanceCriteria"] + ["Fallback criteria for testing added."],
#                 "AdditionalInformation": f"{user_story['AdditionalInformation']} Enhanced with minimal context."
#             },
#             "INVESTAnalysis": {criterion: {"OriginalScore": invest_criteria.get(criterion, {}).get("score", 0), "ImprovedScore": 0, "Explanation": invest_criteria.get(criterion, {}).get("explanation", ""), "Recommendation": ""} for criterion in ["Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable"]},
#             "Overall": {"InputScore": input_score, "ImprovedScore": 0, "Summary": "Error in analysis", "RefinementSummary": []}
#         }

# @mcp.tool(description="Analyzes and refines user stories using provided INVEST criteria.")
# async def invest_analyze(user_story: Dict[str, Any], format_output: Optional[bool] = False) -> Dict[str, Any]:
#     """Refine a user story using provided INVEST criteria and provide improvement recommendations."""
#     try:
#         logger.info(f"Received user_story: {user_story}")
#         processed_story, invest_criteria, aspects, context, input_score = preprocess_input(user_story)
#         analysis_result = analyze_user_story(processed_story, invest_criteria, aspects, context, input_score)
        
#         return {"content": [{"type": "json", "json": analysis_result}]}
            
#     except Exception as e:
#         error_msg = f"Error analyzing user story: {str(e)}"
#         logger.error(error_msg)
#         return {
#             "content": [{"type": "text", "text": error_msg}],
#             "isError": True
#         }

# @app.post("/invest_analyze", response_model=AnalysisResponse)
# async def http_invest_analyze(user_story_input: UserStoryInput):
#     """HTTP endpoint to analyze and refine a user story."""
#     try:
#         data = user_story_input.dict()
#         result = await invest_analyze(data)
#         return JSONResponse(content=result)
#     except json.JSONDecodeError:
#         return JSONResponse(content={"content": [{"type": "text", "text": "Invalid JSON format"}], "isError": True})
#     except Exception as e:
#         return JSONResponse(content={"content": [{"type": "text", "text": f"Error: {str(e)}"}], "isError": True})

# if __name__ == "__main__":
#     import uvicorn
#     # Uncomment the line below to run as MCP server instead of FastAPI
#     # print("UserStory INVEST Analyzer MCP server running on stdio...")
#     # mcp.run()
#     print("Starting FastAPI server for UserStory INVEST Analyzer...")
#     uvicorn.run(app, host="127.0.0.1", port=8000)








# import os
# import json
# import re
# from typing import Dict, Any, List, Optional
# from langchain_groq import ChatGroq
# from dotenv import load_dotenv
# from langchain.schema import SystemMessage, HumanMessage
# from mcp.server.fastmcp import FastMCP
# from fastapi import FastAPI, Request
# from fastapi.responses import JSONResponse
# from pydantic import BaseModel, Field
# import logging
# import time

# # Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Load environment variables
# load_dotenv()

# # Initialize MCP server
# mcp = FastMCP("userstory-invest-mcp")

# # Initialize FastAPI app
# app = FastAPI(title="UserStory INVEST Analyzer API")

# # Validate environment variables
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# GROQ_MODEL = os.getenv("GROQ_MODEL")

# if not GROQ_API_KEY or not GROQ_MODEL:
#     raise ValueError("GROQ_API_KEY or GROQ_MODEL environment variables not set")

# # Pydantic Models
# class UserStory(BaseModel):
#     Title: str
#     Description: str
#     AcceptanceCriteria: List[str]
#     AdditionalInformation: str

# class InvestCriterion(BaseModel):
#     score: int = Field(ge=1, le=5)
#     explanation: str
#     recommendation: str

# class Overall(BaseModel):
#     score: int = Field(ge=0, le=30)
#     summary: Optional[str] = None

# class UserStoryInput(BaseModel):
#     UserStory: UserStory
#     Independent: InvestCriterion
#     Negotiable: InvestCriterion
#     Valuable: InvestCriterion
#     Estimable: InvestCriterion
#     Small: InvestCriterion
#     Testable: InvestCriterion
#     overall: Overall
#     aspects_to_enhance: str
#     additional_context: str

# class AnalysisResponse(BaseModel):
#     content: List[Dict[str, Any]]
#     isError: Optional[bool] = False

# def sanitize_json_string(json_str):
#     """Sanitize a JSON string by removing or replacing control characters."""
#     json_str = re.sub(r'[\x00-\x09\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', json_str)
#     def clean_string_value(match):
#         value = match.group(1)
#         value = value.replace('\n', '\\n').replace('\t', '\\t').replace('\r', '\\r')
#         return f'"{value}"'
#     json_str = re.sub(r'"((?:\\.|[^"\\])*)"', clean_string_value, json_str)
#     return json_str

# def preprocess_input(user_input: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Dict[str, Any]], str, str, int]:
#     """Preprocess user input to extract UserStory, INVEST criteria, and refinement guidance."""
#     try:
#         logger.info(f"Preprocessed input: {user_input}")

#         if "UserStory" not in user_input:
#             raise ValueError("Input must contain a 'UserStory' object with Title, Description, AcceptanceCriteria, and AdditionalInformation.")
        
#         user_story = user_input["UserStory"]
#         required_fields = ["Title", "Description", "AcceptanceCriteria", "AdditionalInformation"]
#         for field in required_fields:
#             if field not in user_story:
#                 raise ValueError(f"UserStory must contain the field: {field}")

#         invest_criteria = {}
#         required_criteria = ["Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable"]
#         for criterion in required_criteria:
#             if criterion not in user_input:
#                 raise ValueError(f"Input must contain '{criterion}' with score, explanation, and recommendation.")
#             invest_criteria[criterion] = {
#                 "score": user_input[criterion].get("score", 0),
#                 "explanation": user_input[criterion].get("explanation", ""),
#                 "recommendation": user_input[criterion].get("recommendation", "")
#             }
#             if not isinstance(invest_criteria[criterion]["score"], (int, float)):
#                 invest_criteria[criterion]["score"] = 0
#             invest_criteria[criterion]["score"] = max(1, min(5, int(invest_criteria[criterion]["score"])))

#         aspects_to_enhance = user_input.get("aspects_to_enhance", "No specific aspects provided.")
#         if not isinstance(aspects_to_enhance, str):
#             raise ValueError("'aspects_to_enhance' must be a string.")

#         additional_context = user_input.get("additional_context", "No additional context provided.")
#         if not isinstance(additional_context, str):
#             raise ValueError("'additional_context' must be a string.")

#         input_score = user_input.get("overall", {}).get("score", 0)
#         if not isinstance(input_score, (int, float)):
#             input_score = 0
#         input_score = max(0, min(30, int(input_score)))

#         return user_story, invest_criteria, aspects_to_enhance, additional_context, input_score

#     except json.JSONDecodeError:
#         raise ValueError("Invalid JSON format. Please ensure the input is a properly structured JSON object.")
#     except Exception as e:
#         raise ValueError(f"Error processing input: {str(e)}")

# def create_analysis_prompt(user_story: Dict[str, Any], invest_criteria: Dict[str, Dict[str, Any]], aspects_to_enhance: str, additional_context: str, input_score: int) -> List[SystemMessage | HumanMessage]:
#     """Create the prompt messages for user story refinement using provided INVEST criteria."""
#     user_story_str = json.dumps(user_story)
#     invest_criteria_str = json.dumps(invest_criteria)
#     timestamp = time.time()
#     messages = [
#         SystemMessage(content="""You are an expert agile coach specializing in refining user stories using the INVEST criteria. 
# Your task is to:
# 1. Use the provided user story and its existing INVEST scores as the original baseline.
# 2. Create an improved version that dynamically refines the original story, addressing all identified weaknesses.

# Follow this structured approach:
# - Use the provided original components (Title, Description, AcceptanceCriteria, AdditionalInformation) and INVEST scores as the starting point.
# - Identify weaknesses based on the provided scores, explanations, and recommendations, focusing on areas specified in aspects_to_enhance.
# - Generate an improved version that enhances all weak areas (e.g., testability if score is low), incorporating the aspects to enhance and additional context.
# - Ensure the improved story is noticeably different from the original in clarity, specificity, and quality, and varies creatively with each generation.
# - Re-score each INVEST criterion for the improved user story (1-5 scale), aiming for a perfect 30/30.
# - Calculate the improved INVEST score by summing the improved scores.
# - Generate a detailed refinement summary highlighting the differences."""),
#         HumanMessage(content=f"""
#         # Original User Story: {user_story_str}

#         # Original INVEST Criteria: {invest_criteria_str}

#         ## Refinement Guidance

#         ### Aspects of the user story to enhance:
#         {aspects_to_enhance}

#         ### Additional information or context to consider:
#         {additional_context}

#         ## Task Overview

#         Refine the provided user story with these steps:

#         ### Step 1: Use the Original User Story and Scores
#         - Use the provided components (Title, Description, AcceptanceCriteria, AdditionalInformation).
#         - Use the provided INVEST scores and explanations as the baseline for the original story.
#         - The user has provided an input score of {input_score}/30 for the original story as the overall baseline.

#         ### Step 2: Create an Improved Version
#         - Generate an improved user story (Title, Description, AcceptanceCriteria, AdditionalInformation) dynamically based on the original story, addressing weaknesses identified in the provided INVEST criteria.
#         - Incorporate the aspects to enhance and additional context to guide the refinement.
#         - Ensure the improved version varies creatively with each run, avoiding repetition of exact phrasing unless structurally required, while maintaining the original intent.
#         - Re-score each INVEST criterion for the IMPROVED version (1-5 scale), targeting improvements where scores are low (e.g., Testable to 5/5 if originally low).
#         - Calculate the new total INVEST score for the improved version by summing the improved scores (target: 30/30).

#         ### Step 3: Generate Analysis Output
#         - Include both original and improved user story components.
#         - For each INVEST criterion, use the provided original score, provide the improved score, use the provided explanation, and update the recommendation based on the improvements made.
#         - Ensure recommendations reflect the changes made in the improved version.

#         ### Step 4: Create a Dynamic Refinement Summary
#         - List specific improvements as bullet points (using '*' on new lines).
#         - Include concrete examples of changes between versions, emphasizing improvements in weak areas.
#         - End with "INVEST Score improved from {input_score}/30 to Y/30", where Y is the total improved score.

#         ## Response Format:

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
#           "INVESTAnalysis": {{
#             "Independent": {{
#               "OriginalScore": number,
#               "ImprovedScore": number,
#               "Explanation": "string",
#               "Recommendation": "string"
#             }},
#             "Negotiable": {{
#               "OriginalScore": number,
#               "ImprovedScore": number,
#               "Explanation": "string",
#               "Recommendation": "string"
#             }},
#             "Valuable": {{
#               "OriginalScore": number,
#               "ImprovedScore": number,
#               "Explanation": "string",
#               "Recommendation": "string"
#             }},
#             "Estimable": {{
#               "OriginalScore": number,
#               "ImprovedScore": number,
#               "Explanation": "string",
#               "Recommendation": "string"
#             }},
#             "Small": {{
#               "OriginalScore": number,
#               "ImprovedScore": number,
#               "Explanation": "string",
#               "Recommendation": "string"
#             }},
#             "Testable": {{
#               "OriginalScore": number,
#               "ImprovedScore": number,
#               "Explanation": "string",
#               "Recommendation": "string"
#             }}
#           }},
#           "Overall": {{
#             "InputScore": number,
#             "ImprovedScore": number,
#             "Summary": "string",
#             "RefinementSummary": ["string", ...]
#           }}
#         }}

#         IMPORTANT:
#         - Return ONLY raw JSON without markdown or backticks.
#         - Ensure scores are integers (1-5), overall scores sum correctly (max 30).
#         - Use the provided input_score ({input_score}/30) as the Overall.InputScore in the response.
#         - List RefinementSummary as an array of strings (one per bullet point).
#         - Generate the ImprovedUserStory dynamically based on the input, enhancing weak areas (e.g., add detailed, testable acceptance criteria if Testable is low) without hardcoding a specific story.
#         - Introduce creative variations in phrasing with each run to reflect the timestamp: {timestamp}.
#         - Use the provided INVEST scores and explanations as the original baseline.
#         """)
#     ]
#     return messages

# def analyze_user_story(user_story: Dict[str, Any], invest_criteria: Dict[str, Dict[str, Any]], aspects_to_enhance: str = "", additional_context: str = "", input_score: int = 0, chat_model=None) -> Dict[str, Any]:
#     """Refine the user story using provided INVEST criteria and generate an improved version."""
#     try:
#         if not chat_model:
#             chat_model = ChatGroq(model=GROQ_MODEL, api_key=GROQ_API_KEY, temperature=0.9)
        
#         analysis_prompt = create_analysis_prompt(user_story, invest_criteria, aspects_to_enhance, additional_context, input_score)
#         response = chat_model.invoke(analysis_prompt)
#         content = response.content.strip()
        
#         json_content = sanitize_json_string(content)
#         result = json.loads(json_content)
        
#         # Validate and restructure the result
#         required_sections = ["OriginalUserStory", "ImprovedUserStory", "INVESTAnalysis", "Overall"]
#         for section in required_sections:
#             if section not in result:
#                 if section == "OriginalUserStory":
#                     result[section] = user_story
#                 elif section == "ImprovedUserStory":
#                     result[section] = {
#                         "Title": user_story["Title"],
#                         "Description": f"{user_story['Description']} (Refined for clarity and testability)",
#                         "AcceptanceCriteria": user_story["AcceptanceCriteria"] + ["Additional criteria added for verification."],
#                         "AdditionalInformation": f"{user_story['AdditionalInformation']} Enhanced dynamically."
#                     }
#                 elif section == "INVESTAnalysis":
#                     result[section] = {criterion: {"OriginalScore": 0, "ImprovedScore": 0, "Explanation": "", "Recommendation": ""} for criterion in ["Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable"]}
#                 elif section == "Overall":
#                     result[section] = {"InputScore": input_score, "ImprovedScore": 0, "Summary": "", "RefinementSummary": []}
        
#         # Populate original scores and explanations from invest_criteria
#         criteria = ["Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable"]
#         for criterion in criteria:
#             if criterion in invest_criteria:
#                 result["INVESTAnalysis"][criterion]["OriginalScore"] = invest_criteria[criterion]["score"]
#                 result["INVESTAnalysis"][criterion]["Explanation"] = invest_criteria[criterion]["explanation"]
        
#         # Validate scores
#         for criterion in criteria:
#             result["INVESTAnalysis"][criterion]["OriginalScore"] = max(1, min(5, int(result["INVESTAnalysis"][criterion].get("OriginalScore", 0))))
#             result["INVESTAnalysis"][criterion]["ImprovedScore"] = max(1, min(5, int(result["INVESTAnalysis"][criterion].get("ImprovedScore", 0))))
        
#         # Calculate and validate overall scores
#         calculated_improved_score = sum(result["INVESTAnalysis"][c]["ImprovedScore"] for c in criteria)
#         result["Overall"]["InputScore"] = max(0, min(30, int(input_score)))
#         result["Overall"]["ImprovedScore"] = min(30, calculated_improved_score)
        
#         # Update RefinementSummary
#         if "RefinementSummary" in result["Overall"] and isinstance(result["Overall"]["RefinementSummary"], str):
#             result["Overall"]["RefinementSummary"] = [point.strip() for point in result["Overall"]["RefinementSummary"].split('*') if point.strip()]
#         result["Overall"]["RefinementSummary"] = [re.sub(r"INVEST Score improved from \d+/30 to \d+/30", f"INVEST Score improved from {input_score}/30 to {calculated_improved_score}/30", point) for point in result["Overall"]["RefinementSummary"]]
        
#         return result
        
#     except Exception as e:
#         return {
#             "error": f"Analysis failed: {str(e)}",
#             "OriginalUserStory": user_story,
#             "ImprovedUserStory": {
#                 "Title": user_story["Title"],
#                 "Description": f"{user_story['Description']} (Refined dynamically due to error)",
#                 "AcceptanceCriteria": user_story["AcceptanceCriteria"] + ["Fallback criteria for testing added."],
#                 "AdditionalInformation": f"{user_story['AdditionalInformation']} Enhanced with minimal context."
#             },
#             "INVESTAnalysis": {criterion: {"OriginalScore": invest_criteria.get(criterion, {}).get("score", 0), "ImprovedScore": 0, "Explanation": invest_criteria.get(criterion, {}).get("explanation", ""), "Recommendation": ""} for criterion in ["Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable"]},
#             "Overall": {"InputScore": input_score, "ImprovedScore": 0, "Summary": "Error in analysis", "RefinementSummary": []}
#         }

# @mcp.tool(description="Analyzes and refines user stories using provided INVEST criteria.")
# async def invest_analyze(user_story: Dict[str, Any], format_output: Optional[bool] = False) -> Dict[str, Any]:
#     """Refine a user story using provided INVEST criteria and provide improvement recommendations."""
#     try:
#         logger.info(f"Received user_story: {user_story}")
#         processed_story, invest_criteria, aspects, context, input_score = preprocess_input(user_story)
#         analysis_result = analyze_user_story(processed_story, invest_criteria, aspects, context, input_score)
        
#         return {"content": [{"type": "json", "json": analysis_result}]}
            
#     except Exception as e:
#         error_msg = f"Error analyzing user story: {str(e)}"
#         logger.error(error_msg)
#         return {
#             "content": [{"type": "text", "text": error_msg}],
#             "isError": True
#         }

# @app.post("/invest_analyze", response_model=AnalysisResponse)
# async def http_invest_analyze(user_story_input: UserStoryInput):
#     """HTTP endpoint to analyze and refine a user story."""
#     try:
#         data = user_story_input.dict(exclude_unset=True)
#         result = await invest_analyze(data)
#         return JSONResponse(content=result)
#     except json.JSONDecodeError:
#         return JSONResponse(content={"content": [{"type": "text", "text": "Invalid JSON format"}], "isError": True})
#     except ValueError as e:
#         return JSONResponse(content={"content": [{"type": "text", "text": str(e)}], "isError": True})
#     except Exception as e:
#         return JSONResponse(content={"content": [{"type": "text", "text": f"Error: {str(e)}"}], "isError": True})

# if __name__ == "__main__":
#     import uvicorn
#     print("Starting FastAPI server for UserStory INVEST Analyzer...")
#     uvicorn.run(app, host="127.0.0.1", port=8000)









import os
import json
import re
from typing import Dict, Any, List, Optional
from langchain_together import ChatTogether
from dotenv import load_dotenv
from langchain.schema import SystemMessage, HumanMessage
from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize MCP server
mcp = FastMCP("userstory-invest-mcp")

# Initialize FastAPI app
app = FastAPI(title="UserStory INVEST Analyzer API")

# Validate environment variables
Together_AI_API_KEY = os.getenv("Together_AI_API_KEY")
ToGetherAI_MODEL = os.getenv("ToGetherAI_MODEL")

if not Together_AI_API_KEY or not ToGetherAI_MODEL:
    raise ValueError("Together_AI_API_KEY or ToGetherAI_MODEL environment variables not set")

# Pydantic Models (kept for reference, but bypassed in debug mode)
class UserStory(BaseModel):
    Title: str
    Description: str
    AcceptanceCriteria: List[str]
    AdditionalInformation: str

class InvestCriterion(BaseModel):
    score: int = Field(ge=1, le=5)
    explanation: str
    recommendation: str

class Overall(BaseModel):
    score: int = Field(ge=0, le=30)
    summary: Optional[str] = None
    key_recommendations: Optional[List[str]] = None  # Added to match your updated JSON

class UserStoryInput(BaseModel):
    UserStory: UserStory
    Independent: InvestCriterion
    Negotiable: InvestCriterion
    Valuable: InvestCriterion
    Estimable: InvestCriterion
    Small: InvestCriterion
    Testable: InvestCriterion
    overall: Overall
    aspects_to_enhance: str
    additional_context: str

class AnalysisResponse(BaseModel):
    content: List[Dict[str, Any]]
    isError: Optional[bool] = False

def sanitize_json_string(json_str):
    """Sanitize a JSON string by removing or replacing control characters."""
    json_str = re.sub(r'[\x00-\x09\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', json_str)
    def clean_string_value(match):
        value = match.group(1)
        value = value.replace('\n', '\\n').replace('\t', '\\t').replace('\r', '\\r')
        return f'"{value}"'
    json_str = re.sub(r'"((?:\\.|[^"\\])*)"', clean_string_value, json_str)
    return json_str

def preprocess_input(user_input: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Dict[str, Any]], str, str, int]:
    """Preprocess user input to extract UserStory, INVEST criteria, and refinement guidance."""
    try:
        logger.info(f"Preprocessed input: {user_input}")

        if "UserStory" not in user_input:
            raise ValueError("Input must contain a 'UserStory' object with Title, Description, AcceptanceCriteria, and AdditionalInformation.")
        
        user_story = user_input["UserStory"]
        required_fields = ["Title", "Description", "AcceptanceCriteria", "AdditionalInformation"]
        for field in required_fields:
            if field not in user_story:
                raise ValueError(f"UserStory must contain the field: {field}")

        invest_criteria = {}
        required_criteria = ["Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable"]
        for criterion in required_criteria:
            if criterion not in user_input:
                raise ValueError(f"Input must contain '{criterion}' with score, explanation, and recommendation.")
            invest_criteria[criterion] = {
                "score": user_input[criterion].get("score", 0),
                "explanation": user_input[criterion].get("explanation", ""),
                "recommendation": user_input[criterion].get("recommendation", "")
            }
            if not isinstance(invest_criteria[criterion]["score"], (int, float)):
                invest_criteria[criterion]["score"] = 0
            invest_criteria[criterion]["score"] = max(1, min(5, int(invest_criteria[criterion]["score"])))

        aspects_to_enhance = user_input.get("aspects_to_enhance", "No specific aspects provided.")
        if not isinstance(aspects_to_enhance, str):
            raise ValueError("'aspects_to_enhance' must be a string.")

        additional_context = user_input.get("additional_context", "No additional context provided.")
        if not isinstance(additional_context, str):
            raise ValueError("'additional_context' must be a string.")

        input_score = user_input.get("overall", {}).get("score", 0)
        if not isinstance(input_score, (int, float)):
            input_score = 0
        input_score = max(0, min(30, int(input_score)))

        return user_story, invest_criteria, aspects_to_enhance, additional_context, input_score

    except json.JSONDecodeError:
        raise ValueError("Invalid JSON format. Please ensure the input is a properly structured JSON object.")
    except Exception as e:
        raise ValueError(f"Error processing input: {str(e)}")

def create_analysis_prompt(user_story: Dict[str, Any], invest_criteria: Dict[str, Dict[str, Any]], aspects_to_enhance: str, additional_context: str, input_score: int) -> List[SystemMessage | HumanMessage]:
    """Create the prompt messages for user story refinement using provided INVEST criteria."""
    user_story_str = json.dumps(user_story)
    invest_criteria_str = json.dumps(invest_criteria)
    timestamp = time.time()
    messages = [
        SystemMessage(content="""You are an expert agile coach specializing in refining user stories using the INVEST criteria. 
Your task is to:
1. Use the provided user story and its existing INVEST scores as the original baseline.
2. Create an improved version that dynamically refines the original story, addressing all identified weaknesses.

Follow this structured approach:
- Use the provided original components (Title, Description, AcceptanceCriteria, AdditionalInformation) and INVEST scores as the starting point.
- Identify weaknesses based on the provided scores, explanations, and recommendations, focusing on areas specified in aspects_to_enhance.
- Generate an improved version that enhances all weak areas (e.g., testability if score is low), incorporating the aspects to enhance and additional context.
- Ensure the improved story is noticeably different from the original in clarity, specificity, and quality, and varies creatively with each generation.
- Re-score each INVEST criterion for the improved user story (1-5 scale), aiming for a perfect 30/30.
- Calculate the improved INVEST score by summing the improved scores.
- Generate a detailed refinement summary highlighting the differences."""),
        HumanMessage(content=f"""
        # Original User Story: {user_story_str}

        # Original INVEST Criteria: {invest_criteria_str}

        ## Refinement Guidance

        ### Aspects of the user story to enhance:
        {aspects_to_enhance}

        ### Additional information or context to consider:
        {additional_context}

        ## Task Overview

        Refine the provided user story with these steps:

        ### Step 1: Use the Original User Story and Scores
        - Use the provided components (Title, Description, AcceptanceCriteria, AdditionalInformation).
        - Use the provided INVEST scores and explanations as the baseline for the original story.
        - The user has provided an input score of {input_score}/30 for the original story as the overall baseline.

        ### Step 2: Create an Improved Version
        - Generate an improved user story (Title, Description, AcceptanceCriteria, AdditionalInformation) dynamically based on the original story, addressing weaknesses identified in the provided INVEST criteria.
        - Incorporate the aspects to enhance and additional context to guide the refinement.
        - Ensure the improved version varies creatively with each run, avoiding repetition of exact phrasing unless structurally required, while maintaining the original intent.
        - Re-score each INVEST criterion for the IMPROVED version (1-5 scale), targeting improvements where scores are low (e.g., Testable to 5/5 if originally low).
        - Calculate the new total INVEST score for the improved version by summing the improved scores (target: 30/30).

        ### Step 3: Generate Analysis Output
        - Include both original and improved user story components.
        - For each INVEST criterion, use the provided original score, provide the improved score, use the provided explanation, and update the recommendation based on the improvements made.
        - Ensure recommendations reflect the changes made in the improved version.

        ### Step 4: Create a Dynamic Refinement Summary
        - List specific improvements as bullet points (using '*' on new lines).
        - Include concrete examples of changes between versions, emphasizing improvements in weak areas.
        - End with "INVEST Score improved from {input_score}/30 to Y/30", where Y is the total improved score.

        ## Response Format:

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
          "INVESTAnalysis": {{
            "Independent": {{
              "OriginalScore": number,
              "ImprovedScore": number,
              "Explanation": "string",
              "Recommendation": "string"
            }},
            "Negotiable": {{
              "OriginalScore": number,
              "ImprovedScore": number,
              "Explanation": "string",
              "Recommendation": "string"
            }},
            "Valuable": {{
              "OriginalScore": number,
              "ImprovedScore": number,
              "Explanation": "string",
              "Recommendation": "string"
            }},
            "Estimable": {{
              "OriginalScore": number,
              "ImprovedScore": number,
              "Explanation": "string",
              "Recommendation": "string"
            }},
            "Small": {{
              "OriginalScore": number,
              "ImprovedScore": number,
              "Explanation": "string",
              "Recommendation": "string"
            }},
            "Testable": {{
              "OriginalScore": number,
              "ImprovedScore": number,
              "Explanation": "string",
              "Recommendation": "string"
            }}
          }},
          "Overall": {{
            "InputScore": number,
            "ImprovedScore": number,
            "Summary": "string",
            "RefinementSummary": ["string", ...]
          }}
        }}

        IMPORTANT:
        - Return ONLY raw JSON without markdown or backticks.
        - Ensure scores are integers (1-5), overall scores sum correctly (max 30).
        - Use the provided input_score ({input_score}/30) as the Overall.InputScore in the response.
        - List RefinementSummary as an array of strings (one per bullet point).
        - Generate the ImprovedUserStory dynamically based on the input, enhancing weak areas (e.g., add detailed, testable acceptance criteria if Testable is low) without hardcoding a specific story.
        - Introduce creative variations in phrasing with each run to reflect the timestamp: {timestamp}.
        - Use the provided INVEST scores and explanations as the original baseline.
        """)
    ]
    return messages

def extract_json_from_text(text: str) -> str:
    """
    Extract JSON from text that might contain additional content before or after the JSON.
    Args:
        text: Text that contains JSON
    Returns:
        Extracted JSON string
    """
    json_pattern = r'(\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\}))*\})'
    match = re.search(json_pattern, text)
    if match:
        return match.group(1)
    return text

def analyze_user_story(user_story: Dict[str, Any], invest_criteria: Dict[str, Dict[str, Any]], aspects_to_enhance: str = "", additional_context: str = "", input_score: int = 0, chat_model=None) -> Dict[str, Any]:
    """Refine the user story using provided INVEST criteria and generate an improved version."""
    try:
        if not chat_model:
            chat_model = ChatTogether(model=ToGetherAI_MODEL, api_key=Together_AI_API_KEY, temperature=0.9)
        
        logger.info(f"Using model: {ToGetherAI_MODEL} with API key: {Together_AI_API_KEY[:5]}... (masked)")
        analysis_prompt = create_analysis_prompt(user_story, invest_criteria, aspects_to_enhance, additional_context, input_score)
        response = chat_model.invoke(analysis_prompt)
        content = response.content.strip() if response.content else ""
        logger.info(f"Raw model response: '{content}'")
        
        if not content:
            raise ValueError("Model returned empty response")
        
        # Extract JSON from the response
        json_content = extract_json_from_text(content)
        logger.info(f"Extracted JSON content: '{json_content}'")
        
        # Sanitize and parse the extracted JSON
        sanitized_json = sanitize_json_string(json_content)
        logger.info(f"Sanitized JSON content: '{sanitized_json}'")
        result = json.loads(sanitized_json)
        
        # Validate and restructure the result (rest of your existing code remains unchanged)
        required_sections = ["OriginalUserStory", "ImprovedUserStory", "INVESTAnalysis", "Overall"]
        for section in required_sections:
            if section not in result:
                if section == "OriginalUserStory":
                    result[section] = user_story
                elif section == "ImprovedUserStory":
                    result[section] = {
                        "Title": user_story["Title"],
                        "Description": f"{user_story['Description']} (Refined for clarity and testability)",
                        "AcceptanceCriteria": user_story["AcceptanceCriteria"] + ["Additional criteria added for verification."],
                        "AdditionalInformation": f"{user_story['AdditionalInformation']} Enhanced dynamically."
                    }
                elif section == "INVESTAnalysis":
                    result[section] = {criterion: {"OriginalScore": 0, "ImprovedScore": 0, "Explanation": "", "Recommendation": ""} for criterion in ["Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable"]}
                elif section == "Overall":
                    result[section] = {"InputScore": input_score, "ImprovedScore": 0, "Summary": "", "RefinementSummary": []}
        
        criteria = ["Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable"]
        for criterion in criteria:
            if criterion in invest_criteria:
                result["INVESTAnalysis"][criterion]["OriginalScore"] = invest_criteria[criterion]["score"]
                result["INVESTAnalysis"][criterion]["Explanation"] = invest_criteria[criterion]["explanation"]
        
        for criterion in criteria:
            result["INVESTAnalysis"][criterion]["OriginalScore"] = max(1, min(5, int(result["INVESTAnalysis"][criterion].get("OriginalScore", 0))))
            result["INVESTAnalysis"][criterion]["ImprovedScore"] = max(1, min(5, int(result["INVESTAnalysis"][criterion].get("ImprovedScore", 0))))
        
        calculated_improved_score = sum(result["INVESTAnalysis"][c]["ImprovedScore"] for c in criteria)
        result["Overall"]["InputScore"] = max(0, min(30, int(input_score)))
        result["Overall"]["ImprovedScore"] = min(30, calculated_improved_score)
        
        if "RefinementSummary" in result["Overall"] and isinstance(result["Overall"]["RefinementSummary"], str):
            result["Overall"]["RefinementSummary"] = [point.strip() for point in result["Overall"]["RefinementSummary"].split('*') if point.strip()]
        result["Overall"]["RefinementSummary"] = [re.sub(r"INVEST Score improved from \d+/30 to \d+/30", f"INVEST Score improved from {input_score}/30 to {calculated_improved_score}/30", point) for point in result["Overall"]["RefinementSummary"]]
        
        return result
        
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        return {
            "error": f"Analysis failed: {str(e)}",
            "OriginalUserStory": user_story,
            "ImprovedUserStory": {
                "Title": user_story["Title"],
                "Description": f"{user_story['Description']} (Refined dynamically due to error)",
                "AcceptanceCriteria": user_story["AcceptanceCriteria"] + ["Fallback criteria for testing added."],
                "AdditionalInformation": f"{user_story['AdditionalInformation']} Enhanced with minimal context."
            },
            "INVESTAnalysis": {criterion: {"OriginalScore": invest_criteria.get(criterion, {}).get("score", 0), "ImprovedScore": 0, "Explanation": invest_criteria.get(criterion, {}).get("explanation", ""), "Recommendation": ""} for criterion in ["Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable"]},
            "Overall": {"InputScore": input_score, "ImprovedScore": 0, "Summary": "Error in analysis", "RefinementSummary": []}
        }

@mcp.tool(description="Analyzes and refines user stories using provided INVEST criteria.")
async def invest_analyze(user_story: Dict[str, Any], format_output: Optional[bool] = False) -> Dict[str, Any]:
    """Refine a user story using provided INVEST criteria and provide improvement recommendations."""
    try:
        logger.info(f"Received user_story: {user_story}")
        processed_story, invest_criteria, aspects, context, input_score = preprocess_input(user_story)
        analysis_result = analyze_user_story(processed_story, invest_criteria, aspects, context, input_score)
        
        return {"content": [{"type": "json", "json": analysis_result}]}
            
    except Exception as e:
        error_msg = f"Error analyzing user story: {str(e)}"
        logger.error(error_msg)
        return {
            "content": [{"type": "text", "text": error_msg}],
            "isError": True
        }

@app.post("/invest_analyze")
async def http_invest_analyze(request: Request):
    """HTTP endpoint to analyze and refine a user story (debug mode)."""
    try:
        # Log the raw body as bytes
        raw_body_bytes = await request.body()
        logger.info(f"Raw request body (bytes): {raw_body_bytes}")

        # Decode the body
        raw_body = raw_body_bytes.decode('utf-8')
        logger.info(f"Raw request body (decoded): {raw_body}")

        # Attempt to parse as JSON
        parsed_data = json.loads(raw_body)
        logger.info(f"Parsed data: {parsed_data}")

        # Process with invest_analyze
        result = await invest_analyze(parsed_data)
        return JSONResponse(content=result)
    except json.JSONDecodeError as jde:
        return JSONResponse(content={"content": [{"type": "text", "text": f"Invalid JSON format: {str(jde)} - Raw body: {raw_body}"}], "isError": True})
    except Exception as e:
        return JSONResponse(content={"content": [{"type": "text", "text": f"Error: {str(e)}"}], "isError": True})

if __name__ == "__main__":
    print("UserStory INVEST Analyzer MCP server running on stdio...")
    mcp.run()
    import uvicorn
    print("Starting FastAPI server for UserStory INVEST Analyzer...")
    
    uvicorn.run(app, host="127.0.0.1", port=8000)