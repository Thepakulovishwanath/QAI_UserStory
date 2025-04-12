from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os
from langchain.schema import SystemMessage, HumanMessage
import json
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn  # Added for programmatic server running
import logging
import threading
from mcp.server.fastmcp import FastMCP

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server for Claude Desktop
mcp = FastMCP("userstory-invest-mcp")

def sanitize_json_string(json_str):
    """Sanitize a JSON string by removing or replacing control characters."""
    json_str = re.sub(r'[\x00-\x09\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', json_str)
    def clean_string_value(match):
        value = match.group(1)
        value = value.replace('\n', '\\n').replace('\t', '\\t').replace('\r', '\\r')
        return f'"{value}"'
    json_str = re.sub(r'"((?:\\.|[^"\\])*)"', clean_string_value, json_str)
    return json_str

class UserStoryInvestAnalyzer:
    def __init__(self, chat_model=None):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = os.getenv("GROQ_MODEL")
        self.chat_model = chat_model
        if not self.api_key or not self.model:
            raise ValueError("GROQ_API_KEY or GROQ_MODEL environment variables not set")
        
    def initialize_chat_model(self):
        """Initialize and return the Groq chat model."""
        if not self.chat_model:
            self.chat_model = ChatGroq(model=self.model, api_key=self.api_key)
        return self.chat_model
        
    def create_analysis_prompt(self, user_story, aspects_to_enhance, additional_context, input_score, criteria_scores):
        """Create the prompt messages for user story extraction and INVEST analysis."""
        if not isinstance(user_story, str):
            user_story = json.dumps(user_story, ensure_ascii=False)
        else:
            try:
                json.loads(user_story)
            except json.JSONDecodeError:
                raise ValueError("user_story string is not valid JSON")
        
        user_story_escaped = json.dumps(user_story)[1:-1]  # Escape for prompt
        
        criteria_scores_text = "\n".join(
            f"- {criterion}: {score}/5" for criterion, score in criteria_scores.items()
        )
        
        messages = [
            SystemMessage(content="""You are an expert agile coach specializing in analyzing user stories using the INVEST criteria. 
            Your task is twofold:
            1. Analyze the original user story using the provided INVEST scores.
            2. Create an improved version and provide a detailed refinement summary, considering the provided refinement guidance.

            Follow this structured approach:
            - Extract the original components (Title, Description, AcceptanceCriteria, AdditionalInformation).
            - Use the provided INVEST scores for the original story as given.
            - Identify specific weaknesses in the original story based on the provided scores and explanations.
            - Create an improved version addressing those weaknesses, incorporating the aspects to enhance and additional context provided.
            - If the aspects to enhance or additional context indicate "No specific aspects provided." or "No additional context provided.", perform a general refinement based on INVEST criteria, focusing on clarity, testability, and estimability.
            - Re-score each INVEST criterion for the improved user story (1-5 scale).
            - Calculate the improved INVEST score by summing the improved scores.
            - Generate a detailed refinement summary comparing the two versions.

            Return ONLY raw JSON without markdown or backticks."""),
            HumanMessage(content=f"""
            # User Story: {user_story_escaped}

            ## Original INVEST Scores:
            {criteria_scores_text}
            Total: {input_score}/30

            ## Refinement Guidance

            ### Aspects of the user story to enhance:
            {aspects_to_enhance}

            ### Additional information or context to consider:
            {additional_context}

            ## Task Overview

            Perform a complete INVEST analysis on the provided user story with these steps:

            ### Step 1: Analyze the Original User Story
            - Extract all components (Title, Description, AcceptanceCriteria, AdditionalInformation).
            - Use the provided INVEST scores for the original story as listed above.
            - Identify weaknesses based on the provided scores.

            ### Step 2: Create an Improved Version
            - Generate an improved user story addressing each weakness.
            - Consider the aspects to enhance and additional context to guide the refinement.
            - Re-score each INVEST criterion for the IMPROVED version (1-5 scale).
            - Calculate the new total INVEST score.

            ### Step 3: Generate Analysis Output
            - Include both original and improved user story components.
            - For each INVEST criterion, provide the original score (as provided), improved score, explanation, and recommendation.
            - Ensure explanations reflect the actual content and provided scores.

            ### Step 4: Create a Refinement Summary
            - List improvements as bullet points (using '*' on new lines).
            - Include examples of changes.
            - End with "INVEST Score improved from {input_score}/30 to Y/30", where Y is the total improved score.

            ## Response Format:
            {{
              "OriginalUserStory": {{"Title": "string", "Description": "string", "AcceptanceCriteria": ["string", ...], "AdditionalInformation": "string"}},
              "ImprovedUserStory": {{"Title": "string", "Description": "string", "AcceptanceCriteria": ["string", ...], "AdditionalInformation": "string"}},
              "Independent": {{"score": number, "improved_score": number, "explanation": "string", "recommendation": "string"}},
              "Negotiable": {{"score": number, "improved_score": number, "explanation": "string", "recommendation": "string"}},
              "Valuable": {{"score": number, "improved_score": number, "explanation": "string", "recommendation": "string"}},
              "Estimable": {{"score": number, "improved_score": number, "explanation": "string", "recommendation": "string"}},
              "Small": {{"score": number, "improved_score": number, "explanation": "string", "recommendation": "string"}},
              "Testable": {{"score": number, "improved_score": number, "explanation": "string", "recommendation": "string"}},
              "overall": {{"input_score": number, "improved_score": number, "summary": "string", "refinement_summary": "string with '*' bullets"}}
            }}
            """)
        ]
        return messages
    
    @mcp.tool(description="Analyzes and refines user stories using provided INVEST criteria.")       
    def analyze_user_story(self, user_story, aspects_to_enhance="", additional_context="", input_score=0, criteria_scores=None):
        """Extract components and perform INVEST analysis with refinement guidance."""
        if criteria_scores is None:
            criteria_scores = {c: 0 for c in ["Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable"]}
        
        try:
            chat_model = self.initialize_chat_model()
            analysis_prompt = self.create_analysis_prompt(user_story, aspects_to_enhance, additional_context, input_score, criteria_scores)
            response = chat_model.invoke(analysis_prompt)
            
            if not isinstance(response.content, str):
                raise ValueError(f"LLM response.content is not a string: {type(response.content)}")
            content = response.content.strip()
            if not content:
                raise ValueError("LLM returned empty content")
            
            json_content = sanitize_json_string(content)
            try:
                result = json.loads(json_content)
            except json.JSONDecodeError as e:
                raise ValueError(f"LLM returned invalid JSON: {json_content[:100]}... Error: {str(e)}")
            
            filtered_result = {
                "OriginalUserStory": result.get("OriginalUserStory", {"Title": "", "Description": "", "AcceptanceCriteria": [], "AdditionalInformation": ""}),
                "ImprovedUserStory": result.get("ImprovedUserStory", {"Title": "", "Description": "", "AcceptanceCriteria": [], "AdditionalInformation": ""}),
                "Independent": result.get("Independent", {"score": criteria_scores["Independent"], "improved_score": 0, "explanation": "", "recommendation": ""}),
                "Negotiable": result.get("Negotiable", {"score": criteria_scores["Negotiable"], "improved_score": 0, "explanation": "", "recommendation": ""}),
                "Valuable": result.get("Valuable", {"score": criteria_scores["Valuable"], "improved_score": 0, "explanation": "", "recommendation": ""}),
                "Estimable": result.get("Estimable", {"score": criteria_scores["Estimable"], "improved_score": 0, "explanation": "", "recommendation": ""}),
                "Small": result.get("Small", {"score": criteria_scores["Small"], "improved_score": 0, "explanation": "", "recommendation": ""}),
                "Testable": result.get("Testable", {"score": criteria_scores["Testable"], "improved_score": 0, "explanation": "", "recommendation": ""}),
                "overall": result.get("overall", {"input_score": input_score, "improved_score": 0, "summary": "", "refinement_summary": ""})
            }
            
            for criterion in ["Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable"]:
                filtered_result[criterion]["score"] = criteria_scores[criterion]
                filtered_result[criterion]["improved_score"] = max(1, min(5, int(filtered_result[criterion].get("improved_score", 0))))
            
            calculated_improved_score = sum(filtered_result[c]["improved_score"] for c in ["Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable"])
            filtered_result["overall"]["input_score"] = max(0, min(30, int(input_score)))
            filtered_result["overall"]["improved_score"] = calculated_improved_score
            if filtered_result["overall"]["refinement_summary"]:
                filtered_result["overall"]["refinement_summary"] = re.sub(
                    r"INVEST Score improved from \d+/30 to \d+/30",
                    f"INVEST Score improved from {input_score}/30 to {calculated_improved_score}/30",
                    filtered_result["overall"]["refinement_summary"]
                )
            
            return filtered_result
            
        except Exception as e:
            return {
                "OriginalUserStory": {"Title": "", "Description": "", "AcceptanceCriteria": [], "AdditionalInformation": ""},
                "ImprovedUserStory": {"Title": "", "Description": "", "AcceptanceCriteria": [], "AdditionalInformation": ""},
                "Independent": {"score": criteria_scores["Independent"], "improved_score": 0, "explanation": "", "recommendation": ""},
                "Negotiable": {"score": criteria_scores["Negotiable"], "improved_score": 0, "explanation": "", "recommendation": ""},
                "Valuable": {"score": criteria_scores["Valuable"], "improved_score": 0, "explanation": "", "recommendation": ""},
                "Estimable": {"score": criteria_scores["Estimable"], "improved_score": 0, "explanation": "", "recommendation": ""},
                "Small": {"score": criteria_scores["Small"], "improved_score": 0, "explanation": "", "recommendation": ""},
                "Testable": {"score": criteria_scores["Testable"], "improved_score": 0, "explanation": "", "recommendation": ""},
                "overall": {"input_score": input_score, "improved_score": 0, "summary": f"Error in analysis: {str(e)}", "refinement_summary": ""}
            }

def extract_user_stories_from_input(input_json):
    """Extract all user stories from the input JSON."""
    try:
        data = input_json
        if not isinstance(data, list):
            data = [data]
            
        user_stories = []
        for item in data:
            if "input" not in item:
                continue
                
            user_story = item["input"]
            required_fields = ["title", "description", "acceptance_criteria", "additional_information"]
            if not all(field in user_story for field in required_fields):
                continue
                
            aspects_to_enhance = item.get("aspects_to_enhance", "")
            if not aspects_to_enhance and "evaluation" in item and "aspects_to_enhace" in item["evaluation"]:
                aspects_to_enhance = item["evaluation"].get("aspects_to_enhace", "")
            if not isinstance(aspects_to_enhance, str) or not aspects_to_enhance:
                aspects_to_enhance = "No specific aspects provided."
            
            additional_context = item.get("additional_context", "")
            if not additional_context and "evaluation" in item and "additional_context" in item["evaluation"]:
                additional_context = item["evaluation"].get("additional_context", "")
            if not isinstance(additional_context, str) or not additional_context:
                additional_context = "No additional context provided."

            input_score = 0
            if "evaluation" in item and "overall" in item["evaluation"] and "score" in item["evaluation"]["overall"]:
                input_score = item["evaluation"]["overall"]["score"]
                if not isinstance(input_score, (int, float)):
                    input_score = 0
                input_score = max(0, min(30, int(input_score)))

            evaluation = item.get("evaluation", {})
            criteria_scores = {}
            for criterion in ["Independent", "Negotiable", "Valuable", "Estimable", "Small", "Testable"]:
                score = evaluation.get(criterion, {}).get("score", 0)
                criteria_scores[criterion] = max(1, min(5, int(score)))
                
            user_stories.append({
                "user_story": user_story,
                "aspects_to_enhance": aspects_to_enhance,
                "additional_context": additional_context,
                "input_score": input_score,
                "criteria_scores": criteria_scores
            })
            
        return user_stories
        
    except Exception as e:
        raise ValueError(f"Error processing input: {str(e)}")

# FastAPI setup
app = FastAPI(title="User Story INVEST Analyzer API", description="API to analyze and improve user stories using INVEST criteria.")

# Pydantic model for input validation
class UserStoryInput(BaseModel):
    input: Dict[str, Any]  # The user story details (title, description, etc.)
    evaluation: Dict[str, Any] = {}  # Optional evaluation data (scores, aspects_to_enhance, etc.)
    aspects_to_enhance: str = ""
    additional_context: str = ""

@app.post("/analyze", response_model=List[Dict[str, Any]], summary="Analyze user stories")
async def analyze_user_stories(user_stories: List[UserStoryInput]):
    """
    Analyze a list of user stories using the INVEST criteria and return improved versions.
    
    - **Request Body**: A list of user story objects, each containing `input`, `evaluation`, `aspects_to_enhance`, and `additional_context`.
    - **Response**: A list of analysis results, each containing original and improved user stories, INVEST scores, and refinement summary.
    """
    try:
        # Convert Pydantic models to dict for processing
        input_data = [story.dict() for story in user_stories]
        
        # Extract user stories
        analyzer = UserStoryInvestAnalyzer()
        extracted_stories = extract_user_stories_from_input(input_data)
        
        if not extracted_stories:
            raise HTTPException(status_code=400, detail="No valid user stories found in the input.")
        
        # Process each user story
        results = []
        for story_data in extracted_stories:
            try:
                result = analyzer.analyze_user_story(
                    user_story=story_data["user_story"],
                    aspects_to_enhance=story_data["aspects_to_enhance"],
                    additional_context=story_data["additional_context"],
                    input_score=story_data["input_score"],
                    criteria_scores=story_data["criteria_scores"]
                )
                results.append(result)
            except Exception as e:
                results.append({
                    "error": f"Error processing user story: {str(e)}",
                    "OriginalUserStory": {"Title": "", "Description": "", "AcceptanceCriteria": [], "AdditionalInformation": ""},
                    "ImprovedUserStory": {"Title": "", "Description": "", "AcceptanceCriteria": [], "AdditionalInformation": ""},
                    "overall": {"input_score": story_data["input_score"], "improved_score": 0, "summary": f"Error: {str(e)}", "refinement_summary": ""}
                })
        
        return results
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

def run_fastapi():
    port = 8001
    max_port = 8010
    
    while port <= max_port:
        try:
            logger.info(f"Attempting to start FastAPI server on port {port}")
            uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
            break
        except OSError as e:
            if "address already in use" in str(e).lower() or "only one usage" in str(e).lower():
                logger.warning(f"Port {port} is already in use, trying port {port+1}")
                port += 1
            else:
                raise
    
    if port > max_port:
        logger.error(f"Could not find an available port between {8000} and {max_port}")
        raise RuntimeError("No available ports found")

# Function to run the MCP server for Claude Desktop
def run_mcp():
    logger.info("Starting MCP server for Claude Desktop integration")
    mcp.run()

# Main function to run both FastAPI and MCP concurrently
def main():
    # Start FastAPI in a separate thread
    fastapi_thread = threading.Thread(target=run_fastapi)
    fastapi_thread.daemon = True  # Daemonize so it stops when main thread exits
    fastapi_thread.start()
    logger.info("FastAPI server thread started")

    # Start MCP in the main thread (or could be another thread if preferred)
    run_mcp()

if __name__ == "__main__":
    main()