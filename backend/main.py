import os
import json
import csv
import shutil
import subprocess
from pathlib import Path
from fastapi import FastAPI, Query, Depends, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import models
from database import engine, get_db
from services.sourcing import global_search

# Création automatique des tables SQLite au démarrage (Socle BDD)
models.Base.metadata.create_all(bind=engine)

# Dossier où seront stockés les projets de CAO uploadés
UPLOAD_DIR = Path("/app/data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Initialisation de FastAPI
app = FastAPI(title="KiCad Hardware DevOps API")

# Configuration des CORS pour le Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_api_key():
    """Charge la clé API Mouser depuis le fichier partagé"""
    cred_path = '/app/data/hardware/credentials.json'
    if os.path.exists(cred_path):
        with open(cred_path, 'r') as f:
            return json.load(f).get("MOUSER_API_KEY")
    return None

# --- ROUTES API ---
@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API de Sourcing Hardware !"}

@app.get("/api/bom")
def get_bom():
    """Lit la BOM de démo actuelle (pour compatibilité)"""
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
    """Route d'agrégation multi-fournisseurs (Mouser + Farnell)"""
    api_key_mouser = load_api_key()
    propositions = global_search(q, api_key_mouser)
    return propositions

@app.post("/api/upload")
async def upload_kicad_project(file: UploadFile = File(...), db: Session = Depends(get_db)):
    print(f"[KIBOT] Upload")

    """Route d'upload dynamique avec génération automatique de la BOM via KiBot"""
    ext = Path(file.filename).suffix.lower()
    if ext not in [".kicad_pcb", ".brd"]:
        raise HTTPException(status_code=400, detail="Extension non supportée (.kicad_pcb ou .brd uniquement)")

    project_name = Path(file.filename).stem
    project_dir = UPLOAD_DIR / project_name
    project_dir.mkdir(parents=True, exist_ok=True)

    file_path = project_dir / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Enregistrement en BDD
    nuevo_proyecto = models.Project(filename=file.filename)
    db.add(nuevo_proyecto)
    db.commit()
    db.refresh(nuevo_proyecto)

    # Création du schéma virtuel vide exigé par KiBot dans le dossier du projet
    schema_virtuel = project_dir / f"{project_name}.kicad_sch"
    with open(schema_virtuel, "w") as f:
        f.write("(kicad_sch (version 20231120) (generator kibot)\n)")

    # EXÉCUTION DE KIBOT (La magie DevOps Hardware)
    # On utilise ton fichier de configuration config.kibot.yaml global
    config_path = "/app/data/hardware/config.kibot.yaml"

    try:
        print(f"[KIBOT] Lancement de l'extraction pour {file.filename}...")

        # On définit explicitement le nom du fichier HTML attendu par le frontend
        output_html_path = project_dir / f"{project_name}-ibom.html"

        command = [
            "kibot",
            "-c", config_path,
            "-b", str(file_path),
            "-e", str(schema_virtuel),
            "-d", str(project_dir)
        ]

        # On remet temporairement check=True pour voir l'erreur exacte dans les logs si ça rate !
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print("[KIBOT] Exécution terminée avec succès !")

    except subprocess.CalledProcessError as e:
        print(f"[KIBOT] CRASH DE LA GÉNÉRATION : {e.stderr}")
        raise HTTPException(status_code=500, detail=f"KiBot a échoué : {e.stderr}")
    except Exception as e:
        print(f"[KIBOT] Erreur générale : {e}")
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "status": "success",
        "message": "Fichier reçu et traité par KiBot !",
        "project_id": nuevo_proyecto.id,
        "filename": file.filename
    }

@app.get("/api/projects/{project_id}/bom")
def get_project_bom(project_id: int, db: Session = Depends(get_db)):
    """Lit dynamiquement la vraie BOM CSV du projet générée par KiBot"""

    # On va chercher le projet en Base de Données pour connaître le nom du fichier d'origine
    projet = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not projet:
        raise HTTPException(status_code=404, detail="Projet introuvable en base de données")

    # On reconstruit le chemin vers le dossier de cet upload spécifique
    project_name = Path(projet.filename).stem
    project_dir = UPLOAD_DIR / project_name

    # KiBot nomme généralement le fichier de sortie selon le schéma/pcb, ou selon ta config.
    # Pour être totalement flexible, on va chercher le premier fichier .csv présent dans le dossier du projet
    csv_files = list(project_dir.glob("*.csv"))

    if not csv_files:
        # Si KiBot n'a pas encore fini ou si le CSV n'a pas été généré, on renvoie une liste vide
        return []

    csv_path = csv_files[0]
    bom_data = []

    # Lecture du vrai CSV généré pour CE projet
    try:
        with open(csv_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            print(f"[DEBUG CSV] Colonnes détectées par Python : {reader.fieldnames}")

            for row in reader:
                # Gestion des variantes de colonnes KiCAd 8 / KiBot
                ref = row.get('References', row.get('Reference', row.get('Designator', '')))
                value = row.get('Value', row.get('Part', row.get('Comment', '')))

                qty_keys = ['Quantity Per PCB', 'Quantity', 'Qty', 'Quantity V', 'Qnty', 'Count', 'Quantité']
                qty = '1' # Valeur par défaut

                for key in qty_keys:
                    if key in row and row[key]:
                        qty = row[key]
                        break

                if ref and value:
                    bom_data.append({
                        "ref": ref,
                        "value": value,
                        "qty": int(qty) if str(qty).strip().isdigit() else 1 # Sécurité conversion
                    })

        print(f"[API] Vraie BOM chargée pour le projet {project_id} ({len(bom_data)} composants trouvés)")
        return bom_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la lecture de la BOM : {str(e)}")
