import csv
import json
import urllib.request
import os
from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)

# Même fonction sécurisée que précédemment pour charger la clé
def load_api_key():
    cred_path = '/app/data/credentials.json'
    if os.path.exists(cred_path):
        with open(cred_path, 'r') as f:
            return json.load(f).get("MOUSER_API_KEY")
    return None

def search_mouser(keyword, api_key):
    """Recherche par mot-clé ou référence (renvoie jusqu'à 5 résultats)"""
    if not api_key:
        return {"error": "Clé API manquante"}

    url = f"https://api.mouser.com/api/v1.0/search/keyword?apiKey={api_key}"
    payload = {
        "SearchByKeywordRequest": {
            "keyword": keyword,
            "records": 5,
            "startingRecord": 0,
            "searchOptions": "string",
            "searchWithWarner": "true"
        }
    }
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
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
                    "stock": part.get("AvailabilityInStock", "0"),
                    "price": price,
                    "lifecycle": part.get("LifecycleStatus") or "Actif"
                })
            return propositions
    except Exception as e:
        return {"error": str(e)}

@app.route('/api/bom')
def get_bom():
    """Lit le CSV généré par KiBot et renvoie les lignes sous forme de JSON"""
    csv_path = '/app/data/bom.csv'
    if not os.path.exists(csv_path):
        return jsonify({"error": "bom.csv introuvable"}), 404

    bom_data = []
    with open(csv_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            ref = row.get('References', row.get('Reference', ''))
            value = row.get('Part', row.get('Value', ''))
            if ref and value:
                bom_data.append({"ref": ref, "value": value})
    return jsonify(bom_data)

@app.route('/api/search')
def api_search():
    """Endpoint appelé en AJAX par le navigateur pour chercher un composant"""
    keyword = request.args.get('q', '')
    api_key = load_api_key()
    results = search_mouser(keyword, api_key)
    return jsonify(results)

@app.route('/')
def index():
    """La page HTML unique avec le JavaScript interactif corrigé pour l'Unicode"""
    html_template = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Sourcing Interactif - Mouser</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; background-color: #1e1e2e; color: #cdd6f4; margin: 40px; }
            h1 { color: #89b4fa; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; background-color: #313244; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #45475a; }
            th { background-color: #45475a; color: #89b4fa; }
            select { background-color: #45475a; color: #cdd6f4; border: 1px solid #89b4fa; padding: 5px; border-radius: 4px; width: 100%; }
            .btn-search { background-color: #89b4fa; color: #11111b; border: none; padding: 6px 12px; cursor: pointer; border-radius: 4px; font-weight: bold; }
            .stock-ok { color: #a6e3a1; font-weight: bold; }
            .stock-none { color: #f38ba8; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>Aide à la Décision - Sourcing Composants</h1>
        <table>
            <thead>
                <tr>
                    <th style="width: 10%;">Repère</th>
                    <th style="width: 15%;">Valeur KiCad</th>
                    <th style="width: 45%;">Recherche Mouser / Sélection</th>
                    <th style="width: 10%;">Fabricant</th>
                    <th style="width: 10%;">Stock</th>
                    <th style="width: 10%;">Prix Base</th>
                </tr>
            </thead>
            <tbody id="bom-table-body">
                <tr><td colspan="6">Chargement de la BOM...</td></tr>
            </tbody>
        </table>

        <script>
            // Registre global pour stocker les résultats de recherche de chaque ligne sans bug d'encodage
            window.mouserResultsRegistry = {};

            // 1. Charger la BOM au démarrage
            fetch('/api/bom')
                .then(res => res.json())
                .then(data => {
                    const tbody = document.getElementById('bom-table-body');
                    tbody.innerHTML = '';

                    data.forEach((item, index) => {
                        tbody.innerHTML += `
                            <tr id="row-${index}">
                                <td><b>${item.ref}</b></td>
                                <td>${item.value}</td>
                                <td id="search-cell-${index}">
                                    <input type="text" id="input-${index}" value="${item.value}" style="background:#1e1e2e; color:#fff; border:1px solid #45475a; padding:5px; border-radius:4px; width: 70%;">
                                    <button class="btn-search" onclick="LancerRecherche(${index})">🔍</button>
                                </td>
                                <td id="mfr-${index}">-</td>
                                <td id="stock-${index}">-</td>
                                <td id="price-${index}">-</td>
                            </tr>
                        `;
                    });
                });

            // 2. Fonction pour chercher et peupler le menu déroulant
            function LancerRecherche(index) {
                const query = document.getElementById(`input-${index}`).value;
                const tdSelection = document.getElementById(`search-cell-${index}`);

                tdSelection.innerHTML = "<i>Recherche en cours...</i>";

                fetch(`/api/search?q=${encodeURIComponent(query)}`)
                    .then(res => res.json())
                    .then(propositions => {
                        if (propositions.error || !propositions || propositions.length === 0) {
                            tdSelection.innerHTML = `
                                <input type="text" id="input-${index}" value="${query}" style="background:#1e1e2e; color:#fff; border:1px solid #45475a; padding:5px; border-radius:4px; width: 70%;">
                                <button class="btn-search" onclick="LancerRecherche(${index})">🔍</button>
                                <br><span style='color:#f38ba8; font-size:9pt;'>Aucun résultat chez Mouser</span>
                            `;
                            return;
                        }

                        // On sauvegarde les propositions dans notre registre global pour cette ligne précise
                        window.mouserResultsRegistry[index] = propositions;

                        // On crée un menu déroulant HTML propre
                        let selectHtml = `<select id="select-${index}" onchange="MettreAJourLigne(${index})">`;
                        selectHtml += `<option value="">-- Choisir une alternative (${propositions.length}) --</option>`;

                        propositions.forEach((prop, pIdx) => {
                            selectHtml += `<option value="${pIdx}">${prop.mpn} [${prop.manufacturer}] (${prop.stock} pcs)</option>`;
                        });
                        selectHtml += `</select>`;

                        tdSelection.innerHTML = selectHtml;
                    })
                    .catch(err => {
                        tdSelection.innerHTML = "<span style='color:#f38ba8;'>Erreur de connexion</span>";
                    });
            }

            // 3. Mettre à jour les cases quand l'utilisateur choisit un composant
            function MettreAJourLigne(index) {
                const selectEl = document.getElementById(`select-${index}`);
                const chosenIdx = selectEl.value;
                if (chosenIdx === "") return;

                // Récupération directe depuis le registre global (Zéro bug d'encodage/Unicode)
                const comp = window.mouserResultsRegistry[index][chosenIdx];

                document.getElementById(`mfr-${index}`).innerText = comp.manufacturer;
                document.getElementById(`stock-${index}`).innerText = comp.stock;

                // Gestion dynamique de la couleur du stock
                if (comp.stock && comp.stock !== "0" && !comp.stock.includes("Aucun")) {
                    document.getElementById(`stock-${index}`).className = "stock-ok";
                } else {
                    document.getElementById(`stock-${index}`).className = "stock-none";
                }

                document.getElementById(`price-${index}`).innerText = comp.price;
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
