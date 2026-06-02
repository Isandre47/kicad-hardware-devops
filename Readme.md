Petit projet pour améliorer le choix des composants électronique par fournisseur.

L'idée est de partie d'un schéma électronique dont on a la liste des composants, ( via Kicad pour le moment ) puis on va récupérer les informations chez divers fournisseurs de composants pour afficher le résultat directement sur un site web.

Cela permettra, entre autres choses, d'économiser du temps à chercher sur chaque site la disponibilité, les prix etc..

Le souhait est de tout centraliser et automatiser les tâches chronophages.

A moyen terme, il est envisagé de pouvoir déposer son listing et d'avoir un retour rapide sur les disponibilités etc.., d'avoir un historique etc.


Le projet est sous docker, pour l'utiliser il faudra donc utiliser `docker compose up -d`.

Pour le moment, fonctionne avec Mouser, il faut obtenir auprès d'eux une clé API qu'il faudra renseigner dans le fichier credentials.json dans le dossier project/hardware.

L'accès au schéma http://localhost:8081/ et le résultat des stocks http://localhost:8080/
