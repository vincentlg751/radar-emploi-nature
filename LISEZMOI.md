# Radar Emploi Nature — application Android, iPhone et web

L'application reprend la dernière version du Radar (l'artifact claude.ai du 31 octobre 2026) : mêmes onglets, mêmes fonctions et mêmes prompts Claude.

- **Offres, Favoris, Candidatés :** étoile pour mettre en favori, date de candidature, suppression en deux temps (corbeille Notion).
- **Indice de compatibilité** sur 6 critères : compétences, expérience, formation, équilibre de vie selon le lieu, secteur, outils.
- **Adaptation du CV** à une offre et **structure de lettre de motivation** pour les favoris et les candidatures.
- **Mes expériences :** une conversation avec Claude pour enregistrer ce qui n'est pas sur le CV.
- **Sources de recherche** de l'agent du matin, et **ajout d'une offre par lien** (avec lecture de l'annonce par Claude).
- Filtres par région, contrat, langue (offres en anglais), niveau, domaine, date et indice.

Tout reste synchronisé avec Notion : une offre mise en favori sur le téléphone l'est aussi dans la base et dans l'artifact claude.ai.

## Comment ça marche

```
Téléphone / navigateur  ──mot de passe──▶  Serveur personnel (Cloudflare)  ──▶  Notion (vos 2 bases)
     (l'application)                        garde les clés Notion et Claude  ──▶  Claude (API Anthropic)
```

- **L'application** (`radar-template.html`) ne contient ni clé ni donnée. Elle est publiée sur GitHub Pages et emballée en app Android / iPhone (`mobile/`).
- **Le serveur personnel** (`server/`) garde la clé Notion et la clé API Claude. Il n'accepte que votre mot de passe et ne peut lire et modifier que les deux bases du Radar : « Veille offres emploi écologie » et « Sources de recherche ». Il tourne gratuitement sur Cloudflare Workers.
- **Le CV et les fiches « Mes expériences »** restent sur l'appareil. Ils ne partent vers Claude, via le serveur, que lorsque vous lancez une analyse.

## Mise en place (environ 20 minutes, une seule fois)

### 1. Notion : connecter l'intégration aux deux bases

L'intégration « Radar Emploi Nature » et le secret GitHub `NOTION_TOKEN` existent déjà. Vérifiez seulement qu'elle a accès aux **deux** bases :

1. Ouvrez la base **« Veille offres emploi écologie »**. Cliquez sur **•••** en haut à droite, puis **Connexions**, et vérifiez que **Radar Emploi Nature** y figure.
2. Faites de même pour la base **« Sources de recherche »**.
3. Sur https://www.notion.so/profile/integrations, ouvrez l'intégration, puis l'onglet **Capacités**. Cochez **Lire**, **Mettre à jour** et **Insérer du contenu**, puis enregistrez.

### 2. Claude : créer une clé API

1. Sur https://console.anthropic.com, ouvrez **API Keys**, puis cliquez sur **Create Key**. Nommez-la « Radar Emploi » et copiez-la (elle commence par `sk-ant-`).
2. Dans **Limits**, fixez un plafond de dépense mensuel, par exemple 10 €. Les analyses sont facturées à l'usage, quelques centimes chacune.

### 3. Cloudflare : créer le compte et une clé d'accès

1. Créez un compte gratuit sur https://dash.cloudflare.com/sign-up.
2. Dans le tableau de bord, ouvrez **Workers & Pages** une première fois et choisissez votre sous-domaine `workers.dev` (par exemple `vincent-lg`).
3. Copiez votre **Account ID** : il s'affiche à droite de la page **Workers & Pages** (ou dans l'adresse de la page, juste après `dash.cloudflare.com/`).
4. Ouvrez https://dash.cloudflare.com/profile/api-tokens, puis cliquez sur **Create Token**. Choisissez le modèle **Edit Cloudflare Workers**, puis **Continue to summary** et **Create Token**. Copiez la clé.

### 4. GitHub : donner les secrets au robot

Ouvrez https://github.com/vincentlg751/radar-emploi-nature/settings/secrets/actions. Pour chaque ligne, cliquez sur **New repository secret** :

| Name | Secret |
|---|---|
| `CLOUDFLARE_API_TOKEN` | la clé Cloudflare (étape 3.4) |
| `CLOUDFLARE_ACCOUNT_ID` | l'Account ID (étape 3.3) |
| `ANTHROPIC_API_KEY` | la clé Claude (étape 2.1) |
| `APP_PASSWORD` | le mot de passe de l'application : **16 caractères minimum**, inventé pour l'occasion (par exemple 4 mots au hasard) |

`NOTION_TOKEN` est déjà en place.

### 5. Mettre le serveur en ligne

1. Ouvrez l'onglet **Actions**, cliquez sur **Serveur Radar Emploi (Cloudflare)**, puis sur **Run workflow**.
2. À la fin du passage, l'adresse du serveur s'affiche dans l'étape « Mettre le serveur en ligne », sous la forme `https://radar-emploi.VOTRE-SOUS-DOMAINE.workers.dev`.
3. Facultatif : pour ne pas avoir à taper cette adresse sur chaque appareil, enregistrez-la dans **Settings**, puis **Secrets and variables**, puis **Actions**, onglet **Variables**, avec **New repository variable** : nom `RADAR_SERVER`, valeur l'adresse du serveur. Relancez ensuite les robots **Radar Emploi Nature** et **Application mobile**.

### 6. Installer l'application

- **iPhone et Android, depuis le navigateur (immédiat) :** ouvrez https://vincentlg751.github.io/radar-emploi-nature/. Sur iPhone, dans Safari, touchez **Partager**, puis **Sur l'écran d'accueil**. Sur Android, dans Chrome, touchez **⋮**, puis **Installer l'application**.
- **Android, application native :** dans **Actions**, puis **Application mobile (Android et iOS)**, téléchargez l'artefact **RadarEmploi-android** du dernier passage, dézippez-le et ouvrez `RadarEmploi.apk` sur le téléphone.
- **iPhone, application native :** Apple impose un Mac et un compte développeur. Téléchargez l'artefact **RadarEmploi-ios-xcode**, ou sur un Mac lancez `cd mobile && npm install && npm run ios && npx cap open ios`. Dans Xcode, choisissez votre équipe (**Signing & Capabilities**), branchez l'iPhone, puis cliquez sur **▶**.

Au premier lancement, saisissez l'adresse du serveur et le mot de passe. Laissez « Rester connecté sur cet appareil » coché sur votre téléphone personnel ; décochez-le sur un ordinateur partagé.

## Au quotidien

- L'agent Claude de 5h40 continue d'alimenter la base Notion. L'application lit la base à chaque ouverture et à chaque **Actualiser**.
- Hors connexion, l'application affiche la dernière liste chargée. Les modifications (favori, candidature…) demandent le réseau.
- **Changer le mot de passe :** modifiez le secret `APP_PASSWORD` dans GitHub, puis relancez le robot **Serveur Radar Emploi**. Les appareils connectés devront se reconnecter.
- **En cas de problème :** le message d'erreur de l'application indique la cause. Si Notion est « introuvable », refaites l'étape 1. Si Claude est refusé, vérifiez la clé et le plafond de dépense dans la console Anthropic.
- **L'artifact claude.ai** fonctionne toujours, en parallèle de l'application, sur les mêmes données.

## Sécurité

- **Clés :** les clés Notion et Claude ne sont que sur Cloudflare (secrets chiffrés). Elles ne sont ni dans l'application, ni sur le téléphone, ni dans le dépôt.
- **Accès :** le serveur exige le mot de passe à chaque requête. Il le compare en temps constant et freine les essais répétés. Il n'accepte que l'application (GitHub Pages, Android, iPhone) comme origine, et refuse toute page Notion hors des deux bases du Radar.
- **Page :** aucun texte d'offre n'est inséré comme du HTML, et seuls les liens `http(s)` sont gardés. La politique de sécurité (CSP) n'autorise que le script de la page, identifié par son empreinte (`scripts/csp.py`), et les appels vers le serveur. Les lecteurs PDF / DOCX sont servis avec l'application, sans CDN. La page refuse de s'afficher dans le cadre d'un autre site.
- **Android :** l'inspection à distance du contenu de l'app est désactivée, et ses données (CV, mot de passe mémorisé) sont exclues des sauvegardes Google et des transferts vers un autre téléphone (`mobile/harden_android.py`). L'APK fourni par le robot est une version de test, signée avec une clé de développement.
- **Robots GitHub :** actions épinglées par empreinte (mises à jour par Dependabot). Les secrets ne sont fournis qu'aux étapes qui en ont besoin, et les robots n'ont aucun droit d'écriture sur le dépôt.

## Fichiers

| Fichier | Rôle |
|---|---|
| `radar-template.html` | L'application (portée de l'artifact claude.ai, avec écran de connexion) |
| `server/` | Le serveur personnel : relais Notion (`src/notion.js`), relais Claude (`src/claude.js`), tests (`npm test`) |
| `scripts/build.py`, `scripts/csp.py` | Génèrent le site publié (dossier `site/`) et sa politique de sécurité |
| `radar-app/` | Manifeste, mode hors connexion, icônes et lecteurs PDF / DOCX de l'application |
| `mobile/` | Projet Android / iPhone (Capacitor) : `prepare.py`, `harden_android.py`, icônes |
| `.github/workflows/serveur.yml` | Met le serveur en ligne sur Cloudflare |
| `.github/workflows/radar.yml` | Publie l'application sur GitHub Pages |
| `.github/workflows/mobile.yml` | Compile l'APK Android et vérifie le projet iOS |

---

# Expos du moment

L'application des expositions a déménagé dans son propre dépôt, [Expos-du-moment/Expositions](https://github.com/Expos-du-moment/Expositions), publiée à l'adresse https://expos-du-moment.github.io/Expositions/. Elle est ainsi totalement séparée du Radar emploi : autre adresse, autres données de navigateur.

L'ancienne adresse `…/radar-emploi-nature/expositions/` renvoie automatiquement vers la nouvelle (`scripts/expositions_redirect.py`).
