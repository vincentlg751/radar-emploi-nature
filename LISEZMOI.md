# Radar Emploi Nature — site public

Une page web en accès libre (sans compte claude.ai ni Notion) qui affiche les offres de la base Notion « Veille offres emploi écologie ». Elle calcule aussi un indice de compatibilité avec votre CV, directement dans votre navigateur.

Chaque matin vers 7h15 (heure de Paris), GitHub relit la base Notion et régénère la page. La veille Claude de 5h40 a alors déjà ajouté les nouvelles offres.

## Contenu

| Fichier | Rôle |
|---|---|
| `radar-template.html` | La page (recherche, filtres, CV, indice), sans les données |
| `scripts/build.py` | Lit la base Notion avec l'API officielle et produit `site/index.html` et `site/offres.json` (utilisé par les applications) |
| `.github/workflows/radar.yml` | Lance la génération chaque jour et publie sur GitHub Pages |

## Mise en place (environ 15 minutes, une seule fois)

### 1. Créer une clé Notion

1. Ouvrez https://www.notion.so/profile/integrations, puis cliquez sur **Nouvelle intégration**.
2. Remplissez les champs : nom « Radar Emploi Nature », espace « Espace de Vincent Le Gal », type **Interne**. Enregistrez.
3. Dans l'onglet **Configuration**, copiez le **Secret interne** (il commence par `ntn_` ou `secret_`). Gardez-le pour l'étape 3.
4. Ouvrez la base « Veille offres emploi écologie » dans Notion. Cliquez sur **•••** en haut à droite, puis **Connexions**, puis ajoutez **Radar Emploi Nature**.

### 2. Créer le dépôt GitHub

1. Créez un compte gratuit sur https://github.com si vous n'en avez pas.
2. Cliquez sur **+**, puis **New repository**. Nommez-le `radar-emploi-nature` et choisissez **Public** (requis pour GitHub Pages gratuit). Cliquez sur **Create repository**.
3. Cliquez sur **uploading an existing file**. Glissez `radar-template.html`, `LISEZMOI.md` et le dossier `scripts`, puis cliquez sur **Commit changes**.
4. Créez le fichier du robot. Le dossier `.github` est souvent masqué sur Mac et Windows, donc créez-le à la main :
   - cliquez sur **Add file**, puis **Create new file** ;
   - comme nom de fichier, tapez exactement `.github/workflows/radar.yml` ;
   - collez le contenu du fichier `radar.yml` fourni, puis cliquez sur **Commit changes**.

### 3. Donner la clé Notion à GitHub

Dans le dépôt, allez dans **Settings**, puis **Secrets and variables**, puis **Actions**, puis **New repository secret**.
- Name : `NOTION_TOKEN`
- Secret : collez le secret interne de l'étape 1.

### 4. Activer la publication

1. Allez dans **Settings**, puis **Pages**. Dans **Build and deployment**, choisissez la source **GitHub Actions**.
2. Allez dans l'onglet **Actions**, cliquez sur **Radar Emploi Nature**, puis sur **Run workflow**.
3. Après environ une minute, la page est en ligne à l'adresse `https://VOTRE-NOM-GITHUB.github.io/radar-emploi-nature/`.

Cette adresse ne change plus. Ouvrez-la sur ordinateur ou téléphone, sans compte.

## À savoir

- **Visibilité :** la page est publique. Toute personne qui a l'adresse voit les offres et leur statut (Candidaté, Écarté…).
- **Votre CV :** il reste dans votre navigateur. Il n'est jamais envoyé à GitHub ni à Notion.
- **Indice de compatibilité :** il est calculé localement à partir des mots-clés du CV et de l'offre, du niveau demandé, du domaine et du type de contrat.
- **Analyse rédigée (facultatif) :** pour obtenir les points à revoir, l'accroche et les reformulations, ajoutez votre propre clé API Anthropic dans le bloc « Mon CV ».
- **En cas d'échec du robot :** GitHub vous envoie un e-mail. La cause la plus fréquente est que l'intégration n'est plus connectée à la base (refaites l'étape 1.4).

---

# Expos du moment — application iPhone

Une seconde page, publiée au même endroit, à l'adresse `https://VOTRE-NOM-GITHUB.github.io/radar-emploi-nature/expositions/`. Elle regroupe les expositions en cours à Paris et en Île-de-France.

- **Onglets Gratuites / Payantes / Toutes**, recherche, filtres par **thématique**, « Nouveautés », « Finit bientôt » et favoris.
- **Carte** des lieux et **Près de moi** (tri par distance, avec votre position).
- Fiche détaillée avec dates, adresse, tarif, bouton **Itinéraire** (ouvre Plans) et lien vers le site ou la billetterie.
- Fonctionne hors connexion avec la dernière liste chargée.

## L'installer sur l'iPhone

1. Ouvrez l'adresse ci-dessus dans **Safari**.
2. Touchez **Partager**, puis **Sur l'écran d'accueil**.
3. L'icône « Expos » s'ouvre ensuite en plein écran, comme une application.

## Renouvellement automatique de la base

Chaque jour à 5h40 UTC, le robot `.github/workflows/expositions.yml` :

1. lit l'API ouverte **Que faire à Paris** de la Ville de Paris (sans clé) et la sélection manuelle `expositions/data/selection.json` ;
2. retire les expositions terminées ;
3. compare avec la veille. Les nouvelles reçoivent la date du jour (`vu_le`) et apparaissent avec l'étiquette **Nouveau** dans l'app pendant 7 jours ;
4. enregistre la base (`expositions/data/expositions.json`) et le journal (`expositions/data/journal.json`) dans le dépôt, puis relance la publication du site.

Le résumé de chaque passage (total, nouvelles, retirées) s'affiche dans l'onglet **Actions** de GitHub. L'app signale aussi les expositions apparues depuis votre dernière visite.

| Fichier | Rôle |
|---|---|
| `expositions/app/` | L'application (page, icônes, mode hors connexion, carte Leaflet) |
| `expositions/refresh.py` | Renouvelle la base et détecte les nouvelles expositions |
| `expositions/build.py` | Copie l'app et la base dans `site/expositions/` avant publication |
| `expositions/data/selection.json` | Expositions ajoutées à la main (grandes expos, lieux absents de l'API) |
| `expositions/MODELE.md` | Le modèle de données (gratuites puis payantes) |

**Ajouter une exposition à la main :** copiez une fiche dans `selection.json`, modifiez-la, puis cliquez sur **Commit changes**. Le robot se relance tout seul.

---

# Radar Emploi — application Android et iPhone

La page Radar Emploi Nature (recherche, filtres, CV, indice de compatibilité, analyse et prompts Claude) existe aussi en application. Deux façons de l'installer :

## 1. Application installable depuis le navigateur (immédiat, sans store)

Ouvrez `https://VOTRE-NOM-GITHUB.github.io/radar-emploi-nature/` sur le téléphone.

- **iPhone :** dans **Safari**, touchez **Partager**, puis **Sur l'écran d'accueil**.
- **Android :** dans **Chrome**, touchez **⋮**, puis **Installer l'application** (ou **Ajouter à l'écran d'accueil**).

L'icône « Radar Emploi » s'ouvre en plein écran. La liste des offres est relue à chaque ouverture, et la dernière liste reste consultable hors connexion. Le CV et la clé API restent sur le téléphone.

## 2. Application native (APK Android, projet Xcode pour iOS)

Le dossier `mobile/` contient un projet [Capacitor](https://capacitorjs.com) qui emballe la même page. Le robot `.github/workflows/mobile.yml` le compile à chaque modification (ou via **Actions → Application mobile → Run workflow**) :

- **Android :** téléchargez l'artefact **RadarEmploi-android** en bas de la page du passage, dézippez-le, puis ouvrez `RadarEmploi.apk` sur le téléphone. Autorisez l'installation depuis cette source quand Android le demande.
- **iOS :** Apple impose un Mac et un compte développeur pour installer une app native. Téléchargez **RadarEmploi-ios-xcode**, ou sur un Mac lancez `cd mobile && npm install && npm run ios && npx cap open ios`. Dans Xcode, choisissez votre équipe (**Signing & Capabilities**), branchez l'iPhone, puis cliquez sur **▶**. Pour la publier sur l'App Store ou TestFlight, utilisez **Product → Archive**.

L'application native intègre la liste d'offres du jour de sa compilation et relit `offres.json` sur GitHub Pages à chaque ouverture : elle reste à jour sans réinstallation.

| Fichier | Rôle |
|---|---|
| `radar-app/` | Manifeste, mode hors connexion et icônes de l'application installable (`make_icons.py` redessine les icônes) |
| `mobile/prepare.py` | Produit `mobile/www/` à partir de `radar-template.html` et de la liste d'offres |
| `mobile/capacitor.config.json` | Nom (« Radar Emploi ») et identifiant de l'application native |
| `mobile/assets/` | Icône et écran de démarrage des apps natives |
| `.github/workflows/mobile.yml` | Compile l'APK Android et vérifie le projet iOS |
