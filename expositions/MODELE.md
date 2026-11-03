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
