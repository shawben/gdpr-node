import os
import httpx
from fastapi import FastAPI, Request, Response, HTTPException
from web3 import Web3

# CONFIGURATION
# We get these from Environment Variables (set in Railway later)
RPC_URL = os.getenv("RPC_URL") 
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
VAULT_URL = os.getenv("VAULT_URL") # Internal URL of the other service
PRICE_ETH = 0.001

app = FastAPI()
w3 = Web3(Web3.HTTPProvider(RPC_URL))

def verify_payment(tx_hash, sender):
    try:
        tx = w3.eth.get_transaction(tx_hash)
        # 1. Check if it went to our contract
        if tx['to'].lower() != CONTRACT_ADDRESS.lower():
            return False
        # 2. Check value
        if w3.from_wei(tx['value'], 'ether') < PRICE_ETH:
            return False
        # 3. Check sender
        if tx['from'].lower() != sender.lower():
            return False
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

@app.get("/sse")
async def proxy_sse(request: Request):
    tx_hash = request.headers.get("X-Payment-Tx")
    wallet = request.headers.get("X-Wallet-Address")

    # If no payment header, return 402 + Instructions
    if not tx_hash or not wallet:
        return Response(
            status_code=402,
            content=f'{{"error": "Payment Required", "contract": "{CONTRACT_ADDRESS}", "price": "{PRICE_ETH}"}}',
            media_type="application/json"
        )

    # Verify Payment on Blockchain
    if verify_payment(tx_hash, wallet):
        # PROXY REQUEST TO PRIVATE VAULT
        async with httpx.AsyncClient() as client:
            try:
                # We connect to the internal vault service
                async with client.stream("GET", f"{VAULT_URL}/sse") as response:
                    # Stream the response back to the user
                    return Response(
                        content=response.aiter_bytes(),
                        media_type="text/event-stream"
                    )
            except Exception as e:
                return Response(status_code=500, content=f"Vault Error: {str(e)}")
    else:
        return Response(status_code=403, content="Invalid Payment Proof")
