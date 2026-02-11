import os
import asyncio
import json
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import StreamingResponse
from web3 import Web3

# --- IMPORT YOUR AI AGENT ---
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
            
        # 2. Check Value
        if w3.from_wei(tx['value'], 'ether') < PRICE_ETH:
            print(f"❌ Insufficient Funds: {tx['value']}")
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
        # The agent returns a structured object (GDPRAlert)
        analysis = await analyze_ruling(raw_text)
        
        # Convert to a pretty string for the stream
        yield f"data: --------------------------------\n\n"
        yield f"data: 🚨 HIGH RISK ALERT DETECTED 🚨\n\n"
        yield f"data: 🏢 Company: {analysis.company_name}\n\n"
        yield f"data: 💶 Fine: €{analysis.fine_amount_euro:,.2f}\n\n"
        yield f"data: ⚖️ Severity: {analysis.severity_score}/10\n\n"
        yield f"data: 📝 Summary: {analysis.violation_summary}\n\n"
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