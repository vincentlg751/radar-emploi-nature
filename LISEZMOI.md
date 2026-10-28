# Radar Emploi Nature — site public

Une page web en accès libre (sans compte claude.ai ni Notion) qui affiche les offres de la base Notion « Veille offres emploi écologie ». Elle calcule aussi un indice de compatibilité avec votre CV, directement dans votre navigateur.

Chaque matin vers 7h15 (heure de Paris), GitHub relit la base Notion et régénère la page. La veille Claude de 5h40 a alors déjà ajouté les nouvelles offres.

## Contenu

| Fichier | Rôle |
|---|---|
| `radar-template.html` | La page (recherche, filtres, CV, indice), sans les données |
| `scripts/build.py` | Lit la base Notion avec l'API officielle et produit `site/index.html` |
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
