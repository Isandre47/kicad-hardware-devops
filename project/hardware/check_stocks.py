import csv
import json
import urllib.request
import os

def load_api_key():
    """Charge la clé API depuis le fichier credentials.json"""
    cred_path = '/tmp/work/hardware/credentials.json'
    if os.path.exists(cred_path):
        with open(cred_path, 'r') as f:
            data = json.load(f)
            return data.get("MOUSER_API_KEY")
    return None

def fetch_mouser_stock(mpn, api_key):
    """Interroge l'API officielle de Mouser de manière sécurisée"""
    if not api_key or api_key == "TON_AVANT_DERNIERE_CLE_ICI":
        return {"error": "Clé API manquante"}

    url = f"https://api.mouser.com/api/v1.0/search/partnumber?apiKey={api_key}"
    payload = {
        "SearchByPartRequest": {
            "mouserPartNumber": mpn,
            "partSearchOptions": "string"
        }
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=7) as response:
            result = json.loads(response.read().decode('utf-8'))

            # SÉCURITÉ : On vérifie chaque niveau du dictionnaire pas à pas
            if not result:
                return None

            search_results = result.get("SearchResults")
            if not search_results or not isinstance(search_results, dict):
                return None

            parts = search_results.get("Parts", [])
            if parts and len(parts) > 0 and isinstance(parts[0], dict):
                part = parts[0]

                # Récupération sécurisée du prix
                price_breaks = part.get("PriceBreaks", [])
                base_price = "N/A"
                if price_breaks and len(price_breaks) > 0 and isinstance(price_breaks[0], dict):
                    base_price = price_breaks[0].get("Price", "N/A")

                return {
                    "vendor": "Mouser",
                    "stock": part.get("AvailabilityInStock", "0"),
                    "price": base_price,
                    "lifecycle": part.get("LifecycleStatus", "Actif")
                }
    except Exception as e:
        return {"error": str(e)}
    return None

def generate_stock_page():
    csv_path = '/tmp/work/hardware/bom.csv'
    html_output = '/tmp/work/stocks.html'

    api_key = load_api_key()

    if not os.path.exists(csv_path):
        print("Erreur : Le fichier bom.csv n'existe pas.")
        return

    html_content = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Suivi des Stocks - Mouser API</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #1e1e2e; color: #cdd6f4; margin: 40px; }
            h1 { color: #89b4fa; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; background-color: #313244; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #45475a; }
            th { background-color: #45475a; color: #89b4fa; }
            .stock-ok { color: #a6e3a1; font-weight: bold; }
            .stock-none { color: #f38ba8; font-weight: bold; }
            .error-text { color: #f38ba8; font-style: italic; }
        </style>
    </head>
    <body>
        <h1>Tableau de Bord Supply Chain (Mouser API)</h1>
        <table>
            <tr>
                <th>Repère (Ref)</th>
                <th>Référence Fabricant (MPN)</th>
                <th>Disponibilité Mouser</th>
                <th>Prix Unitaire Base</th>
                <th>Statut Cycle de vie</th>
            </tr>
    """

    with open(csv_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                ref = row.get('References', row.get('Reference', ''))
                mpn = row.get('Part', row.get('Value', ''))

                # FILTRAGE INTELLIGENT : On ignore les descriptions ou valeurs trop génériques
                # qui vont à coup sûr faire échouer ou polluer l'interrogation Mouser
                mots_a_ignorer = ['yellow', 'green', 'red', 'conn_', 'pinheader', '350ma', '6pf', '100nf', '1uf', '10uf', 'mounting', 'logo', 'fiducial']
                if not mpn or any(mot in mpn.lower() for mot in mots_a_ignorer) or len(mpn) <= 3:
                    # Optionnel : décommenter la ligne suivante pour voir ce qui est sauté
                    # print(f"Composant générique ignoré : {mpn}")
                    continue

                print(f"Appel API Mouser pour : {mpn}...")
                info = fetch_mouser_stock(mpn, api_key)

                if not info:
                    html_content += f"<tr><td><b>{ref}</b></td><td>{mpn}</td><td colspan='3' class='error-text'>Non trouvé ou non distribué par Mouser</td></tr>"
                elif "error" in info:
                    html_content += f"<tr><td><b>{ref}</b></td><td>{mpn}</td><td colspan='3' class='error-text'>Erreur API: {info['error']}</td></tr>"
                else:
                    stock_val = info['stock']
                    stock_class = "stock-ok" if stock_val != "0" and ("In Stock" in str(stock_val) or (isinstance(stock_val, int) and stock_val > 0)) else "stock-none"

                    html_content += f"""
                    <tr>
                        <td><b>{ref}</b></td>
                        <td>{mpn}</td>
                        <td class="{stock_class}">{stock_val}</td>
                        <td>{info['price']}</td>
                        <td>{info['lifecycle']}</td>
                    </tr>
                    """

    with open(html_output, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("Page stocks.html mise à jour via Mouser API !")

if __name__ == "__main__":
    generate_stock_page()
