import urllib.request
import json
import os
import csv # Ajouté ici pour nettoyer la route /api/bom plus bas

from fastapi import FastAPI, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import models
from database import engine, get_db

# Création automatique des tables SQLite au démarrage
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="KiCad Hardware DevOps API")

# Crucial pour que ton Frontend Vuetify (qui tournera sur un autre port)
# puisse interroger ce Backend sans blocage de sécurité (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En développement, on autorise tout
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API de Sourcing Hardware !"}

@app.get("/api/historique")
def get_historique(db: Session = Depends(get_db)):
    """Exemple de route qui interroge la base de données via l'ORM"""
    projets = db.query(models.Project).order_by(models.Project.uploaded_at.desc()).all()
    return projets

def load_api_key():
    cred_path = '/app/data/hardware/credentials.json'
    if os.path.exists(cred_path):
        with open(cred_path, 'r') as f:
            return json.load(f).get("MOUSER_API_KEY")
    return None

def search_mouser(keyword, api_key):
    if not api_key:
        return {"error": "Clé API manquante"}
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
                    "stock": part.get("AvailabilityInStock", "0"),
                    "price": price,
                    "lifecycle": part.get("LifecycleStatus") or "Actif"
                })
            return propositions
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/bom")
def get_bom():
    import csv
    csv_path = '/app/data/hardware/bom.csv'
    if not os.path.exists(csv_path):
        return []
    bom_data = []
    with open(csv_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            ref = row.get('References', row.get('Reference', ''))
            value = row.get('Value', row.get('Part', ''))
            if ref and value:
                bom_data.append({"ref": ref, "value": value})
    return bom_data

@app.get("/api/search")
def api_search(q: str = Query("")):
    api_key = load_api_key()
    return search_mouser(q, api_key)
