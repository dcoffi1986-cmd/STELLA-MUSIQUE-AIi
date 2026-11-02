# STELLA OMR (Audiveris)
Service distinct de l'application chorale, pour éviter de bloquer son démarrage.

Docker build context: racine du dépôt (.).
Dockerfile: omr/Dockerfile.
Endpoint GET /health : présence du binaire.
Endpoint POST /recognize : multipart field file (PDF), header X-OMR-Token.
Définir OMR_TOKEN (secret aléatoire) sur le service OMR. Ne pas publier ce secret dans GitHub.
Le serveur principal pourra appeler ce service via OMR_SERVICE_URL et OMR_TOKEN, configurés côté serveur uniquement.
Le moteur nécessite des ressources Java; les limites Render Free peuvent empêcher la transcription.
Audiveris est distribué sous licence AGPL-3.0; examiner les obligations avant distribution commerciale.
