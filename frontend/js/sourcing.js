const BACKEND_URL = "http://localhost:5000";
window.mouserResultsRegistry = {};

// 1. Charger la BOM au démarrage depuis FastAPI
fetch(`${BACKEND_URL}/api/bom`)
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
                        <input type="text" id="input-${index}" value="${item.value}">
                        <button class="btn-search" onclick="LancerRecherche(${index})">🔍</button>
                    </td>
                    <td id="mfr-${index}">-</td>
                    <td id="stock-${index}">-</td>
                    <td id="price-${index}">-</td>
                </tr>
            `;
      });
    })
    .catch(err => {
      document.getElementById('bom-table-body').innerHTML = `<tr><td colspan="6" style="color:#f38ba8;">Erreur lors du chargement de l'API Backend. Vérifiez que FastAPI est démarré.</td></tr>`;
    });

// 2. Chercher les alternatives chez Mouser via l'API Backend
function LancerRecherche(index) {
  const query = document.getElementById(`input-${index}`).value;
  const tdSelection = document.getElementById(`search-cell-${index}`);

  tdSelection.innerHTML = "<i>Recherche en cours via FastAPI...</i>";

  fetch(`${BACKEND_URL}/api/search?q=${encodeURIComponent(query)}`)
      .then(res => res.json())
      .then(propositions => {
        if (propositions.error || !propositions || propositions.length === 0) {
          tdSelection.innerHTML = `
                    <input type="text" id="input-${index}" value="${query}">
                    <button class="btn-search" onclick="LancerRecherche(${index})">🔍</button>
                    <br><span style='color:#f38ba8; font-size:9pt;'>Aucun résultat chez Mouser</span>
                `;
          return;
        }

        window.mouserResultsRegistry[index] = propositions;

        let selectHtml = `<select id="select-${index}" onchange="MettreAJourLigne(${index})">`;
        selectHtml += `<option value="">-- Choisir une alternative (${propositions.length}) --</option>`;

        propositions.forEach((prop, pIdx) => {
          selectHtml += `<option value="${pIdx}">${prop.mpn} [${prop.manufacturer}] (${prop.stock} pcs)</option>`;
        });
        selectHtml += `</select>`;

        tdSelection.innerHTML = selectHtml;
      })
      .catch(err => {
        tdSelection.innerHTML = "<span style='color:#f38ba8;'>Erreur de communication avec l'API</span>";
      });
}

// 3. Mettre à jour l'affichage de la ligne
function MettreAJourLigne(index) {
  const selectEl = document.getElementById(`select-${index}`);
  const chosenIdx = selectEl.value;
  if (chosenIdx === "") return;

  const comp = window.mouserResultsRegistry[index][chosenIdx];

  document.getElementById(`mfr-${index}`).innerText = comp.manufacturer;
  document.getElementById(`stock-${index}`).innerText = comp.stock;

  if (comp.stock && comp.stock !== "0" && !comp.stock.includes("Aucun")) {
    document.getElementById(`stock-${index}`).className = "stock-ok";
  } else {
    document.getElementById(`stock-${index}`).className = "stock-none";
  }

  document.getElementById(`price-${index}`).innerText = comp.price;
}
