"""Prépare mobile/www/ : l'application Radar Emploi Nature pour Android et iPhone (Capacitor).

L'application relit à chaque ouverture la liste publiée sur GitHub Pages (offres.json). Si le site a
été généré juste avant (site/offres.json), une copie est embarquée pour le premier lancement hors connexion.

Variable facultative : RADAR_DATA_URL (par défaut https://vincentlg751.github.io/radar-emploi-nature/offres.json).
"""
import os, pathlib, shutil, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
WWW = HERE / "www"
sys.path.insert(0, str(ROOT / "scripts"))
import csp as csp_policy  # noqa: E402

DATA_URL = os.environ.get("RADAR_DATA_URL", "https://vincentlg751.github.io/radar-emploi-nature/offres.json")

if __name__ == "__main__":
    html = (ROOT / "radar-template.html").read_text(encoding="utf-8")
    # Le manifeste et le service worker servent à la version web ; l'app native n'en a pas besoin.
    html = html.replace('<link rel="manifest" href="manifest.webmanifest">\n', "")
    html = csp_policy.harden(csp_policy.with_data_url(html, DATA_URL))
    if WWW.exists():
        shutil.rmtree(WWW)
    (WWW / "icons").mkdir(parents=True)
    (WWW / "index.html").write_text(html, encoding="utf-8")
    for icon in ("icon-192.png", "apple-touch-icon.png"):
        shutil.copy2(ROOT / "radar-app" / "icons" / icon, WWW / "icons" / icon)
    shutil.copytree(ROOT / "radar-app" / "vendor", WWW / "vendor")
    bundled = ROOT / "site" / "offres.json"
    if bundled.exists():
        shutil.copy2(bundled, WWW / "offres.json")
    print(f"www prêt (liste : {DATA_URL}{', copie embarquée' if bundled.exists() else ''}) -> {WWW}")
