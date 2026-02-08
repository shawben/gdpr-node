from pydantic import BaseModel, Field
from typing import Literal

class GDPRAlert(BaseModel):
    company_name: str = Field(description="The legal entity fined.")
    fine_amount_euro: float = Field(description="The fine amount in Euros.")
    violation_summary: str = Field(description="One-sentence summary.")
    severity_score: int = Field(description="Risk score 1-10.")
    sector: Literal["Tech", "Finance", "Retail", "Healthcare", "Other"]
    is_publicly_traded: bool = Field(description="True if public.")
