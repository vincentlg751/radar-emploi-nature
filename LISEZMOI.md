# Radar Emploi Nature — application Android, iPhone et web

Gratuit, sans serveur ni abonnement, sur le même principe que l'app « Expositions » : chaque matin, un robot GitHub lit la base Notion et publie la liste des offres ; l'application lit cette liste.

L'application reprend la dernière version du Radar (l'artifact claude.ai du 31 octobre 2026) : mêmes onglets, mêmes fonctions et mêmes prompts.

- **Offres, Favoris, Candidatés :** étoile, date de candidature, retrait d'une offre.
- **Indice de compatibilité** sur 6 critères (compétences, expérience, formation, équilibre de vie selon le lieu, secteur, outils), calculé sur l'appareil à partir de votre CV.
- **Claude, sans abonnement :** adaptation du CV, structure de lettre de motivation, conversation « Mes expériences », lecture d'une annonce collée, indice affiné. Le Radar prépare la demande (le prompt d'origine, votre CV et l'offre). Vous la collez dans Claude (l'app ou claude.ai, le compte gratuit suffit), puis vous recollez la réponse dans le Radar, qui l'affiche.
- **Sources de recherche** de l'agent du matin (consultation).
- Filtres par région, contrat, langue, niveau, domaine, date et indice. Fonctionne hors connexion avec la dernière liste.

## Installer l'application (5 minutes)

Le secret GitHub `NOTION_TOKEN` est déjà en place. Il reste à vérifier, dans Notion, que l'intégration « Radar Emploi Nature » est connectée aux deux bases :
1. Ouvrez la base **« Veille offres emploi écologie »**. Cliquez sur **•••**, puis **Connexions** : **Radar Emploi Nature** doit y figurer. Sinon, cliquez sur **Ajouter des connexions**, choisissez **Radar Emploi Nature**, puis **Confirmer**.
2. Faites de même pour la base **« Sources de recherche »**.

Ensuite, sur le téléphone :
- **iPhone :** dans **Safari**, ouvrez https://vincentlg751.github.io/radar-emploi-nature/. Touchez **Partager**, puis **Sur l'écran d'accueil**, puis **Ajouter**.
- **Android :** dans **Chrome**, ouvrez la même adresse. Touchez **⋮**, puis **Installer l'application**.
- **Android, application native (facultatif) :** dans l'onglet **Actions** du dépôt, ouvrez **Application mobile (Android et iOS)**, puis le dernier passage avec une coche verte. Téléchargez **RadarEmploi-android**, dézippez-le et ouvrez `RadarEmploi.apk`.

## Bon à savoir

- **Mise à jour :** le robot **Radar Emploi Nature** publie la liste chaque jour à 7h15 (heure de Paris en hiver), après la veille Claude de 5h40. Si GitHub demande une validation (**Review deployments**), allez dans **Settings**, puis **Environments**, puis **github-pages**, décochez **Required reviewers** et cliquez sur **Save protection rules** : la mise à jour se fera seule.
- **Vos actions restent sur l'appareil :** favoris, candidatures, offres retirées ou ajoutées, CV, fiches « Mes expériences ». Elles ne remontent pas dans Notion et ne passent pas d'un appareil à l'autre. Une offre en favori ou en candidature reste visible même après sa sortie de la veille.
- **Sources de recherche :** pour ajouter un site ou le mettre en pause, modifiez la base Notion (ou utilisez l'artifact claude.ai). La liste de l'application suit le lendemain matin.
- **L'artifact claude.ai** fonctionne toujours, en parallèle, avec Notion en direct.
- **Ce qui est publié :** la liste des offres est publique (comme le site). Le statut des offres, les dates de candidature et les offres « Écarté » ne sont jamais publiés.

## Sécurité

- **Aucune clé dans l'application :** la clé Notion ne sert qu'au robot GitHub (secret chiffré). Le CV ne quitte l'appareil que si vous collez vous-même une demande dans Claude.
- **Page :** aucun texte d'offre n'est inséré comme du HTML, et seuls les liens `http(s)` sont gardés, dans le robot comme dans l'application. La politique de sécurité (CSP) n'autorise que le script de la page, identifié par son empreinte (`scripts/csp.py`), et la liste publiée. Les lecteurs PDF / DOCX sont servis avec l'application, sans CDN. La page refuse de s'afficher dans le cadre d'un autre site.
- **Android :** inspection à distance désactivée ; données de l'app exclues des sauvegardes et des transferts (`mobile/harden_android.py`). L'APK est une version de test, signée avec une clé de développement.
- **Robots GitHub :** actions épinglées par empreinte (mises à jour par Dependabot), clé Notion fournie à une seule étape, aucun droit d'écriture sur le dépôt.

## Fichiers

| Fichier | Rôle |
|---|---|
| `radar-template.html` | L'application (portée de l'artifact claude.ai) |
| `scripts/build.py` | Lit Notion et produit le site publié : application et `offres.json` |
| `scripts/csp.py` | Politique de sécurité de la page |
| `radar-app/` | Manifeste, mode hors connexion, icônes et lecteurs PDF / DOCX |
| `mobile/` | Projet Android / iPhone (Capacitor) |
| `.github/workflows/radar.yml` | Robot du matin : lit Notion et publie sur GitHub Pages |
| `.github/workflows/mobile.yml` | Compile l'APK Android et vérifie le projet iOS |

---

# Expos du moment

L'application des expositions a déménagé dans son propre dépôt, [Expos-du-moment/Expositions](https://github.com/Expos-du-moment/Expositions), publiée à l'adresse https://expos-du-moment.github.io/Expositions/. Elle est ainsi totalement séparée du Radar emploi : autre adresse, autres données de navigateur.

L'ancienne adresse `…/radar-emploi-nature/expositions/` renvoie automatiquement vers la nouvelle (`scripts/expositions_redirect.py`).
