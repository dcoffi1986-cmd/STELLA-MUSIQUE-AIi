# STELLA MUSIC AI — reconnaissance OMR

## État réel
- PDF : import et aperçu fonctionnels.
- Détection de symboles : expérimentale, pas une transcription musicale fiable.
- **Audiveris** : adaptateur et endpoint `POST /api/recognize-musicxml` intégrés au code, **moteur non installé sur Render**.
- Synthèse chantée SATB : non disponible.

## Installation Audiveris
Installer une version officielle d'Audiveris sur un serveur disposant de Java, des bibliothèques système et de mémoire suffisante. Définir `AUDIVERIS_BIN` vers l'exécutable Audiveris. Vérifier `GET /api/status` avant de tester la conversion PDF → MXL.

L'adaptateur lance `audiveris -batch -export -output <dossier> -- <partition.pdf>` avec une limite de 150 secondes, des fichiers temporaires et une limite mémoire Java. L'interface mobile actuelle ne déclenche pas encore cet endpoint. Une architecture à traitement asynchrone et à quotas sera nécessaire pour un service public.

L'offre Render Free actuelle ne garantit pas les ressources nécessaires à Audiveris. Ne pas changer d'offre ni installer de serveur payant sans accord explicite.

## Qualité et droits
Audiveris peut se tromper ; valider la transcription avant toute utilisation pédagogique. Audiveris est sous licence AGPL-3.0 : vérifier les obligations applicables au service web. Ne pas publier ni conserver des partitions protégées sans droits.
