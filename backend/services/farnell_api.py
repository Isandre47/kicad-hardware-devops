import urllib.request
import json
import os

def fetch_farnell_stock(mpn: str):
    """Interroge l'API officielle de Farnell (Element14) avec le bon parsing JSON"""
    cred_path = '/app/data/hardware/credentials.json'
    api_key = None
    if os.path.exists(cred_path):
        with open(cred_path, 'r') as f:
            api_key = json.load(f).get("FARNELL_API_KEY")

    if not api_key or api_key == "TA_CLE_FARNELL":
        return []

    # URL de recherche REST officielle
    url = f"https://api.element14.com/catalog/products?versionNumber=1.4&term=manuPartNum:{mpn}&storeInfo.id=fr.farnell.com&resultsSettings.offset=0&resultsSettings.numberOfResults=1&resultsSettings.refinements.filters=rohsCompliant%2CinStock&resultsSettings.responseGroup=large&callInfo.omitXmlSchema=false&callInfo.responseDataFormat=json&callinfo.apiKey={api_key}"

    try:
        req = urllib.request.Request(
            url,
            headers={'Accept': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read().decode('utf-8'))

            # On gère les deux types de retours possibles de l'API Farnell
            search_return = result.get("manufacturerPartNumberSearchReturn") or result.get("keywordSearchResult") or {}
            products = search_return.get("products", [])

            propositions = []
            for prod in products:
                # Extraction du prix de la première tranche (Ex: 1-49 pièces)
                prices = prod.get("prices", [])
                price_str = "N/A"
                if prices and isinstance(prices, list):
                    first_tier = prices[0]
                    price_str = f"{first_tier.get('cost', 'N/A')} €"

                # Extraction directe du stock (clé 'inv' d'après ton JSON)
                stock_val = prod.get("inv", "0")

                propositions.append({
                    "mpn": prod.get("translatedManufacturerPartNumber", mpn),
                    "manufacturer": prod.get("vendorName", "Inconnu"),
                    "description": prod.get("displayName", "Composant Farnell"),
                    "stock": str(stock_val),
                    "price": price_str,
                    "lifecycle": "Disponible",
                    "provider": "Farnell"
                })
            return propositions
    except Exception as e:
        print(f"Erreur API Farnell pour {mpn}: {e}")
        return []
