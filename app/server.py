from fastmcp import FastMCP
from agent import analyze_ruling
from feed import fetch_latest_ruling

mcp = FastMCP("GDPR Vault")

@mcp.tool()
async def get_high_risk_alerts() -> str:
    """Returns structured JSON of high-risk GDPR violations."""
    raw = await fetch_latest_ruling()
    data = await analyze_ruling(raw)
    if data.severity_score >= 8:
        return data.model_dump_json()
    return "No critical risks."
if __name__ == "__main__":
    import os
    # Railway provides a PORT environment variable automatically
    port = int(os.getenv("PORT", 8000)) 
    mcp.run(transport="http", host="0.0.0.0", port=port)
