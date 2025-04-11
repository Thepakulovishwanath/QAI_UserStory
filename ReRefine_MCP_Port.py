# import os
# import json
# import re
# from typing import Dict, Any, List, Optional
# from langchain_together import ChatTogether
# from dotenv import load_dotenv
# from langchain.schema import SystemMessage, HumanMessage
# from mcp.server.fastmcp import FastMCP
# import logging
# import time
# from aiohttp import web  # Add this for HTTP server

# # Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Load environment variables
# load_dotenv()

# # Initialize MCP server
# mcp = FastMCP("userstory-invest-mcp")

# # Validate environment variables
# Together_AI_API_KEY = os.getenv("Together_AI_API_KEY")
# ToGetherAI_MODEL = os.getenv("ToGetherAI_MODEL")

# if not Together_AI_API_KEY or not ToGetherAI_MODEL:
#     raise ValueError("Together_AI_API_KEY or ToGetherAI_MODEL environment variables not set")

# # [Your existing functions: sanitize_json_string, preprocess_input, create_analysis_prompt, extract_json_from_text, analyze_user_story remain unchanged]
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

# def extract_json_from_text(text: str) -> str:
#     """
#     Extract JSON from text that might contain additional content before or after the JSON.
#     """
#     json_pattern = r'(\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\}))*\})'
#     match = re.search(json_pattern, text)
#     if match:
#         return match.group(1)
#     return text

# def analyze_user_story(user_story: Dict[str, Any], invest_criteria: Dict[str, Dict[str, Any]], aspects_to_enhance: str = "", additional_context: str = "", input_score: int = 0, chat_model=None) -> Dict[str, Any]:
#     """Refine the user story using provided INVEST criteria and generate an improved version."""
#     try:
#         if not chat_model:
#             chat_model = ChatTogether(model=ToGetherAI_MODEL, api_key=Together_AI_API_KEY, temperature=0.9)
        
#         logger.info(f"Using model: {ToGetherAI_MODEL} with API key: {Together_AI_API_KEY[:5]}... (masked)")
#         analysis_prompt = create_analysis_prompt(user_story, invest_criteria, aspects_to_enhance, additional_context, input_score)
#         response = chat_model.invoke(analysis_prompt)
#         content = response.content.strip() if response.content else ""
#         logger.info(f"Raw model response: '{content}'")
        
#         if not content:
#             raise ValueError("Model returned empty response")
        
#         # Extract JSON from the response
#         json_content = extract_json_from_text(content)
#         logger.info(f"Extracted JSON content: '{json_content}'")
        
#         # Sanitize and parse the extracted JSON
#         sanitized_json = sanitize_json_string(json_content)
#         logger.info(f"Sanitized JSON content: '{sanitized_json}'")
#         result = json.loads(sanitized_json)
        
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
        
#         criteria = ["Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable"]
#         for criterion in criteria:
#             if criterion in invest_criteria:
#                 result["INVESTAnalysis"][criterion]["OriginalScore"] = invest_criteria[criterion]["score"]
#                 result["INVESTAnalysis"][criterion]["Explanation"] = invest_criteria[criterion]["explanation"]
        
#         for criterion in criteria:
#             result["INVESTAnalysis"][criterion]["OriginalScore"] = max(1, min(5, int(result["INVESTAnalysis"][criterion].get("OriginalScore", 0))))
#             result["INVESTAnalysis"][criterion]["ImprovedScore"] = max(1, min(5, int(result["INVESTAnalysis"][criterion].get("ImprovedScore", 0))))
        
#         calculated_improved_score = sum(result["INVESTAnalysis"][c]["ImprovedScore"] for c in criteria)
#         result["Overall"]["InputScore"] = max(0, min(30, int(input_score)))
#         result["Overall"]["ImprovedScore"] = min(30, calculated_improved_score)
        
#         if "RefinementSummary" in result["Overall"] and isinstance(result["Overall"]["RefinementSummary"], str):
#             result["Overall"]["RefinementSummary"] = [point.strip() for point in result["Overall"]["RefinementSummary"].split('*') if point.strip()]
#         result["Overall"]["RefinementSummary"] = [re.sub(r"INVEST Score improved from \d+/30 to \d+/30", f"INVEST Score improved from {input_score}/30 to {calculated_improved_score}/30", point) for point in result["Overall"]["RefinementSummary"]]
        
#         return result
        
#     except Exception as e:
#         logger.error(f"Analysis error: {str(e)}")
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

# # HTTP handler for MCP over port 5000
# async def handle_request(request):
#     try:
#         data = await request.json()
#         logger.info(f"Received HTTP request: {data}")
#         if not isinstance(data, dict) or "jsonrpc" not in data or "method" not in data:
#             return web.Response(text=json.dumps({"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}, "id": data.get("id", None)}), status=400, content_type="application/json")
        
#         method_name = data["method"]
#         params = data.get("params", {})
        
#         if method_name == "invest_analyze":
#             result = await invest_analyze(**params)
#             response = {"jsonrpc": "2.0", "result": result, "id": data["id"]}
#         else:
#             response = {"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": data["id"]}
        
#         return web.Response(text=json.dumps(response), content_type="application/json")
#     except Exception as e:
#         logger.error(f"Error handling request: {str(e)}")
#         return web.Response(text=json.dumps({"jsonrpc": "2.0", "error": {"code": -32000, "message": str(e)}, "id": data.get("id", None)}), status=500, content_type="application/json")

# if __name__ == "__main__":
#     PORT = 5000
#     app = web.Application()
#     app.router.add_post("/", handle_request)
#     print(f"Starting UserStory INVEST Analyzer MCP server on http://127.0.0.1:{PORT}...")
#     web.run_app(app, host="127.0.0.1", port=PORT)








import os
import json
import re
from typing import Dict, Any, List, Optional
from langchain_together import ChatTogether
from dotenv import load_dotenv
from langchain.schema import SystemMessage, HumanMessage
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Route, Mount
import uvicorn
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize MCP server
mcp = FastMCP("userstory-invest-mcp")

# Validate environment variables
Together_AI_API_KEY = os.getenv("Together_AI_API_KEY")
ToGetherAI_MODEL = os.getenv("ToGetherAI_MODEL")

if not Together_AI_API_KEY or not ToGetherAI_MODEL:
    raise ValueError("Together_AI_API_KEY or ToGetherAI_MODEL environment variables not set")


# [Your existing functions: sanitize_json_string, preprocess_input, create_analysis_prompt, extract_json_from_text, analyze_user_story remain unchanged]
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
        
        # Validate and restructure the result
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
        return {"content": [{"type": "text", "text": error_msg}], "isError": True}

# Set up SSE transport
sse = SseServerTransport("/messages/")

async def handle_sse(request: Request) -> None:
    _server = mcp._mcp_server
    async with sse.connect_sse(request.scope, request.receive, request._send) as (reader, writer):
        await _server.run(reader, writer, _server.create_initialization_options())

# Create Starlette app
app = Starlette(
    debug=True,
    routes=[
        Route("/sse", endpoint=handle_sse),
        Mount("/messages/", app=sse.handle_post_message),
    ],
)

if __name__ == "__main__":
    PORT = 5000
    print(f"Starting UserStory INVEST Analyzer MCP server on http://127.0.0.1:{PORT}/sse...")
    uvicorn.run(app, host="127.0.0.1", port=PORT)