"""Génère le site publié par GitHub Pages (dossier site/) : l'application Radar Emploi Nature.

La page ne contient aucune donnée : les offres sont lues dans Notion à travers le serveur
personnel (dossier server/), après connexion par mot de passe.

Variable facultative : RADAR_SERVER (adresse du serveur, pré-remplie dans l'écran de connexion).
Lancé par .github/workflows/radar.yml.
"""
import os, pathlib, shutil, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import csp  # noqa: E402


def build(out_dir, server=""):
    html = (ROOT / "radar-template.html").read_text(encoding="utf-8")
    html = csp.harden(csp.with_server(html, server), server)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(html, encoding="utf-8")
    (out_dir / ".nojekyll").write_text("")
    app = ROOT / "radar-app"
    shutil.copy2(app / "manifest.webmanifest", out_dir / "manifest.webmanifest")
    shutil.copy2(app / "sw.js", out_dir / "sw.js")
    (out_dir / "icons").mkdir(exist_ok=True)
    for icon in ("icon-192.png", "icon-512.png", "icon-maskable-512.png", "apple-touch-icon.png"):
        shutil.copy2(app / "icons" / icon, out_dir / "icons" / icon)
    shutil.copytree(app / "vendor", out_dir / "vendor", dirs_exist_ok=True)
    print(f"Application -> {out_dir / 'index.html'} ({len(html.encode()) // 1024} Kio)")


if __name__ == "__main__":
    build(ROOT / "site", os.environ.get("RADAR_SERVER", ""))
