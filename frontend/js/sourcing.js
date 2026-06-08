const BACKEND_URL = "http://localhost:5000";
window.mouserResultsRegistry = {};
window.bomQuantities = {};
window.lineTotals = {};

// On récupère les paramètres passés dans l'URL (project_id et name)
const urlParams = new URLSearchParams(window.location.search);
const projectId = urlParams.get('project_id');
const projectName = urlParams.get('name');

// Détermination de la bonne route d'API
// Si on a un projectId, on interroge la nouvelle route (qu'on va lister juste après), sinon la BDD par défaut
const bomEndpoint = projectId ? `${BACKEND_URL}/api/projects/${projectId}/bom` : `${BACKEND_URL}/api/bom`;

console.log("Chargement de la BOM via l'endpoint :", bomEndpoint);

// Charger la BOM au démarrage depuis FastAPI
fetch(bomEndpoint)
    .then(res => res.json())
    .then(data => {
      const tbody = document.getElementById('bom-table-body');
      tbody.innerHTML = '';

      if (data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="color:#f9e2af;">Aucun composant trouvé.</td></tr>`;
        return;
      }

      data.forEach((item, index) => {
        // On sauvegarde la quantité pour les calculs futurs
        window.bomQuantities[index] = item.qty || 1;
        window.lineTotals[index] = 0;

        tbody.innerHTML += `
                <tr id="row-${index}">
                    <td><b>${item.ref}</b></td>
                    <td>${item.value}</td>
                    <td style="color: #f9e2af; text-align: center;"><b>${item.qty || 1}</b></td>
                    <td id="search-cell-${index}">
                        <input type="text" id="input-${index}" value="${item.value}">
                        <button class="btn-search" onclick="LancerRecherche(${index})">🔍</button>
                    </td>
                    <td id="mfr-${index}">-</td>
                    <td id="stock-${index}">-</td>
                    <td id="price-${index}" style="text-align: right;">0.00 €</td>
                    <td id="total-${index}" style="text-align: right; color: #a6e3a1; font-weight: bold;">0.00 €</td>
                </tr>
            `;
      });
    });

// Chercher les alternatives chez Mouser via l'API Backend
function LancerRecherche(index) {
  const query = document.getElementById(`input-${index}`).value;
  const tdSelection = document.getElementById('search-cell-' + index);

  tdSelection.innerHTML = `
    <div class="spinner-sm"></div> 
    <span style="font-size: 10pt; color: #89b4fa; margin-left: 8px;">Interrogation des distributeurs...</span>
  `;

  fetch(`${BACKEND_URL}/api/search?q=${encodeURIComponent(query)}`)
      .then(res => res.json())
      .then(propositions => {
        if (propositions.error || !propositions || propositions.length === 0) {
          tdSelection.innerHTML = `
                    <input type="text" id="input-${index}" value="${query}">
                    <button class="btn-search" onclick="LancerRecherche(${index})">🔍</button>
                `;
          return;
        }

        window.mouserResultsRegistry[index] = propositions;

        let selectHtml = `<select id="select-${index}" onchange="MettreAJourLigne(${index})">`;
        selectHtml += `<option value="">-- Choisir une alternative (${propositions.length}) --</option>`;

        propositions.forEach((prop, pIdx) => {
          const providerBadge = prop.provider ? `via ${prop.provider.toUpperCase()}` : '';
          selectHtml += `<option value="${pIdx}">${prop.mpn} [${prop.manufacturer}] (${prop.stock} pcs) - ${prop.price} - ${providerBadge}</option>`;
        });
        selectHtml += `</select>`;
        tdSelection.innerHTML = selectHtml;
      });
}

// Mettre à jour l'affichage de la ligne
function MettreAJourLigne(index) {
  const selectEl = document.getElementById(`select-${index}`);
  const chosenIdx = selectEl.value;
  if (chosenIdx === "") return;

  const comp = window.mouserResultsRegistry[index][chosenIdx];

  // Affichage du Fabricant et du Stock
  document.getElementById(`mfr-${index}`).innerText = comp.manufacturer;
  document.getElementById(`stock-${index}`).innerText = comp.stock;

  // Extraction du prix unitaire (on nettoie la chaîne pour n'avoir que le chiffre)
  // Ex: "0.286 €" ou "1.35 €" -> 0.286 ou 1.35
  let unitPrice = 0;
  if (comp.price && comp.price !== "N/A") {
    const cleanedPrice = comp.price.replace(/[^\d.,]/g, '').replace(',', '.');
    unitPrice = parseFloat(cleanedPrice) || 0;
  }

  const qty = window.bomQuantities[index];
  const lineTotal = unitPrice * qty;

  // Sauvegarde du total de la ligne
  window.lineTotals[index] = lineTotal;

  // Affichage dans le tableau
  document.getElementById(`price-${index}`).innerText = `${unitPrice.toFixed(3)} €`;
  document.getElementById(`total-${index}`).innerText = `${lineTotal.toFixed(2)} €`;

  // Calcul du montant global de la carte
  CalculerMontantGlobal();
}

function CalculerMontantGlobal() {
  let globalTotal = 0;
  Object.keys(window.lineTotals).forEach(key => {
    globalTotal += window.lineTotals[key];
  });
  document.getElementById('global-total').innerText = `${globalTotal.toFixed(2)} €`;
}
