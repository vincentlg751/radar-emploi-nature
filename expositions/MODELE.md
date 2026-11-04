# Modèle de données — Expositions

Une fiche par exposition dans `data/expositions.json` (générée) et `data/selection.json` (saisie à la main).

## Champs communs

| Champ | Exemple | Rôle |
|---|---|---|
| `id` | `qfap-12345`, `sel-orsay-mary-cassatt` | Identifiant stable. Sert à repérer les nouvelles expositions. |
| `titre`, `resume` | | Texte affiché |
| `debut`, `fin` | `2026-10-06` | Dates (AAAA-MM-JJ). Une expo est retirée le lendemain de `fin`. |
| `horaires` | | Texte libre |
| `lieu`, `adresse` | `Musée d'Orsay` | Lieu et adresse postale |
| `lat`, `lon` | `48.86`, `2.3266` | Position sur la carte, distance « Près de moi » |
| `thematiques` | `["Beaux-arts"]` | Liste parmi : Photographie, Art contemporain, Beaux-arts, Histoire & patrimoine, Sciences & nature, Design, mode & arts déco, Architecture & ville, Street art & BD, Société & monde, Jeunesse, Autres |
| `image`, `lien` | URL | Visuel et page officielle |
| `a_verifier` | `true` | Affiche un avertissement : tarif ou dates non confirmés |
| `vu_le` | `2026-11-03` | Ajouté automatiquement : premier jour où l'expo est apparue dans la base |
| `source` | | D'où vient la fiche |

## Modèle 1 — exposition gratuite

```json
"tarif": { "type": "gratuit", "prix_min": 0, "detail": "Entrée libre" }
```

`type` peut aussi valoir `gratuit_sous_condition` (sur réservation, pour certains publics…). Ces expositions apparaissent dans l'onglet **Gratuites**.

## Modèle 2 — exposition payante

```json
"tarif": {
  "type": "payant",
  "prix_min": 16,
  "detail": "Plein tarif 22 €, réduit 16 €, gratuit -18 ans",
  "reservation": true,
  "billetterie": "https://…"
}
```

`prix_min` sert au tri « Prix croissant » et à l'étiquette « Dès 16 € ». `billetterie` affiche un bouton **Réserver**. Ces expositions apparaissent dans l'onglet **Payantes**.

`type: "inconnu"` (tarif non communiqué) n'apparaît que dans l'onglet **Toutes**.

## Affluence (tri « Les plus demandées »)

Ajouté automatiquement quand le lieu de l'expo est reconnu :

```json
"affluence": { "visiteurs": 8700000, "annee": 2024, "lieu": "Musée du Louvre", "niveau": 3, "score": 6.94, "source": "…" }
```

Il s'agit de la **fréquentation annuelle du lieu**, pas d'un comptage propre à l'expo : aucune source publique ne donne la fréquentation de chaque exposition en temps réel. Les chiffres viennent de `data/affluence.json` (saisis à la main, prioritaires, avec leur source) et du jeu ouvert « Fréquentation des Musées de France » (ministère de la Culture, data.gouv.fr), recopié dans `data/affluence-auto.json`. Niveaux : 3 = au moins 2 millions de visiteurs par an (« Très forte affluence »), 2 = au moins 800 000 (« Forte affluence »), 1 = au moins 200 000.
