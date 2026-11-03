"""Copie l'application Expositions et sa base dans site/expositions/ (publiée par GitHub Pages)."""
import pathlib, shutil

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE.parent / "site" / "expositions"

if __name__ == "__main__":
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(HERE / "app", OUT)
    shutil.copy2(HERE / "data" / "expositions.json", OUT / "expositions.json")
    # Sans page Radar (secret Notion absent), la racine du site renvoie vers l'application.
    index = OUT.parent / "index.html"
    if not index.exists():
        index.write_text('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=expositions/">'
                         '<title>Expos du moment</title><a href="expositions/">Expos du moment</a>\n', encoding="utf-8")
        (OUT.parent / ".nojekyll").write_text("")
    print(f"Application Expositions -> {OUT}")
