from dotenv import load_dotenv
load_dotenv()  # <--- This loads the key from the .env file

import os
from pydantic_ai import Agent
from schemas import GDPRAlert

# Requires OPENAI_API_KEY in environment variables
journalist = Agent(
    'openai:gpt-4o-mini',
    result_type=GDPRAlert,
    system_prompt="You are a Regulatory Risk Analyst. Extract structured data."
)

async def analyze_ruling(raw_text: str) -> GDPRAlert:
    result = await journalist.run(f"Analyze: {raw_text}")
    return result.data
