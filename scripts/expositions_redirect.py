"""L'app « Expos du moment » a déménagé dans son propre dépôt (organisation Expos-du-moment).

Publie à l'ancienne adresse …/radar-emploi-nature/expositions/ :
- une page qui renvoie vers la nouvelle adresse (les icônes déjà installées continuent de marcher) ;
- un service worker qui vide l'ancien cache hors connexion et se désinstalle.
"""
import pathlib

NEW_URL = "https://expos-du-moment.github.io/Expositions/"
SITE = pathlib.Path(__file__).resolve().parent.parent / "site"

PAGE = f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="0; url={NEW_URL}">
<link rel="canonical" href="{NEW_URL}">
<title>Expos du moment a déménagé</title>
<style>body{{font:16px/1.5 -apple-system,system-ui,sans-serif;margin:0;padding:40px 20px;background:#F4F1EA;color:#1B1916;text-align:center}}a{{color:#B4442B;font-weight:600}}</style>
</head><body>
<p>L'application <b>Expos du moment</b> a une nouvelle adresse :</p>
<p><a href="{NEW_URL}">{NEW_URL}</a></p>
<p>Ouvrez-la dans Safari puis <b>Partager › Sur l'écran d'accueil</b> pour la réinstaller.</p>
<script>
if ("serviceWorker" in navigator) navigator.serviceWorker.getRegistrations().then(rs => rs.forEach(r => r.scope.includes("/expositions/") && r.unregister()));
location.replace({NEW_URL!r});
</script>
</body></html>
"""

SW = """// Ancien service worker de l'app Expositions : vide son cache et se désinstalle.
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys()
    .then(ks => Promise.all(ks.filter(k => k.startsWith("expos-")).map(k => caches.delete(k))))
    .then(() => self.registration.unregister())
    .then(() => self.clients.matchAll())
    .then(cs => cs.forEach(c => c.navigate(c.url))));
});
"""

if __name__ == "__main__":
    out = SITE / "expositions"
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(PAGE, encoding="utf-8")
    (out / "sw.js").write_text(SW, encoding="utf-8")
    if not (SITE / "index.html").exists():  # page Radar non générée (secret Notion absent)
        (SITE / "index.html").write_text('<!doctype html><meta charset="utf-8"><title>Radar Emploi Nature</title>'
                                          '<p>Page en cours de génération.</p>\n', encoding="utf-8")
    (SITE / ".nojekyll").write_text("")
    print(f"Renvoi {out} -> {NEW_URL}")
