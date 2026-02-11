from dotenv import load_dotenv
load_dotenv()  # <--- This loads the key from the .env file

from pydantic_ai import Agent
from schemas import GDPRAlert
import os

# 1. Define the Agent using Type Hints in brackets [GDPRAlert, None]
# The [GDPRAlert] here tells the Agent exactly what schema to use for the output
journalist: Agent[None, GDPRAlert] = Agent('openai:gpt-4o-mini')

# 2. Use a decorator for the system prompt (it's cleaner and more robust)
@journalist.system_prompt
def add_system_prompt():
    return "You are a Regulatory Risk Analyst. Extract structured data from GDPR rulings."

# 3. Your analysis function
async def analyze_ruling(ruling_text: str):
    # This calls the agent to process the text
    result = await journalist.run(ruling_text)
    return result.output
