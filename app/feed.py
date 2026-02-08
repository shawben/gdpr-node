import httpx
from bs4 import BeautifulSoup
import logging

# Configure logging to see what's happening in production
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

URL = "https://www.enforcementtracker.com"

async def fetch_latest_ruling() -> str:
    """
    Production scraper for GDPR Enforcement Tracker.
    Fetches the latest fine from the main table.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
            logger.info(f"Connecting to {URL}...")
            response = await client.get(URL, headers=headers)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")
            
            # The data is usually in a table with id="filterTable" or similar classes
            # We look for the first row (tr) in the table body (tbody)
            table = soup.find("table", {"id": "filterTable"})
            if not table:
                # Fallback: Try finding any table if the ID changed
                table = soup.find("table")
            
            if not table:
                logger.warning("Structure changed: No table found. Using fallback data.")
                return _get_fallback_data()

            # Get the first row of data (skipping headers)
            rows = table.find_all("tr")
            
            # Usually row 0 is header, row 1 is data. 
            # We iterate to find the first meaningful data row.
            latest_entry = None
            for row in rows[1:]:
                cols = row.find_all("td")
                if len(cols) > 4: # Ensure it has enough columns (Country, Fine, etc.)
                    # Extract text from columns
                    # Col 2: Date, Col 3: Fine, Col 4: Controller, Col 6: Reason
                    country = cols[0].get_text(strip=True)
                    fine = cols[2].get_text(strip=True)
                    company = cols[3].get_text(strip=True)
                    reason = cols[5].get_text(strip=True) if len(cols) > 5 else "Unknown"
                    
                    latest_entry = f"""
                    NEW ENFORCEMENT DETECTED:
                    Country: {country}
                    Company: {company}
                    Fine Amount: {fine}
                    Reason: {reason}
                    Source: GDPR Enforcement Tracker
                    """
                    break
            
            if latest_entry:
                logger.info("Successfully scraped latest ruling.")
                return latest_entry
            else:
                logger.warning("Table found but no rows parsable. Using fallback.")
                return _get_fallback_data()

    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        return _get_fallback_data()

def _get_fallback_data() -> str:
    """
    Returns real historical data if the live scraper is blocked.
    This ensures your node always returns *something* valid.
    """
    return """
    FALLBACK DATA (Live Scrape Failed):
    Decision: 2024-X (Historical)
    Entity: Meta Platforms Ireland Limited
    Fine: €1,200,000,000
    Violation: Transfer of data to the US without adequate safeguards (Art. 46 GDPR).
    Authority: Data Protection Commission (Ireland)
    """
