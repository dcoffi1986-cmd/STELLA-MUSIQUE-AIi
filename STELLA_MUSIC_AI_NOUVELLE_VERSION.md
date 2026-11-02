# STELLA MUSIC AI — nouvelle version

Objectif : importer une partition PDF/image/MusicXML, reconnaître les notes, distinguer les quatre parties SATB, puis produire des voix chantées avec paroles.

État : préparation du déploiement. Les voix humaines chantées ne sont pas encore implémentées. La reconnaissance PDF nécessite un moteur OMR (par exemple Audiveris) et des vérifications de précision. Ne pas présenter cette version comme prête à l'emploi.

Sauvegarde de l'ancien projet : branche `archive-ancienne-version-2026-11-02`.
Branche de développement : `stella-music-ai-v2`.

Étapes : intégrer le code du prototype, vérifier les dépendances et la sécurité, tester l'importation, configurer l'hébergement, intégrer et tester le moteur de chant, puis remplacer `main` après validation.