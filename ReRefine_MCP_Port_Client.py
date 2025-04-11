from mcp import ClientSession
from mcp.client.sse import sse_client
import asyncio

async def test():
    async with sse_client(url="http://127.0.0.1:5000/sse") as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("Tools:", tools.tools)
            result = await session.call_tool("invest_analyze", arguments={
                "user_story": {
                        "UserStory": {
                            "Title": "User Registration",
                            "Description": "As a new user, I want to create an account using my email and password, So that I can access personalized features of the application.",
                            "AcceptanceCriteria": [
                            "User should be able to enter their email and password.",
                            "System should validate the email format.",
                            "Password should be at least 8 characters long.",
                            "If registration is successful, the user should receive a confirmation email.",
                            "If the email is already registered, the system should show an appropriate error message."
                            ],
                            "AdditionalInformation": "not found"
                        },
                        "Independent": {
                            "score": 5,
                            "explanation": "The story is self-contained, has no inherent dependencies on other stories, and can be developed and delivered separately. It also avoids 'this and that' formulations that combine multiple features.",
                            "recommendation": "No changes needed, as the story meets all the criteria for independence."
                        },
                        "Negotiable": {
                            "score": 4,
                            "explanation": "The story leaves room for conversation and refinement, but it could be improved by avoiding prescriptive language. However, the story does not contain overly prescriptive implementation details.",
                            "recommendation": "Rephrase the story to focus on the desired outcome rather than the specific implementation, allowing for more flexibility in the development process."
                        },
                        "Valuable": {
                            "score": 5,
                            "explanation": "The story clearly describes a benefit to the customer, explains why the feature is needed, and delivers value to stakeholders. A real user or customer would care about this story.",
                            "recommendation": "No changes needed, as the story meets all the criteria for value."
                        },
                        "Estimable": {
                            "score": 3,
                            "explanation": "The story lacks sufficient detail for estimation, as it does not provide enough information about the implementation or the scope of the work. However, it does not contain unknowns that prevent reasonable estimation.",
                            "recommendation": "Add more details about the implementation, such as the email content, triggers, and any integrations required, to enable the team to estimate the effort required."
                        },
                        "Small": {
                            "score": 4,
                            "explanation": "The story is focused on a single capability or feature and can be completed by a single developer in a few days. However, it's unclear if it can be completed in a single sprint without more information about the scope and dependencies.",
                            "recommendation": "Break down the story into smaller tasks or sub-stories to ensure it can be completed in a single sprint and to provide more clarity on the scope and dependencies."
                        },
                        "Testable": {
                            "score": 1,
                            "explanation": "The story lacks clear acceptance criteria, making it difficult to verify success objectively. It's also unclear if automated tests can be written for the story.",
                            "recommendation": "Add clear acceptance criteria that define what 'done' looks like, including specific examples of successful email confirmations and any error scenarios that need to be handled."
                        },
                        "overall": {
                            "score": 22,
                            "summary": "Current INVEST Score: 22/30 (Fair). The story has some strengths, particularly in terms of independence and value, but it needs improvement in terms of estimability, testability, and negotiability.",
                            "key_recommendations": [
                            "Add clear acceptance criteria to make the story testable",
                            "Provide more details about the implementation to make the story estimable",
                            "Break down the story into smaller tasks or sub-stories to ensure it can be completed in a single sprint"
                            ]
                        },
                        "aspects_to_enhance": "Need to improve Testable score",
                        "additional_context": ""
                        }
            })
            print("Result:", result.content[0].json)

asyncio.run(test())