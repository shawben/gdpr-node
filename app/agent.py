from dotenv import load_dotenv
load_dotenv()

from pydantic_ai import Agent, RunContext
from schemas import GDPRAlert

# 1. Define the Agent with explicit return type [None, GDPRAlert]
# This tells the LLM: "You MUST return a GDPRAlert object, nothing else."
journalist: Agent[None, GDPRAlert] = Agent(
    'openai:gpt-4o-mini',
    result_type=GDPRAlert,  # <--- FORCE THE RETURN TYPE HERE
    system_prompt="You are a Regulatory Risk Analyst. Extract structured data from GDPR rulings. Always return the result as a structured object, never as plain text."
)

# 2. Your analysis function
async def analyze_ruling(ruling_text: str):
    # Run the agent
    result = await journalist.run(ruling_text)
    
    # Return the structured data (The object itself)
    return result.data  # In newer versions this might be .data or .output depending on exact version, but let's stick to the object.