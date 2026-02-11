import json
import re
from dotenv import load_dotenv
load_dotenv()

from pydantic_ai import Agent, RunContext
from schemas import GDPRAlert

# 1. Instantiate the Agent SIMPLY (No result_type args)
journalist = Agent('openai:gpt-4o-mini')

# 2. Add System Prompt via Decorator
# We EXPLICITLY ask for JSON output here.
@journalist.system_prompt
def add_system_prompt(ctx: RunContext[None]):
    return (
        "You are a Regulatory Risk Analyst. Extract structured data from GDPR rulings. "
        "You MUST return the result as a raw JSON object matching this structure: "
        f"{json.dumps(GDPRAlert.model_json_schema(), indent=2)} "
        "Do not include markdown formatting (like ```json), just the raw JSON string."
    )

# 3. Helper to clean up the response (remove markdown if AI adds it)
def clean_json_string(s: str) -> str:
    # Remove ```json ... ``` wrappers if present
    s = re.sub(r'^```json\s*', '', s, flags=re.MULTILINE)
    s = re.sub(r'^```\s*', '', s, flags=re.MULTILINE)
    s = re.sub(r'\s*```$', '', s, flags=re.MULTILINE)
    return s.strip()

# 4. Analysis Function
async def analyze_ruling(ruling_text: str):
    # Run the agent simply
    result = await journalist.run(ruling_text)
    
    # We use .data or .output (depending on version), but we treat it as a string
    # We try to get the string content safely
    raw_content = getattr(result, 'data', None)
    if not raw_content:
        raw_content = getattr(result, 'output', None) # Fallback for other versions
        
    if not isinstance(raw_content, str):
        # If it returned an object, convert to string or use as is
        raw_content = str(raw_content)

    # Clean and Parse
    try:
        clean_text = clean_json_string(raw_content)
        # Convert JSON string -> GDPRAlert Object
        structured_data = GDPRAlert.model_validate_json(clean_text)
        return structured_data
    except Exception as e:
        # Fallback if parsing fails (returns a dummy error object so server doesn't crash)
        print(f"JSON Parsing Failed: {e}. Raw content: {raw_content}")
        return GDPRAlert(
            company_name="Parse Error",
            fine_amount_euro=0.0,
            violation_summary=f"Could not parse AI response: {str(e)}",
            severity_score=0,
            sector="Other",
            is_publicly_traded=False
        )