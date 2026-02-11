from dotenv import load_dotenv
load_dotenv()

from pydantic_ai import Agent, RunContext
from schemas import GDPRAlert

# 1. Instantiate the Agent SIMPLY (No complex arguments here)
journalist = Agent('openai:gpt-4o-mini')

# 2. Add System Prompt via Decorator (The robust way)
@journalist.system_prompt
def add_system_prompt(ctx: RunContext[None]):
    return (
        "You are a Regulatory Risk Analyst. Extract structured data from GDPR rulings. "
        "Always return the result as a structured object matching the schema."
    )

# 3. Analysis Function
async def analyze_ruling(ruling_text: str):
    # 👇 FORCE THE RESULT TYPE HERE (Runtime enforcement)
    result = await journalist.run(ruling_text, result_type=GDPRAlert)
    
    # Return the data.
    # Note: If the agent was forced to return a type, the result object 
    # will put that structured data into .data
    return result.data