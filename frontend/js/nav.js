document.addEventListener("DOMContentLoaded", function() {
  // On récupère le projet en cours dans l'URL s'il existe
  const urlParams = new URLSearchParams(window.location.search);
  const projectId = urlParams.get('project_id');
  const projectName = urlParams.get('name');

  // Maintien des paramètres pour les onglets
  const queryParams = projectId ? `?project_id=${projectId}&name=${encodeURIComponent(projectName)}` : '';

  // Création de la barre de navigation HTML
  const navHTML = `
        <div style="background-color: #23232f; padding: 10px 20px; display: flex; align-items: center; justify-content: space-between; border-bottom: 2px solid #313244; font-family: 'Segoe UI', sans-serif;">
            <div style="display: flex; align-items: center; gap: 15px;">
                <span style="color: #89b4fa; font-weight: bold; font-size: 13pt;">⚡ Hardware DevOps</span>
                <span style="color: #6c7086; font-size: 11pt;">|</span>
                <span style="color: #a6adc8; font-size: 10pt; font-style: italic;">${projectName ? `Projet : ${projectName}` : 'Aucun projet chargé'}</span>
            </div>
            <div style="display: flex; gap: 10px;">
                <a href="/upload.html" style="color: #cdd6f4; text-decoration: none; padding: 6px 12px; border-radius: 4px; font-size: 10pt; font-weight: bold; background-color: #45475a;">📁 Importer</a>
                <a href="/index.html${queryParams}" id="nav-visuel" style="color: #11111b; text-decoration: none; padding: 6px 12px; border-radius: 4px; font-size: 10pt; font-weight: bold; background-color: #89b4fa; ${!projectId ? 'opacity: 0.5; pointer-events: none;' : ''}">👁️ Visuel Carte</a>
                <a href="/sourcing.html${queryParams}" id="nav-sourcing" style="color: #11111b; text-decoration: none; padding: 6px 12px; border-radius: 4px; font-size: 10pt; font-weight: bold; background-color: #a6e3a1; ${!projectId ? 'opacity: 0.5; pointer-events: none;' : ''}">📊 Sourcing Multi</a>
            </div>
        </div>
    `;

  // Injection automatique au tout début du <body> de la page
  document.body.insertAdjacentHTML('afterbegin', navHTML);

  // Mettre en valeur l'onglet actif selon la page
  const currentPage = window.location.pathname;
  if (currentPage === "/" || currentPage === "/index.html") {
    document.getElementById("nav-visuel").style.outline = "2px solid #fff";
  } else if (currentPage === "/sourcing.html") {
    document.getElementById("nav-sourcing").style.outline = "2px solid #fff";
  }

  // Style CSS du spinner injecté dynamiquement
  const style = document.createElement('style');
  style.innerHTML = `
    .spinner {
        border: 4px solid rgba(255, 255, 255, 0.1);
        width: 36px;
        height: 36px;
        border-radius: 50%;
        border-left-color: #a6e3a1;
        animation: spin 1s linear infinite;
        display: inline-block;
        vertical-align: middle;
        margin-right: 10px;
    }
    .spinner-sm {
        border: 2px solid rgba(255, 255, 255, 0.1);
        width: 16px;
        height: 16px;
        border-left-color: #89b4fa;
        animation: spin 0.8s linear infinite;
        display: inline-block;
        vertical-align: middle;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
  `;
  document.head.appendChild(style);

});
