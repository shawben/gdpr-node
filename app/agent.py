from dotenv import load_dotenv
load_dotenv()  # <--- This loads the key from the .env file

from pydantic_ai import Agent
from schemas import GDPRAlert

# The [GDPRAlert] part tells the agent what to return
journalist = Agent('openai:gpt-4o-mini', deps_type=None, result_type=GDPRAlert)

# Then add the system prompt separately if the constructor is being picky
@journalist.system_prompt
def get_system_prompt():
    return "You are a Regulatory Risk Analyst. Extract structured data.")

async def analyze_ruling(raw_text: str) -> GDPRAlert:
    result = await journalist.run(f"Analyze: {raw_text}")
    return result.data
