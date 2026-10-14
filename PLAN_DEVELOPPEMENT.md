# STELLA MUSIC AI — Plan de réalisation

## Objectif
Plateforme musicale pour chorales, choristes, chefs de chœur, musiciens et compositeurs. Site web mobile d'abord, application Android ensuite.

## État réel
- GitHub Pages : prototype HTML publié.
- Navigation et écrans de démonstration : disponibles.
- Formulaire d'inscription / connexion : code préparé, inactif tant que Supabase n'est pas configuré.
- Comptes utilisateurs, messagerie, stockage musical et génération IA : non opérationnels.

## Étape 1 — Fondations
- Dépôt GitHub, versionnement, hébergement GitHub Pages.
- Séparer progressivement HTML, CSS, JavaScript et configuration.
- Prévoir environnement de test avant changements majeurs.

## Étape 2 — Authentification
- Créer ou choisir le projet Supabase.
- Récupérer l'URL et la clé publique anon/publishable (jamais service_role).
- Configurer Auth, URL du site et redirections autorisées.
- Choisir explicitement la politique de confirmation e-mail.
- Activer inscription, connexion, déconnexion, réinitialisation du mot de passe.
- Tester création et reconnexion sur téléphone.

## Étape 3 — Profils
- Table profiles liée à auth.users.
- Champs : identifiant, nom affiché, instrument/pupitre, avatar, date de création.
- Règles RLS pour limiter les modifications au propriétaire.

## Étape 4 — Chorales
- Tables choirs, choir_members, invitations.
- Rôles administrateur, chef de chœur, membre.
- Vérification des droits côté base de données.

## Étape 5 — Bibliothèque
- Tables songs, scores, recordings.
- Stockage privé des fichiers, contrôle des droits et respect des droits d'auteur.
- Recherche par titre, langue, compositeur et catégorie.

## Étape 6 — Répétitions
- Événements, calendrier, présence, notifications et programmes.

## Étape 7 — Discussions
- Canaux par chorale, messages et pièces jointes.
- Modération, blocage et politique de conservation.

## Étape 8 — Studio IA
- Commencer par aide aux paroles et exercices musicaux.
- Passer par un backend sécurisé pour les clés privées des fournisseurs d'IA.
- Prévoir coûts, quotas, consentement et droits musicaux.

## Étape 9 — Sécurité et qualité
- RLS, sauvegardes, journalisation, tests mobiles et contrôle d'accès.
- Politique de confidentialité et suppression de compte.

## Étape 10 — Lancement
- Bêta privée, retours des chorales, correction des anomalies.
- PWA puis Android si les besoins sont confirmés.
- Monétisation uniquement après validation des usages.

## Première action nécessaire
Identifier le projet Supabase à utiliser. Seules l'URL du projet et la clé publique publishable/anon doivent être utilisées dans le site. Ne jamais publier de clé secrète, jeton personnel ou mot de passe.

## Critères de réussite de la première version utilisable
1. Un membre peut s'inscrire et se connecter.
2. Il peut modifier son profil.
3. Un responsable peut créer une chorale.
4. Il peut inviter un membre et lui donner un rôle.
5. Les données privées ne sont accessibles qu'aux membres autorisés.
