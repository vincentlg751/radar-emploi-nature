"""Copie l'application Expositions et sa base dans site/expositions/ (publiée par GitHub Pages)."""
import pathlib, shutil

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE.parent / "site" / "expositions"

if __name__ == "__main__":
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(HERE / "app", OUT)
    shutil.copy2(HERE / "data" / "expositions.json", OUT / "expositions.json")
    print(f"Application Expositions -> {OUT}")
