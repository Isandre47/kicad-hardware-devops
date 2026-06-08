import urllib.request
import json

def fetch_mouser_stock(keyword: str, api_key: str):
    """Interroge l'API officielle de Mouser par mot-clé ou référence"""
    if not api_key:
        return {"error": "Clé API Mouser manquante"}

    url = f"https://api.mouser.com/api/v1.0/search/keyword?apiKey={api_key}"
    payload = {
        "SearchByKeywordRequest": {
            "keyword": keyword, "records": 5, "startingRecord": 0,
            "searchOptions": "string", "searchWithWarner": "true"
        }
    }
    try:
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}, method='POST'
        )
        with urllib.request.urlopen(req, timeout=7) as response:
            result = json.loads(response.read().decode('utf-8'))
            parts = result.get("SearchResults", {}).get("Parts", [])
            propositions = []
            for part in parts:
                price_breaks = part.get("PriceBreaks", [])
                price = price_breaks[0].get("Price", "N/A") if price_breaks else "N/A"
                propositions.append({
                    "mpn": part.get("ManufacturerPartNumber", "Inconnu"),
                    "manufacturer": part.get("Manufacturer", "Inconnu"),
                    "description": part.get("Description", "Pas de description"),
                    "stock": str(part.get("AvailabilityInStock", "0")),
                    "price": price,
                    "lifecycle": part.get("LifecycleStatus") or "Actif"
                })
            return propositions
    except Exception as e:
        return {"error": str(e)}
