from .mouser_api import fetch_mouser_stock
from .farnell_api import fetch_farnell_stock

def global_search(keyword: str, mouser_key: str):
    results = []

    # Recherche chez Mouser
    try:
        mouser_results = fetch_mouser_stock(keyword, mouser_key)
        # on vérifie que Mouser a bien renvoyé une liste valide de composants
        if isinstance(mouser_results, list):
            print(f"[SOURCING] Mouser a renvoyé {len(mouser_results)} résultats pour '{keyword}'")
            for r in mouser_results:
                r["provider"] = "Mouser"
                results.append(r)
        elif isinstance(mouser_results, dict) and "error" in mouser_results:
            print(f"Alerte Mouser récupérée dans sourcing : {mouser_results['error']}")
    except Exception as e:
        print(f"Erreur critique lors de l'appel Mouser : {e}")

    # Recherche chez Farnell
    try:
        farnell_results = fetch_farnell_stock(keyword)
        if isinstance(farnell_results, list):
            print(f"[SOURCING] Farnell a renvoyé {len(farnell_results)} résultats pour '{keyword}'")
            for r in farnell_results:
                # farnell_api met déjà le tag provider, mais on s'assure qu'il est là
                r["provider"] = "Farnell"
                results.append(r)
    except Exception as e:
        print(f"Erreur critique lors de l'appel Farnell : {e}")

    return results
