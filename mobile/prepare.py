"""Prépare mobile/www/ : l'application Radar Emploi Nature pour Android et iPhone (Capacitor).

Reprend radar-template.html (la dernière version du Radar, avec ses onglets et ses prompts),
qui se connecte au serveur personnel (dossier server/) pour lire et modifier Notion et appeler Claude.

Variable facultative : RADAR_SERVER (adresse du serveur, pré-remplie dans l'écran de connexion).
"""
import os, pathlib, shutil, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
WWW = HERE / "www"
sys.path.insert(0, str(ROOT / "scripts"))
import csp as csp_policy  # noqa: E402

if __name__ == "__main__":
    server = os.environ.get("RADAR_SERVER", "")
    html = (ROOT / "radar-template.html").read_text(encoding="utf-8")
    # Le manifeste et le service worker servent à la version web ; l'app native n'en a pas besoin.
    html = html.replace('<link rel="manifest" href="manifest.webmanifest">\n', "")
    html = csp_policy.harden(csp_policy.with_server(html, server), server)
    if WWW.exists():
        shutil.rmtree(WWW)
    (WWW / "icons").mkdir(parents=True)
    (WWW / "index.html").write_text(html, encoding="utf-8")
    for icon in ("icon-192.png", "apple-touch-icon.png"):
        shutil.copy2(ROOT / "radar-app" / "icons" / icon, WWW / "icons" / icon)
    shutil.copytree(ROOT / "radar-app" / "vendor", WWW / "vendor")
    print(f"www prêt{' (serveur ' + csp_policy.server_origin(server) + ')' if csp_policy.server_origin(server) else ''} -> {WWW}")
