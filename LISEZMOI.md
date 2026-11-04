# Radar Emploi Nature — application Android, iPhone et web

Une page web installable sur le téléphone, sans serveur ni abonnement, sur le même principe que l'app « Expositions ». Elle s'ouvre sans passer par l'app Claude.

- **Les offres :** chaque matin, un robot GitHub lit la base Notion et publie la liste ; l'application la lit à chaque ouverture et garde la dernière pour le hors connexion.
- **Vos actions** (favoris, candidatures, offres retirées ou ajoutées, sources) s'appliquent tout de suite sur le téléphone. Un second robot GitHub les recopie ensuite dans Notion, en une minute environ. Les envois sont chiffrés : rien de lisible n'apparaît sur GitHub.
- **Les écrans** sont ceux de la dernière version du Radar (l'artifact claude.ai) : Offres, Favoris, Candidatés, Mes expériences, Sources de recherche.
- **L'indice de compatibilité** (6 critères) est calculé sur l'appareil à partir de votre CV.
- **Claude, sans abonnement :** pour l'adaptation du CV, la structure de lettre, « Mes expériences », la lecture d'une annonce et l'indice affiné, la page prépare la demande (prompt d'origine, CV et offre). Vous la collez dans Claude (compte gratuit possible), puis vous recollez la réponse, que la page affiche.

Le Radar complet dans claude.ai (https://claude.ai/artifact/AmPQXbCaAC5B7onCMoAVHF) fonctionne toujours, sur les mêmes données Notion.

## 1. Installer l'application (2 minutes)

- **iPhone :** dans **Safari**, ouvrez https://vincentlg751.github.io/radar-emploi-nature/. Touchez **Partager**, puis **Sur l'écran d'accueil**, puis **Ajouter**.
- **Android :** dans **Chrome**, ouvrez la même adresse. Touchez **⋮**, puis **Installer l'application**.
- **Android, application native (facultatif) :** dans l'onglet **Actions** du dépôt, ouvrez **Application mobile (Android et iOS)**, puis le dernier passage avec une coche verte. Téléchargez **RadarEmploi-android**, dézippez-le et ouvrez `RadarEmploi.apk`.

Dans Notion, l'intégration « Radar Emploi Nature » doit être connectée aux deux bases (**•••**, puis **Connexions**) : « Veille offres emploi écologie » et « Sources de recherche ».

## 2. Activer la synchronisation avec Notion (10 minutes, une seule fois)

Tant qu'elle n'est pas activée, vos actions restent en attente sur le téléphone ; elles partiront toutes au moment de l'activation.

**a. Créer la clé de chiffrement (dans l'application)**
1. Dans l'application, touchez **Activer la synchro Notion** (en haut).
2. Touchez **Générer une clé**, puis **Copier la clé**. Gardez la fenêtre ouverte.

**b. Enregistrer cette clé dans GitHub**
1. Ouvrez https://github.com/vincentlg751/radar-emploi-nature/settings/secrets/actions et cliquez sur **New repository secret**.
2. **Name :** `RADAR_SYNC_KEY`. **Secret :** collez la clé. Cliquez sur **Add secret**.

**c. Créer la clé GitHub personnelle**
1. Ouvrez https://github.com/settings/personal-access-tokens/new
2. **Token name :** `Radar Emploi`. **Expiration :** 1 an (GitHub vous préviendra avant la fin).
3. **Repository access :** choisissez **Only select repositories**, puis **radar-emploi-nature**.
4. **Permissions :** cliquez sur **Add permissions**, choisissez **Actions**, puis réglez-la sur **Read and write**. N'ajoutez rien d'autre.
5. Cliquez sur **Generate token**, puis copiez la clé affichée (elle commence par `github_pat_`).

**d. Terminer dans l'application**
1. Collez la clé GitHub dans **Clé GitHub personnelle**.
2. Touchez **Enregistrer et tester**. Le bouton du haut affiche **Notion synchronisé**.

Sur un deuxième appareil, refaites seulement l'étape d avec la même clé de chiffrement (copiez-la depuis le premier appareil) : ne régénérez pas de clé, sinon il faudrait aussi changer le secret GitHub.

## Bon à savoir

- **Mise à jour de la liste :** le robot **Radar Emploi Nature** la publie chaque jour à 7h15 (heure de Paris en hiver), après la veille Claude de 5h40. Si GitHub demande une validation (**Review deployments**), allez dans **Settings**, puis **Environments**, puis **github-pages**, décochez **Required reviewers** et cliquez sur **Save protection rules**.
- **Synchronisation à sens unique :** vos actions partent vers Notion, mais les favoris et candidatures notés ailleurs (dans claude.ai ou sur un autre appareil) n'apparaissent pas dans l'application, car les statuts ne sont jamais publiés.
- **Offre ajoutée par lien :** elle part dans Notion avec la case « À compléter » ; l'agent du matin la complète, et elle remplace alors la version ajoutée sur le téléphone.
- **État de la synchro :** le bouton en haut indique « Notion synchronisé », le nombre d'actions en attente ou une erreur (clé GitHub expirée par exemple : refaites l'étape 2.c).
- **Ce qui est publié :** la liste des offres est publique (comme le site). Le statut des offres, les dates de candidature et les offres « Écarté » ne sont jamais publiés.

## Sécurité

- **Clés :** la clé Notion ne sert qu'aux robots GitHub (secret chiffré). La clé GitHub personnelle et la clé de chiffrement restent sur votre téléphone ; la clé GitHub ne peut que lancer les robots de ce dépôt.
- **Envois chiffrés :** chaque action est chiffrée (AES-256-GCM) avant de partir vers GitHub et déchiffrée par le robot avec le secret `RADAR_SYNC_KEY`. Le journal du robot n'affiche que des nombres.
- **Garde-fous du robot :** seules les deux bases du Radar sont modifiables, chaque page visée est relue et vérifiée, et seules certaines propriétés et valeurs sont acceptées (`scripts/notion_action.py`, testé par `tests/test_notion_action.py`).
- **Page :** aucun texte d'offre n'est inséré comme du HTML, et seuls les liens `http(s)` sont gardés. La politique de sécurité (CSP) n'autorise que le script de la page, identifié par son empreinte (`scripts/csp.py`), la liste publiée et l'API GitHub. Les lecteurs PDF / DOCX sont servis avec l'application, sans CDN. La page refuse de s'afficher dans le cadre d'un autre site.
- **Android :** inspection à distance désactivée ; données de l'app exclues des sauvegardes et des transferts (`mobile/harden_android.py`). L'APK est une version de test, signée avec une clé de développement.
- **Robots GitHub :** actions épinglées par empreinte (mises à jour par Dependabot), secrets fournis à une seule étape, aucun droit d'écriture sur le dépôt.

## Fichiers

| Fichier | Rôle |
|---|---|
| `radar-template.html` | L'application (portée de l'artifact claude.ai) |
| `scripts/build.py` | Lit Notion et produit le site publié : application et `offres.json` |
| `scripts/csp.py` | Politique de sécurité de la page |
| `radar-app/` | Manifeste, mode hors connexion, icônes et lecteurs PDF / DOCX |
| `mobile/` | Projet Android / iPhone (Capacitor) |
| `.github/workflows/radar.yml` | Robot du matin : lit Notion et publie sur GitHub Pages |
| `.github/workflows/notion-action.yml`, `scripts/notion_action.py` | Robot de synchronisation : recopie vos actions dans Notion |
| `.github/workflows/mobile.yml` | Compile l'APK Android et vérifie le projet iOS |

---

# Expos du moment

L'application des expositions a déménagé dans son propre dépôt, [Expos-du-moment/Expositions](https://github.com/Expos-du-moment/Expositions), publiée à l'adresse https://expos-du-moment.github.io/Expositions/. Elle est ainsi totalement séparée du Radar emploi : autre adresse, autres données de navigateur.

L'ancienne adresse `…/radar-emploi-nature/expositions/` renvoie automatiquement vers la nouvelle (`scripts/expositions_redirect.py`).
