import os
import sys   # <--- THIS LINE IS CRITICAL (and was missing or too low)
import asyncio
import json
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import StreamingResponse
from web3 import Web3

# ---------------------------------------------------------
# 👇 THE FIX: Force Python to look in the 'app' folder
# ---------------------------------------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
# ---------------------------------------------------------

# NOW these imports will work
from feed import fetch_latest_ruling
from agent import analyze_ruling

# CONFIGURATION
RPC_URL = os.getenv("RPC_URL", "https://mainnet.base.org") 
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
PRICE_ETH = 0.001

app = FastAPI()
w3 = Web3(Web3.HTTPProvider(RPC_URL))

def verify_payment(tx_hash, sender):
    """
    Verifies that the transaction:
    1. Went to our contract
    2. Had the correct amount
    3. Was sent by the person asking for data
    """
    try:
        tx = w3.eth.get_transaction(tx_hash)
        
        # 1. Check Recipient (Case Insensitive)
        if tx['to'].lower() != CONTRACT_ADDRESS.lower():
            print(f"❌ Wrong Recipient: {tx['to']}")
            return False
            
        # 2. Check Value (Compare in WEI to avoid decimal errors)
        required_wei = w3.to_wei(PRICE_ETH, 'ether')
        if tx['value'] < required_wei:
            print(f"❌ Insufficient Funds! Sent: {tx['value']}, Needed: {required_wei}")
            return False
            
        # 3. Check Sender (The "Identity" Check)
        if tx['from'].lower() != sender.lower():
            print(f"❌ Identity Mismatch: Tx from {tx['from']}, Claim from {sender}")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Verify Error: {e}")
        return False

# --- THE AI GENERATOR ---
async def event_generator():
    """
    1. Scrapes the latest GDPR ruling
    2. Feeds it to the OpenAI Agent
    3. Streams the result line-by-line
    """
    yield "data: 🔍 Scanning Enforcement Tracker...\n\n"
    
    # 1. Get Data
    try:
        raw_text = await fetch_latest_ruling()
        yield "data: ✅ New Ruling Found! Analyzing risks...\n\n"
    except Exception as e:
        yield f"data: ❌ Error scraping data: {str(e)}\n\n"
        return

    # 2. Run Agent
    try:
        # Run analysis
        analysis = await analyze_ruling(raw_text)

        # --- FAIL-SAFE: Check if it's a Dictionary, Object, or String ---
        
        # Case A: It's a Pydantic Model (Object)
        if hasattr(analysis, 'company_name'):
            company = analysis.company_name
            fine = analysis.fine_amount_euro
            score = analysis.severity_score
            summary = analysis.violation_summary
            
        # Case B: It's a Dictionary (JSON)
        elif isinstance(analysis, dict):
            company = analysis.get('company_name', 'Unknown')
            fine = analysis.get('fine_amount_euro', 0)
            score = analysis.get('severity_score', 0)
            summary = analysis.get('violation_summary', 'No summary')

        # Case C: It's just a String (The Error you saw)
        else:
            yield f"data: ⚠️ Agent returned text instead of data:\n\n"
            yield f"data: {str(analysis)}\n\n"
            return

        # Output the formatted stream
        yield f"data: --------------------------------\n\n"
        yield f"data: 🚨 HIGH RISK ALERT DETECTED 🚨\n\n"
        yield f"data: 🏢 Company: {company}\n\n"
        yield f"data: 💶 Fine: €{fine:,.2f}\n\n"
        yield f"data: ⚖️ Severity: {score}/10\n\n"
        yield f"data: 📝 Summary: {summary}\n\n"
        yield f"data: --------------------------------\n\n"
        
    except Exception as e:
        yield f"data: ❌ Agent Error: {str(e)}\n\n"

@app.get("/sse")
async def sse_endpoint(request: Request):
    tx_hash = request.headers.get("X-Payment-Tx")
    wallet = request.headers.get("X-Wallet-Address")

    # 1. Validate Headers
    if not tx_hash or not wallet:
        return Response(
            status_code=402,
            content=json.dumps({
                "error": "Payment Required",
                "contract": CONTRACT_ADDRESS,
                "price": PRICE_ETH
            }),
            media_type="application/json"
        )

    # 2. Verify Payment
    if verify_payment(tx_hash, wallet):
        print(f"✅ Access Granted for {wallet}")
        # Return the AI Stream directly
        return StreamingResponse(event_generator(), media_type="text/event-stream")
    else:
        return Response(status_code=403, content="Invalid Payment Proof")
