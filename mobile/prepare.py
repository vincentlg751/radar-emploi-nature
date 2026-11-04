"""Prépare mobile/www/ : la page Radar Emploi Nature pour l'application Android / iOS.

- reprend radar-template.html tel quel (recherche, filtres, CV, indice, analyse par Claude) ;
- y intègre la dernière liste d'offres si site/offres.json existe (fonctionne alors dès la 1re ouverture, même hors connexion) ;
- indique à l'application où relire la liste à jour à chaque ouverture (GitHub Pages).

Variable facultative : RADAR_DATA_URL (par défaut https://vincentlg751.github.io/radar-emploi-nature/offres.json).
"""
import base64, gzip, json, os, pathlib, shutil, sys, urllib.parse, urllib.request

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
WWW = HERE / "www"
DATA_URL = os.environ.get("RADAR_DATA_URL", "https://vincentlg751.github.io/radar-emploi-nature/offres.json")


def offers_json():
    local = ROOT / "site" / "offres.json"
    if local.exists():
        return local.read_bytes(), str(local)
    try:  # sinon la liste publiée en ligne
        with urllib.request.urlopen(DATA_URL, timeout=30) as r:
            raw = r.read()
        json.loads(raw)
        return raw, DATA_URL
    except Exception as e:
        print(f"Liste des offres non intégrée ({e}). L'application la chargera à l'ouverture.", file=sys.stderr)
        return None, None


if __name__ == "__main__":
    html = (ROOT / "radar-template.html").read_text(encoding="utf-8")
    raw, src = offers_json()
    gz = base64.b64encode(gzip.compress(raw, 9)).decode() if raw else ""
    html = html.replace("__OFFRES_GZ_B64__", gz)
    # L'app native relit la liste en ligne : on autorise cette origine (et elle seule) dans la CSP.
    data_origin = "{0.scheme}://{0.netloc}".format(urllib.parse.urlsplit(DATA_URL))
    csp = "connect-src 'self' https://api.anthropic.com"
    if csp not in html:
        sys.exit("CSP introuvable dans radar-template.html (connect-src).")
    html = html.replace(csp, f"{csp} {data_origin}", 1)
    marker = '<script id="offres-gz"'
    html = html.replace(marker, f"<script>window.RADAR_DATA_URL = {json.dumps(DATA_URL)};</script>\n{marker}", 1)
    # Le manifeste et le service worker servent à la version web ; l'app native n'en a pas besoin.
    html = html.replace('<link rel="manifest" href="manifest.webmanifest">\n', "")
    if WWW.exists():
        shutil.rmtree(WWW)
    (WWW / "icons").mkdir(parents=True)
    (WWW / "index.html").write_text(html, encoding="utf-8")
    for icon in ("icon-192.png", "apple-touch-icon.png"):
        shutil.copy2(ROOT / "radar-app" / "icons" / icon, WWW / "icons" / icon)
    # Lecteurs PDF / DOCX embarqués dans l'application (aucun CDN tiers).
    shutil.copytree(ROOT / "radar-app" / "vendor", WWW / "vendor")
    print(f"www prêt ({src or 'sans offres intégrées'}) -> {WWW}")
