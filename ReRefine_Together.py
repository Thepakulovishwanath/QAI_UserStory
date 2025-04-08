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

def analyze_user_story(user_story: Dict[str, Any], invest_criteria: Dict[str, Dict[str, Any]], aspects_to_enhance: str = "", additional_context: str = "", input_score: int = 0, chat_model=None) -> Dict[str, Any]:
    """Refine the user story using provided INVEST criteria and generate an improved version."""
    try:
        if not chat_model:
            chat_model = ChatTogether(model=ToGetherAI_MODEL, api_key=Together_AI_API_KEY, temperature=0.9)
        
        analysis_prompt = create_analysis_prompt(user_story, invest_criteria, aspects_to_enhance, additional_context, input_score)
        response = chat_model.invoke(analysis_prompt)
        content = response.content.strip()
        
        json_content = sanitize_json_string(content)
        result = json.loads(json_content)
        
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
        
        # Populate original scores and explanations from invest_criteria
        criteria = ["Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable"]
        for criterion in criteria:
            if criterion in invest_criteria:
                result["INVESTAnalysis"][criterion]["OriginalScore"] = invest_criteria[criterion]["score"]
                result["INVESTAnalysis"][criterion]["Explanation"] = invest_criteria[criterion]["explanation"]
        
        # Validate scores
        for criterion in criteria:
            result["INVESTAnalysis"][criterion]["OriginalScore"] = max(1, min(5, int(result["INVESTAnalysis"][criterion].get("OriginalScore", 0))))
            result["INVESTAnalysis"][criterion]["ImprovedScore"] = max(1, min(5, int(result["INVESTAnalysis"][criterion].get("ImprovedScore", 0))))
        
        # Calculate and validate overall scores
        calculated_improved_score = sum(result["INVESTAnalysis"][c]["ImprovedScore"] for c in criteria)
        result["Overall"]["InputScore"] = max(0, min(30, int(input_score)))
        result["Overall"]["ImprovedScore"] = min(30, calculated_improved_score)
        
        # Update RefinementSummary
        if "RefinementSummary" in result["Overall"] and isinstance(result["Overall"]["RefinementSummary"], str):
            result["Overall"]["RefinementSummary"] = [point.strip() for point in result["Overall"]["RefinementSummary"].split('*') if point.strip()]
        result["Overall"]["RefinementSummary"] = [re.sub(r"INVEST Score improved from \d+/30 to \d+/30", f"INVEST Score improved from {input_score}/30 to {calculated_improved_score}/30", point) for point in result["Overall"]["RefinementSummary"]]
        
        return result
        
    except Exception as e:
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
    import uvicorn
    print("Starting FastAPI server for UserStory INVEST Analyzer...")
    uvicorn.run(app, host="127.0.0.1", port=8000)